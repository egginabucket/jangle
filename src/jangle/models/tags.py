from __future__ import annotations

import operator
import re
import warnings
from datetime import datetime
from functools import cached_property, reduce
from typing import Any, Tuple

from django.conf import settings
from django.db import models
from django.utils.timezone import utc

import jangle.lite
from jangle.readers import IANASubtagRegistryReader
from jangle.utils import choice_from_iana

from .languages import (
    ISOLanguage,
    ISOLanguageCodes,
    SimpleISOLanguageCollection,
)
from .regions import Region
from .scripts import Script


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
            saved=datetime.utcnow().replace(tzinfo=utc),
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
                    iana=iana,
                    script=Script.objects.get(code=record.one("Subtag")),
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
                    LanguageTag.objects.create_from_langtag(
                        jangle.lite.LangTag.from_str(tag_str),
                        bool(tag_iana.deprecated),
                        iana=tag_iana,
                    )
                tag_strs = []
                tag = LanguageTag.objects.create(
                    iana=iana,
                    grandfathered_tag=record.one("Tag"),
                )
                tag.save()
            elif record_type == "redundant":
                tag, created = LanguageTag.objects.get_or_create_from_str(
                    record.one("Tag"),
                    allow_deprecated=bool(iana.deprecated),
                    defaults={
                        "iana": iana,
                    },
                )
                if not created:
                    tag.iana = iana
                    tag.save()
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

    records: "models.manager.RelatedManager[IANASubtagRecord]"
    """"""

    file_date = models.DateField(unique=True)
    """"""
    saved = models.DateTimeField()
    """Time registry was saved."""

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
    """"""
    registry = models.ForeignKey(
        IANASubtagRegistry,
        related_name="records",
        on_delete=models.CASCADE,
    )
    """"""
    deprecated = models.DateField(null=True)
    """Date deprecated."""
    added = models.DateField()
    """Date added."""
    comments = models.TextField(null=True)
    """"""
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
    """IANA subtag record."""
    text = models.CharField(max_length=254)
    """"""
    index = models.PositiveSmallIntegerField(default=0)
    """"""

    def __str__(self) -> str:
        return self.text

    class Meta:
        unique_together = ("subtag", "index")
        ordering = ["subtag", "index"]


class SubtagFromIANARecord(models.Model):
    iana = models.OneToOneField(
        IANASubtagRecord,
        related_name="+",
        on_delete=models.CASCADE,
    )
    """IANA (sub)tag record."""

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
    """ISO 639 or registered code."""
    macrolanguage = models.CharField(max_length=3, null=True)
    """"""
    scope = models.CharField(
        choices=Scope.choices,
        default=Scope.INDIVIDUAL,
        max_length=1,
    )
    """Classification."""
    suppress_script = models.ForeignKey(
        Script,
        null=True,
        on_delete=models.SET_NULL,
    )
    """Script used to write
    the overwhelming majority of
    documents in this language.
    """

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
    """"""
    iso_lang = models.OneToOneField(
        ISOLanguage,
        related_name="subtag",
        null=True,
        on_delete=models.CASCADE,
    )
    """"""
    iso_lang_collection = models.OneToOneField(
        SimpleISOLanguageCollection,
        related_name="subtag",
        null=True,
        on_delete=models.CASCADE,
    )
    """"""

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
    """"""

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
    """"""

    script = models.OneToOneField(
        Script,
        related_name="subtag",
        on_delete=models.CASCADE,
    )
    """External ISO-15924 data from unicode.org."""

    def __str__(self) -> str:
        return self.script.code


class RegionSubtag(SubtagFromIANARecord):
    """"""

    code = models.CharField(unique=True, max_length=3)
    """"""
    region = models.OneToOneField(
        Region,
        null=True,
        related_name="subtag",
        on_delete=models.SET_NULL,
    )
    """External UN M.49 and ISO 3166 data."""

    def save(self, *args, **kwargs) -> None:
        if self.region is None:
            try:
                if len(self.code) == 2:
                    self.region = Region.objects.get(iso__alpha_2=self.code)
                else:
                    self.region = Region.objects.get(no=int(self.code))
            except Region.DoesNotExist:
                warnings.warn(f"could not find region of code '{self.code}'")
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.code


