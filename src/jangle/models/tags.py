import operator
import re
import warnings
from datetime import datetime
from functools import cached_property, reduce
from typing import Any

from django.conf import settings
from django.db import models

from jangle.readers import IANASubtagRegistryReader
from jangle.regexp import (
    COMPLIANT,
    EXTENSION_P,
    LANGUAGE_TAG_RE,
    split_subtags,
)

from .languages import (
    ISOLanguage,
    ISOLanguageCodes,
    SimpleISOLanguageCollection,
)
from .regions import Region
from .scripts import Script
from .utils import choice_from_iana


class IANASubtagRegistryManager(models.Manager["IANASubtagRegistry"]):
    def register(self, clear=True, descriptions_batch_size=64) -> None:
        """Saves language, extlang, script, region, grandfathered, and redundant
        language tags and subtags from the IANA language subtag registry
        to their corresponding tables.
        """
        if clear:
            self.all().delete()
        registry = IANASubtagRegistryReader()
        registry_obj = self.create(
            file_date=registry.file_date,
            saved=datetime.utcnow(),
        )
        descriptions = []
        tag_strs = []
        for i, record in enumerate(registry.records):
            if i and not i % descriptions_batch_size:
                IANASubtagDescription.objects.bulk_create(descriptions)
                descriptions = []
            if "Subtag" in record and ".." in record.one("Subtag"):
                continue  # private use
            iana = IANASubtagRecord.objects.create(
                registry=registry_obj,
                deprecated=record.get_one("Deprecated"),
                added=record.one("Added"),
                comments=record.get_one("Comments"),
                pref_value=record.get_one("Preferred-Value"),
            )
            descriptions.extend(
                IANASubtagDescription(
                    subtag=iana,
                    text=text,
                    index=i,
                )
                for i, text in enumerate(record["Description"])
            )
            record_type = record.one("Type")
            if record_type in {"language", "extlang"}:
                if record_type == "language":
                    subtag = LanguageSubtag()
                else:
                    subtag = ExtlangSubtag()
                subtag.iana = iana
                subtag.code = record.one("Subtag")
                subtag.macrolanguage = record.get_one("Macrolanguage")
                if "Scope" in record:
                    subtag.scope = choice_from_iana(
                        LangSubtagFromIANARecord.Scope, record.one("Scope")
                    )
                if "Suppress-Script" in record:
                    subtag.suppress_script = Script.objects.get(
                        code=record.one("Suppress-Script")
                    )
                subtag.save()
                if record_type == "language":
                    LanguageTag.objects.create(lang=subtag)
            elif record_type == "script":
                ScriptSubtag.objects.create(
                    iana=iana, code=record.one("Subtag")
                )
            elif record_type == "region":
                RegionSubtag.objects.create(
                    iana=iana, code=record.one("Subtag")
                )
            elif record_type == "variant":
                VariantSubtag.objects.create(
                    iana=iana, text=record.one("Subtag")
                )
            elif record_type == "grandfathered":
                for tag_str, tag_iana in tag_strs:
                    LanguageTag.objects.from_str(
                        tag_str,
                        bool(tag_iana.deprecated),
                        defaults={"iana": tag_iana},
                    )
                tag_strs = []
                tag = LanguageTag.objects.create(
                    iana=iana,
                    grandfathered_tag=record.one("Tag"),
                )
                tag.save()
            elif record_type == "redundant":
                LanguageTag.objects.from_str(
                    record.one("Tag"),
                    allow_deprecated=bool(iana.deprecated),
                    defaults={
                        "iana": iana,
                    },
                )
            for prefix in record.get("Prefix", []):
                tag_strs.append(
                    (
                        "-".join([prefix, record.one("Subtag")]),
                        iana,
                    )
                )
        IANASubtagDescription.objects.bulk_create(
            descriptions,
            batch_size=descriptions_batch_size,
        )


class IANASubtagRegistry(models.Model):
    """Represents a saved instance
    of the IANA Language Subtag Registry.

    See https://www.iana.org/assignments/iso_lang-subtags-templates/iso_lang-subtags-templates.xhtml,
    https://www.iana.org/assignments/language-subtag-registry/language-subtag-registry.
    """

    file_date = models.DateField(unique=True)
    saved = models.DateTimeField()

    def __str__(self) -> str:
        return f"{self.file_date} / {self.saved}"

    objects = IANASubtagRegistryManager()

    class Meta:
        verbose_name = "IANA Language Subtag Registry"


class IANASubtagRecord(models.Model):
    """Abstract model to represent a record in
    the IANA language subtag registry.
    """

    descriptions: "models.manager.RelatedManager[IANASubtagDescription]"
    registry = models.ForeignKey(
        IANASubtagRegistry,
        on_delete=models.CASCADE,
    )
    deprecated = models.DateField(null=True)
    added = models.DateField()
    comments = models.TextField(null=True)
    pref_value = models.CharField("preferred value", null=True, max_length=42)
    """Preferred value."""

    def first_description(self) -> str:
        return self.descriptions.get(index=0).text

    def __str__(self) -> str:
        return self.first_description()

    class Meta:
        verbose_name = "IANA (sub)tag"


class IANASubtagDescription(models.Model):
    subtag = models.ForeignKey(
        IANASubtagRecord,
        related_name="descriptions",
        on_delete=models.CASCADE,
    )
    text = models.CharField(max_length=75)
    index = models.PositiveSmallIntegerField(default=0)

    def __str__(self) -> str:
        return self.text

    class Meta:
        unique_together = (("subtag", "index"), ("subtag", "text"))
        ordering = ["subtag", "index"]


class SubtagFromIANARecord(models.Model):
    iana = models.OneToOneField(
        IANASubtagRecord,
        on_delete=models.CASCADE,
    )

    class Meta:
        abstract = True


class LangSubtagFromIANARecord(SubtagFromIANARecord):
    class Scope(models.TextChoices):
        INDIVIDUAL = "I", "individual"
        COLLECTION = "C", "collection"
        MACROLANGUAGE = "M", "macrolanguage"
        SPECIAL = "S", "special"
        # PRIVATE_USE = 'P', 'private use'

    code = models.CharField(unique=True, max_length=3)
    macrolanguage = models.CharField(max_length=3, null=True)
    scope = models.CharField(
        choices=Scope.choices,
        default=Scope.INDIVIDUAL,
        max_length=1,
    )
    suppress_script = models.ForeignKey(
        Script,
        null=True,
        on_delete=models.SET_NULL,
    )

    def __str__(self) -> str:
        return self.code

    class Meta:
        abstract = True


class LanguageSubtag(LangSubtagFromIANARecord):
    iso_lang_codes = models.OneToOneField(
        ISOLanguageCodes,
        related_name="subtag",
        null=True,
        on_delete=models.CASCADE,
    )
    iso_lang = models.OneToOneField(
        ISOLanguage,
        related_name="subtag",
        null=True,
        on_delete=models.CASCADE,
    )
    iso_lang_collection = models.OneToOneField(
        SimpleISOLanguageCollection,
        related_name="subtag",
        null=True,
        on_delete=models.CASCADE,
    )

    def save(self, *args, **kwargs) -> None:
        if self.scope == self.Scope.COLLECTION:
            if self.iso_lang_collection and self.iso_lang_codes is None:
                try:
                    self.iso_lang_collection = (
                        SimpleISOLanguageCollection.objects.get_from_ietf(
                            self.code
                        )
                    )
                except SimpleISOLanguageCollection.DoesNotExist:
                    self.iso_lang_codes = (
                        ISOLanguageCodes.objects.get_from_ietf(self.code)
                    )
        else:
            if self.iso_lang is None:
                try:
                    self.iso_lang = ISOLanguage.objects.get_from_ietf(
                        self.code
                    )
                except ISOLanguage.DoesNotExist:
                    warnings.warn(
                        f"could not find any ISO-639 codes from '{self.code}'"
                    )
        super().save(*args, **kwargs)


class ExtlangSubtag(LangSubtagFromIANARecord):
    iso_lang = models.OneToOneField(
        ISOLanguage,
        related_name="ext_subtag",
        null=True,
        on_delete=models.CASCADE,
    )

    def save(self, *args, **kwargs) -> None:
        if not self.iso_lang:
            try:
                self.iso_lang = ISOLanguage.objects.get(part_3=self.code)
            except ISOLanguage.DoesNotExist:
                warnings.warn(
                    f"could not find any ISO-639 codes from '{self.code}'"
                )

        super().save(*args, **kwargs)


class ScriptSubtag(SubtagFromIANARecord):
    code = models.CharField(unique=True, max_length=4)
    ext_data = models.OneToOneField(
        Script,
        related_name="subtag",
        null=True,
        on_delete=models.SET_NULL,
    )

    def save(self, *args, **kwargs) -> None:
        if self.ext_data is None:
            try:
                self.ext_data = Script.objects.get(code=self.code)
            except Script.DoesNotExist:
                warnings.warn(f"could not find script of code '{self.code}'")
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.code


class RegionSubtag(SubtagFromIANARecord):
    code = models.CharField(unique=True, max_length=3)
    ext_data = models.OneToOneField(
        Region,
        null=True,
        related_name="subtag",
        on_delete=models.SET_NULL,
    )

    def save(self, *args, **kwargs) -> None:
        if self.ext_data is None:
            try:
                if len(self.code) == 2:
                    self.ext_data = Region.objects.get(iso__alpha_2=self.code)
                else:
                    self.ext_data = Region.objects.get(no=int(self.code))
            except Region.DoesNotExist:
                warnings.warn(f"could not find region of code '{self.code}'")
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.code