class VariantSubtag(SubtagFromIANARecord):
    """"""

    text = models.CharField(unique=True, max_length=8)
    """"""

    def __str__(self) -> str:
        return self.text


class LanguageTagQuerySet(models.QuerySet["LanguageTag"]):
    def active(self) -> LanguageTagQuerySet:
        """Excludes all deprecated tags and tags with
        deprecated subtags, according to the IANA subtag registry.
        """
        return self.exclude(
            iana__deprecated__isnull=False,
            **{
                f"{subtag}__iana__deprecated__isnull": False
                for subtag in ["extlang", "script", "region", "variants"]
            },
        )

    def private(self) -> LanguageTagQuerySet:
        """Private tags (not langtags with a private subtag)."""
        return self.filter(lang__isnull=True, private__isnull=False)

    def get_from_lite(self, lite: jangle.lite.LanguageTag) -> LanguageTag:
        if lite.private:
            return self.get(lang__isnull=True, private=lite.private)
        if lite.grandfathered:
            return self.get(grandfathered_tag=lite.grandfathered)
        queryset = self
        if lite.langtag is None:
            raise ValueError("empty language tag")
        if lite.langtag.variants:
            tag_variants_qs = (
                models.Q(variants__text=variant)
                for variant in lite.langtag.variants
            )
            queryset = queryset.filter(reduce(operator.and_, tag_variants_qs))
        queryset = queryset.exclude(
            variants_through__index=len(lite.langtag.variants)
        )
        if lite.langtag.extensions:
            extension_qs = (
                models.Q(
                    texts=reduce(
                        operator.and_,
                        (
                            models.Q(index=i, text__iexact=text)
                            for i, text in enumerate(val.texts)
                        ),
                    ),
                    index=i,
                    singleton__iexact=val.singleton,
                )
                for i, val in enumerate(lite.langtag.extensions)
            )
            queryset = queryset.filter(
                extensions=reduce(operator.and_, extension_qs)
            )
        queryset = queryset.exclude(
            extensions__index=len(lite.langtag.extensions)
        )
        return queryset.get(
            lang__code=lite.langtag.lang,
            extlang__code=lite.langtag.extlang,
            script__script__code=lite.langtag.script,
            region__code=lite.langtag.region,
            private=lite.langtag.private,
        )

    def get_from_match(self, match: re.Match[str]) -> LanguageTag:
        return self.get_from_lite(jangle.lite.LanguageTag.from_match(match))

    def get_from_str(self, string: str) -> LanguageTag:
        return self.get_from_lite(jangle.lite.LanguageTag.from_str(string))


class LanguageTagManager(models.Manager["LanguageTag"]):
    """"""

    def get_queryset(self) -> LanguageTagQuerySet:
        return LanguageTagQuerySet(self.model, using=self._db)

    def private(self) -> LanguageTagQuerySet:
        return self.get_queryset().private()

    def active(self) -> LanguageTagQuerySet:
        return self.get_queryset().active()

    def get_from_lite(self, lite: jangle.lite.LanguageTag) -> LanguageTag:
        return self.get_queryset().get_from_lite(lite)

    def get_from_match(self, match: re.Match[str]) -> LanguageTag:
        return self.get_queryset().get_from_match(match)

    def get_from_str(self, string: str) -> LanguageTag:
        return self.get_queryset().get_from_str(string)

    def create_from_langtag(
        self, langtag: jangle.lite.LangTag, allow_deprecated=False, **kwargs
    ) -> LanguageTag:
        subtag_kwargs = {}
        if not allow_deprecated:
            subtag_kwargs["iana__deprecated__isnull"] = True
        tag = self.model(**kwargs)
        tag.lang = LanguageSubtag.objects.get(
            code=langtag.lang,
            **subtag_kwargs,
        )
        if langtag.extlang:
            tag.extlang = ExtlangSubtag.objects.get(
                code=langtag.extlang,
                **subtag_kwargs,
            )
        if langtag.script:
            tag.script = ScriptSubtag.objects.get(
                script__code=langtag.script,
                **subtag_kwargs,
            )
        if langtag.region:
            tag.region = RegionSubtag.objects.get(
                code=langtag.region,
                **subtag_kwargs,
            )
        tag.save()
        for i, variant in enumerate(langtag.variants):
            LanguageTagVariantSubtag.objects.create(
                tag=tag,
                variant=VariantSubtag.objects.get(text=variant),
                index=i,
            )
        for i, extension in enumerate(langtag.extensions):
            ext_obj = ExtensionSubtag.objects.create(
                tag=tag,
                singleton=extension.singleton,
                index=i,
            )
            for i, text in extension.texts:
                ExtensionSubtagText.objects.create(
                    extension=ext_obj,
                    text=text,
                    index=i,
                )
        return tag

    def get_or_create_from_lite(
        self,
        lite: jangle.lite.LanguageTag,
        allow_deprecated=False,
        defaults: dict[str, Any] = {},
    ) -> Tuple[LanguageTag, bool]:
        queryset = self.get_queryset()
        if not allow_deprecated:
            queryset = queryset.active()
        try:
            return queryset.get_from_lite(lite), False
        except self.model.DoesNotExist:
            if lite.langtag:
                return (
                    self.create_from_langtag(
                        lite.langtag, allow_deprecated, **defaults
                    ),
                    True,
                )
            elif lite.private:
                return self.create(private=lite.private), True
            else:
                raise ValueError(f"cannot create grandfathered tag '{lite}'")

    def get_or_create_from_str(
        self,
        string: str,
        allow_deprecated=False,
        defaults: dict[str, Any] = {},
    ) -> Tuple[LanguageTag, bool]:
        lite = jangle.lite.LanguageTag.from_str(string)
        return self.get_or_create_from_lite(lite, allow_deprecated, defaults)

    def native(self) -> LanguageTag:
        """Returns a LanguageTag from `settings.LANGUAGE_CODE`"""
        return self.get_or_create_from_str(settings.LANGUAGE_CODE)[0]