class VariantSubtag(SubtagFromIANARecord):
    text = models.CharField(unique=True, max_length=8)

    def __str__(self) -> str:
        return self.text


class LanguageTagQuerySet(models.QuerySet["LanguageTag"]):
    def private(self) -> "LanguageTagQuerySet":
        return self.exclude(lang__isnull=True, private__isnull=False)


class LanguageTagManager(models.Manager["LanguageTag"]):
    def get_queryset(self) -> LanguageTagQuerySet:
        return LanguageTagQuerySet(self.model, using=self._db)

    def private(self) -> LanguageTagQuerySet:
        return self.get_queryset().private()

    def from_str(
        self,
        tag_str: str,
        allow_deprecated=False,
        allow_create=True,
        defaults: dict[str, Any] = dict(),
    ) -> "LanguageTag":
        iana_kwargs = dict()
        if not allow_deprecated:
            iana_kwargs["iana__deprecated"] = None
        try:
            return self.get(grandfathered_tag__iexact=tag_str, **iana_kwargs)
        except self.model.DoesNotExist as e:
            pass

        match = LANGUAGE_TAG_RE[COMPLIANT].fullmatch(tag_str)
        if not match:
            raise ValueError(f"'{tag_str}' is not a valid language tag")
        groups = match.groupdict(None)
        if groups["private_tag"]:
            private_tag = groups["private_tag"].removeprefix("x-")
            try:
                return self.get(lang__isnull=True, private_iexact=private_tag)
            except self.model.DoesNotExist as e:
                if not allow_create:
                    raise e
                return self.create(private_tag=private_tag, **defaults)

        lang = LanguageSubtag.objects.get(
            code__iexact=groups["iso_639"], **iana_kwargs
        )
        extlang = None
        if groups["extlang"]:
            extlang = ExtlangSubtag.objects.get(
                code__iexact=groups["extlang_iso_639"], **iana_kwargs
            )
        region = None
        if groups["region"]:
            region = RegionSubtag.objects.get(
                code__iexact=groups["region"], **iana_kwargs
            )
        script = None
        if groups["script"]:
            script = ScriptSubtag.objects.get(
                code__iexact=groups["script"], **iana_kwargs
            )
        private_subtag = None
        if groups["private_subtag"]:
            private_subtag = groups["private_subtag"].removeprefix("x-")
        queryset = self.filter(
            lang=lang,
            extlang=extlang,
            region=region,
            script=script,
            private__iexact=private_subtag,
        )
        variants = []
        if groups["variants"]:
            for variant in split_subtags(groups["variants"]):
                variants.append(
                    VariantSubtag.objects.get(text__iexact=variant)
                )
            variants_qs = (models.Q(variants=variant) for variant in variants)
            queryset = queryset.filter(reduce(operator.and_, variants_qs))
        extensions = []
        if groups["extensions"]:
            for extension in split_subtags(groups["extensions"]):
                ext_match: re.Match = re.fullmatch(
                    EXTENSION_P, extension
                )  # type: ignore
                extensions.append(
                    {
                        "singleton": ext_match.group("singleton"),
                        "texts": split_subtags(ext_match.group("ext_text")),
                    }
                )
            extensions_qs = (
                models.Q(
                    extensions=ExtensionSubtag(
                        reduce(
                            operator.and_,
                            (
                                models.Q(index=i, text__iexact=text)
                                for i, text in enumerate(val["texts"])
                            ),
                        ),
                        index=i,
                        singleton__iexact=val["singleton"],
                    )
                )
                for i, val in enumerate(extensions)
            )
            queryset = queryset.filter(reduce(operator.and_, extensions_qs))
        queryset = queryset.exclude(variants_through__index=len(variants))
        queryset = queryset.exclude(extensions__index=len(extensions))
        try:
            return queryset.get()
        except self.model.DoesNotExist as e:
            if not allow_create:
                raise e
            tag = self.create(
                lang=lang,
                extlang=extlang,
                region=region,
                script=script,
                private=private_subtag,
                **defaults,
            )
            for i, variant in enumerate(variants):
                LanguageTagVariantSubtag.objects.create(
                    tag=tag,
                    variant=variant,
                    index=i,
                )
            for i, extension in enumerate(extensions):
                ext_obj = ExtensionSubtag.objects.create(
                    tag=tag,
                    singleton=extension["singleton"],
                    index=i,
                )
                for i, text in enumerate(extension["text"]):
                    ExtensionSubtagText.objects.create(
                        extension=ext_obj,
                        text=text,
                        index=i,
                    )
            return tag

    def native(self) -> "LanguageTag":
        native_lang = self.from_str(settings.LANGUAGE_CODE)
        return native_lang


class LanguageTag(models.Model):
    """Represents an RFC5646 language tag.

    See https://www.rfc-editor.org/rfc/rfc5646.html.
    """

    variants_through: "models.manager.RelatedManager[LanguageTagVariantSubtag]"
    extensions: "models.manager.RelatedManager[ExtensionSubtag]"
    iana = models.ForeignKey(
        IANASubtagRecord,
        null=True,
        on_delete=models.CASCADE,
    )
    grandfathered_tag = models.CharField(null=True, max_length=42)
    lang = models.ForeignKey(
        LanguageSubtag,
        null=True,
        on_delete=models.PROTECT,
    )
    extlang = models.ForeignKey(
        ExtlangSubtag,
        null=True,
        on_delete=models.PROTECT,
    )
    script = models.ForeignKey(
        ScriptSubtag,
        null=True,
        on_delete=models.PROTECT,
    )
    region = models.ForeignKey(
        RegionSubtag,
        null=True,
        on_delete=models.PROTECT,
    )
    variants = models.ManyToManyField(
        VariantSubtag,
        through="LanguageTagVariantSubtag",
        through_fields=("tag", "variant"),
    )
    private = models.CharField(
        null=True,
        max_length=42,
    )

    @property
    def is_private(self) -> bool:
        return self.lang is None and self.private is not None

    @cached_property
    def pref_tag(self) -> "LanguageTag":
        if not (self.iana and self.iana.pref_value):
            return self
        return self.__class__.objects.from_str(self.iana.pref_value)

    @cached_property
    def tag_str(self) -> str:
        if self.grandfathered_tag:
            return self.grandfathered_tag
        else:
            subtags: list[Any] = list(
                filter(
                    None,
                    [
                        self.lang,
                        self.extlang,
                        self.script,
                        self.region,
                        *self.variants.order_by("tags_through__index"),
                        *self.extensions.order_by("index"),
                    ],
                )
            )
        if self.private:
            subtags.extend(["x", self.private])

        return "-".join(map(str, subtags))

    @cached_property
    def description(self) -> str:
        """English description of what the tag represents."""
        if self.iana:
            return self.iana.first_description()
        parts = [self.lang.iana.first_description()]  # type: ignore
        if self.extlang:
            parts.append("-")
            parts.append(self.extlang.iana.first_description())
        if self.region:
            parts.append("as used in")
            parts.append(self.region.iana.first_description())
        if self.script:
            parts.append("as written in")
            parts.append(self.script.iana.first_description())

        for variant in self.variants_through.order_by("index"):
            parts.append("-")
            parts.append(variant.variant.iana.first_description())
        parts.extend(map(str, self.extensions.order_by("index")))
        return " ".join(parts)

    def __str__(self) -> str:
        return self.tag_str

    objects = LanguageTagManager()

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(lang__isnull=False)
                | models.Q(grandfathered_tag__isnull=False)
                | models.Q(private__isnull=False),
                name="langtag_or_grandfathered_or_private",
            )
        ]


class LanguageTagVariantSubtag(models.Model):
    tag = models.ForeignKey(
        LanguageTag,
        related_name="variants_through",
        on_delete=models.CASCADE,
    )
    variant = models.ForeignKey(
        VariantSubtag,
        related_name="tags_through",
        on_delete=models.CASCADE,
    )
    index = models.PositiveSmallIntegerField(default=0)

    class Meta:
        unique_together = (("tag", "index"), ("tag", "variant"))
        ordering = ["tag", "index"]


class ExtensionSubtag(models.Model):
    tag = models.ForeignKey(
        LanguageTag,
        related_name="extensions",
        on_delete=models.CASCADE,
    )
    singleton = models.CharField(max_length=1)
    index = models.PositiveSmallIntegerField(default=0)

    def __str__(self) -> str:
        texts = self.texts.order_by("index")  # type: ignore
        return "-".join([self.singleton, *map(str, texts)])

    class Meta:
        unique_together = (("tag", "index"), ("tag", "singleton"))
        ordering = ["tag", "index"]


class ExtensionSubtagText(models.Model):
    extension = models.ForeignKey(
        ExtensionSubtag,
        related_name="texts",
        on_delete=models.CASCADE,
    )
    text = models.CharField(max_length=8)
    index = models.PositiveSmallIntegerField(default=0)

    def __str__(self) -> str:
        return self.text

    class Meta:
        unique_together = ("extension", "index")
        ordering = ["extension", "index"]