class LanguageTag(models.Model):
    """Represents an RFC5646 language tag.

    See https://www.rfc-editor.org/rfc/rfc5646.html.
    """

    variants_through: "models.manager.RelatedManager[LanguageTagVariantSubtag]"
    """"""
    extensions: "models.manager.RelatedManager[ExtensionSubtag]"
    """"""
    iana = models.ForeignKey(
        IANASubtagRecord,
        null=True,
        on_delete=models.CASCADE,
    )
    """Original IANA (sub)tag record."""
    grandfathered_tag = models.CharField(null=True, max_length=42)
    """"""
    lang = models.ForeignKey(
        LanguageSubtag,
        null=True,
        on_delete=models.PROTECT,
    )
    """Language subtag."""
    extlang = models.ForeignKey(
        ExtlangSubtag,
        null=True,
        on_delete=models.PROTECT,
    )
    """Extlang subtag."""
    script = models.ForeignKey(
        ScriptSubtag,
        null=True,
        on_delete=models.PROTECT,
    )
    """Script subtag."""
    region = models.ForeignKey(
        RegionSubtag,
        null=True,
        on_delete=models.PROTECT,
    )
    """Region subtag."""
    variants = models.ManyToManyField(
        VariantSubtag,
        through="LanguageTagVariantSubtag",
        through_fields=("tag", "variant"),
    )
    private = models.CharField(
        null=True,
        max_length=42,
    )
    """Private tag or subtag."""

    @property
    def is_private(self) -> bool:
        return self.lang is None and self.private is not None

    @cached_property
    def pref_tag(self) -> LanguageTag:
        """Preferred tag as defined in the IANA registry, or `self`."""
        if self.iana and self.iana.pref_value:
            return self.__class__.objects.get_from_str(self.iana.pref_value)
        elif (
            self.lang
            and self.lang.suppress_script
            and self.script
            and self.script.script == self.lang.suppress_script
        ):
            lite = self.lite()
            if not lite.langtag:
                raise ValueError(f"{lite} should have langtag")
            lite.langtag.script = None
            return LanguageTag.objects.get_or_create_from_lite(lite)[0]
        else:
            return self

    @cached_property
    def text(self) -> str:
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
        if self.lang is None:
            if self.private is not None:
                return f'Private tag x-"{self.private}"'
            else:
                raise ValueError(
                    f"IANA record for grandfathered tag '{self}' not found"
                )
        parts = [self.lang.iana.first_description()]
        if self.extlang:
            parts.append("-")
            parts.append(self.extlang.iana.first_description())
        if self.region:
            parts.append("as used in")
            parts.append(self.region.iana.first_description())
        if self.script and self.script.script != self.lang.suppress_script:
            parts.append("as written in")
            parts.append(self.script.iana.first_description())
        for variant in self.variants_through.order_by("index"):
            parts.append("-")
            parts.append(variant.variant.iana.first_description())
        parts.extend(map(str, self.extensions.order_by("index")))
        return " ".join(parts)

    def lite(self) -> jangle.lite.LanguageTag:
        lite = jangle.lite.LanguageTag(
            grandfathered=self.grandfathered_tag,
            langtag=None,
            private=None,
        )
        if self.is_private:
            lite.private = self.private
        elif self.lang:
            langtag = jangle.lite.LangTag(self.lang.code, private=self.private)
            if self.extlang:
                langtag.extlang = self.extlang.code
            if self.script:
                langtag.script = self.script.script.code
            if self.region:
                langtag.region = self.region.code
            langtag.variants = [
                variant_through.variant.text
                for variant_through in self.variants_through.order_by("index")
            ]
            langtag.extensions = [
                jangle.lite.Extension(
                    singleton=extension.singleton,
                    texts=[
                        text.text for text in extension.texts.order_by("index")
                    ],
                )
                for extension in self.extensions.order_by("index")
            ]
            lite.langtag = langtag
        return lite

    def __str__(self) -> str:
        return self.text

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
    """"""

    tag = models.ForeignKey(
        LanguageTag,
        related_name="variants_through",
        on_delete=models.CASCADE,
    )
    """"""
    variant = models.ForeignKey(
        VariantSubtag,
        related_name="tags_through",
        on_delete=models.CASCADE,
    )
    """"""
    index = models.PositiveSmallIntegerField(default=0)
    """"""

    class Meta:
        unique_together = (("tag", "index"), ("tag", "variant"))
        ordering = ["tag", "index"]


class ExtensionSubtag(models.Model):
    """"""

    texts: "models.manager.RelatedManager[ExtensionSubtagText]"
    """"""
    tag = models.ForeignKey(
        LanguageTag,
        related_name="extensions",
        on_delete=models.CASCADE,
    )
    """"""
    singleton = models.CharField(max_length=1)
    """"""
    index = models.PositiveSmallIntegerField(default=0)
    """"""

    def __str__(self) -> str:
        texts = self.texts.order_by("index")
        return "-".join([self.singleton, *map(str, texts)])

    class Meta:
        unique_together = (("tag", "index"), ("tag", "singleton"))
        ordering = ["tag", "index"]


class ExtensionSubtagText(models.Model):
    """"""

    extension = models.ForeignKey(
        ExtensionSubtag,
        related_name="texts",
        on_delete=models.CASCADE,
    )
    """"""
    text = models.CharField(max_length=8)
    """"""
    index = models.PositiveSmallIntegerField(default=0)
    """"""

    def __str__(self) -> str:
        return self.text

    class Meta:
        unique_together = ("extension", "index")
        ordering = ["extension", "index"]
