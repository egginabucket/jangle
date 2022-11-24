from __future__ import annotations

import csv
import warnings
from typing import Optional
from zipfile import ZipFile

import requests
from django.db import models
from requests.compat import urljoin

from jangle.readers import SilTableReader
from jangle.utils import BatchedCreateManager


class InvalidISO639Error(ValueError):
    pass


class ISOLanguageCodesManager(BatchedCreateManager["ISOLanguageCodes"]):
    def get_from_ietf(self, code: str) -> ISOLanguageCodes:
        if len(code) == 2:
            return self.get(part_1=code)
        elif len(code) == 3:
            for field in ["part_2b", "part_2t"]:
                try:
                    return self.get(**{field: code})
                except self.model.DoesNotExist:
                    continue
        else:
            raise InvalidISO639Error(code)
        raise self.model.DoesNotExist(code)

    def register(self, clear=True, batch_size=64) -> None:
        """Saves ISO 639-2 and 639-1 codes from the Library of Congress.
        See https://www.loc.gov/standards/iso639-2/ISO-639-2_utf-8.txt.
        """
        response = requests.get(
            "https://www.loc.gov/standards/iso639-2/ISO-639-2_utf-8.txt"
        )
        response.raise_for_status()
        response.encoding = "utf-8"
        if clear:
            self.all().delete()
        fieldnames = [
            "part_2b",
            "part_2t",
            "part_1",
            "names_en",
            "names_fr",
        ]
        self.batched_create(
            (
                self.model(
                    part_2b=row["part_2b"][-3:],
                    part_2t=row["part_2t"] or row["part_2b"][-3:],
                    part_1=row["part_1"] or None,
                    names_en=row["names_en"],
                    names_fr=row["names_fr"],
                )
                for row in csv.DictReader(
                    response.iter_lines(decode_unicode=True),
                    fieldnames,
                    delimiter="|",
                )
            ),
            batch_size,
        )


class ISOLanguageCodes(models.Model):
    """ISO 639-2 and 639-1 language codeset,
    saved from the Library of Congress.
    """

    language: Optional[ISOLanguage]
    """"""
    part_2b = models.CharField(
        "bibliographic code (ISO 639-2/B)",
        unique=True,
        max_length=3,
    )
    """Bibliographic code (ISO 639-2/B)."""
    part_2t = models.CharField(
        "terminological code (ISO 639-2/T)",
        unique=True,
        max_length=3,
    )
    """Terminological code (ISO 639-2/T)."""
    part_1 = models.CharField(
        "alpha-2 code (ISO 639-1)",
        null=True,
        max_length=2,
    )
    """Alpha-2 code (ISO 639-1)."""
    names_en = models.CharField(
        "noms français",
        unique=True,
        max_length=254,
    )
    """English names.
    Separated with ";" if multiple exist.
    """
    names_fr = models.CharField(
        "English names",
        unique=True,
        max_length=254,
    )
    """French names.
    Separated with ";" if multiple exist.
    """

    @property
    def ietf(self) -> str:
        """Code used in IETF language tags."""
        return self.part_1 or self.part_2b

    def __str__(self) -> str:
        return self.ietf

    objects = ISOLanguageCodesManager()

    class Meta:
        verbose_name = "ISO 639-2 and 639-1 language codeset"


class SimpleISOLanguageCollectionManager(
    BatchedCreateManager["SimpleISOLanguageCollection"]
):
    def get_from_ietf(self, code: str) -> SimpleISOLanguageCollection:
        return self.get(part_5=code)

    def register(self, clear=True, batch_size=64) -> None:
        """Saves basic ISO 639-5 data from the Library of Congress.
        See http://id.loc.gov/vocabulary/iso639-5.tsv.
        """
        response = requests.get("http://id.loc.gov/vocabulary/iso639-5.tsv")
        response.raise_for_status()

        if clear:
            self.all().delete()
        self.batched_create(
            (
                self.model(
                    part_5=row["code"],
                    names_en=row["Label (English)"],
                    names_fr=row["Label (French)"],
                )
                for row in csv.DictReader(
                    response.iter_lines(decode_unicode=True),
                    dialect="excel-tab",
                )
            ),
            batch_size,
        )


class SimpleISOLanguageCollection(models.Model):
    """Basic data for an ISO 639-5 language collection."""

    part_5 = models.CharField(
        "ISO 639-5 alpha-3 code", unique=True, max_length=3
    )
    """ISO 639-5 alpha-3 code."""
    names_en = models.CharField(
        "English names",
        unique=True,
        max_length=254,
    )
    """English names.
    Separated with ";" if multiple exist.
    """
    names_fr = models.CharField(
        "noms français",
        unique=True,
        max_length=254,
    )
    """French names.
    Separated with ";" if multiple exist.
    """

    @property
    def loc_uri(self) -> str:
        """URI on the Library of Congress.
        Contains MADS/SKOS RDF data.
        """
        return urljoin("http://id.loc.gov/vocabulary/iso639-5", self.part_5)

    @property
    def ietf(self) -> str:
        """Code used in IETF language tags."""
        return self.part_5

    def __str__(self) -> str:
        return self.part_5

    objects = SimpleISOLanguageCollectionManager()

    class Meta:
        verbose_name = "simple ISO 639-5 language collection"


class ISOLanguageQuerySet(models.QuerySet["ISOLanguage"]):
    def macrolanguages(self) -> ISOLanguageQuerySet:
        return self.filter(scope=ISOLanguage.Scope.MACROLANGUAGE)

    def individuals(self) -> ISOLanguageQuerySet:
        return self.filter(scope=ISOLanguage.Scope.INDIVIDUAL)

    def specials(self) -> ISOLanguageQuerySet:
        return self.filter(scope=ISOLanguage.Scope.SPECIAL)

    def get_from_ietf(self, code: str) -> ISOLanguage:
        if len(code) == 2:
            return self.get(codes__part_1=code)
        elif len(code) == 3:
            for field in ["part_3", "codes__part_2b", "codes__part_2t"]:
                try:
                    return self.get(**{field: code})
                except self.model.DoesNotExist:
                    continue
        else:
            raise InvalidISO639Error(code)
        raise self.model.DoesNotExist(code)


class ISOLanguageManager(BatchedCreateManager["ISOLanguage"]):
    def get_queryset(self) -> ISOLanguageQuerySet:
        return ISOLanguageQuerySet(self.model, using=self._db)

    def individuals(self) -> ISOLanguageQuerySet:
        return self.get_queryset().individuals()

    def macrolanguages(self) -> ISOLanguageQuerySet:
        return self.get_queryset().macrolanguages()

    def specials(self) -> ISOLanguageQuerySet:
        return self.get_queryset().specials()

    def get_from_ietf(self, code: str) -> ISOLanguage:
        return self.get_queryset().get_from_ietf(code)

    def register(
        self, clear=True, batch_size=64, zf: Optional[ZipFile] = None
    ) -> None:
        """Saves ISO 639-3 languages from SIL International."""

        def generate():
            with SilTableReader("iso-639-3", zf) as reader:
                for row in reader:
                    codes = None
                    if row["Part2B"]:
                        try:
                            codes = ISOLanguageCodes.objects.get(
                                part_2b=row["Part2B"],
                                part_2t=row["Part2T"] or None,
                                part_1=row["Part1"] or None,
                            )
                        except ISOLanguageCodes.DoesNotExist:
                            warnings.warn(str(row))
                    yield self.model(
                        codes=codes,
                        part_3=row["Id"],
                        scope=row["Scope"],
                        lang_type=row["Language_Type"],
                        ref_name=row["Ref_Name"],
                        comment=row["Comment"] or None,
                    )

        if clear:
            self.all().delete()
        self.batched_create(generate(), batch_size)

        # Macrolanguage mappings
        mappings: dict[str, list[str]] = {}
        last_m_id = ""
        with SilTableReader("iso-639-3-macrolanguages", zf) as reader:
            for row in reader:
                if row["M_Id"] != last_m_id:
                    last_m_id = row["M_Id"]
                    mappings[last_m_id] = []
                if row["I_Status"] == "A":  # Active
                    mappings[last_m_id].append(row["I_Id"])
                for m_part_3, i_part_3s in mappings.items():
                    self.filter(part_3__in=i_part_3s).update(
                        macrolanguage=self.get(part_3=m_part_3)
                    )


class ISOLanguage(models.Model):
    """Represents an ISO 639-3 language,
    saved from SIL international"""

    class LanguageType(models.TextChoices):
        ANCIENT = "A", "ancient"
        CONSTRUCTED = "C", "constructed"
        EXTINCT = "E", "extinct"
        HISTORICAL = "H", "historical"
        LIVING = "L", "living"
        SPECIAL = "S", "special"

    class Scope(models.TextChoices):
        INDIVIDUAL = "I", "individual"
        MACROLANGUAGE = "M", "macrolanguage"
        SPECIAL = "S", "special"

    names: "models.manager.RelatedManager[ISOLanguageName]"
    """"""
    codes = models.OneToOneField(
        ISOLanguageCodes,
        related_name="language",
        null=True,
        unique=True,
        on_delete=models.CASCADE,
    )
    """ISO 693-1 and 639-2 codes."""
    ref_name = models.CharField(
        "reference name",
        max_length=150,
    )
    """Reference name."""
    part_3 = models.CharField(
        "alpha-3 code (ISO 639-3)",
        unique=True,
        max_length=3,
    )
    """Alpha-3 code (ISO 639-3)."""
    lang_type = models.CharField(
        "type",
        choices=LanguageType.choices,
        max_length=1,
    )
    """Type."""
    scope = models.CharField(choices=Scope.choices, max_length=1)
    """"""
    comment = models.CharField(null=True, max_length=150)
    """"""
    macrolanguage = models.ForeignKey(
        "self",
        related_name="individuals",
        null=True,
        on_delete=models.SET_NULL,
    )
    """Macrolanguage."""

    @property
    def ietf(self) -> str:
        """Shortest ISO 639 code (part 1 or 3)."""
        return self.codes and self.codes.part_1 or self.part_3

    objects = ISOLanguageManager()

    def __str__(self) -> str:
        return f"{self.part_3} - {self.ref_name}"

    class Meta:
        verbose_name = "ISO 639-3 language"


class ISOLanguageNameManager(BatchedCreateManager["ISOLanguageName"]):
    def register(
        self, clear=True, batch_size=64, zf: Optional[ZipFile] = None
    ) -> None:
        """Saves ISO 639-3 language names from SIL International."""
        if clear:
            self.all().delete()

        with SilTableReader("iso-639-3_Name_Index", zf) as reader:
            self.batched_create(
                (
                    self.model(
                        iso_lang=ISOLanguage.objects.get(part_3=row["Id"]),
                        printable=row["Print_Name"],
                        inverted=row["Inverted_Name"],
                    )
                    for row in reader
                ),
                batch_size,
            )


class ISOLanguageName(models.Model):
    """Represents an English name for an ISO 639-3 language,
    saved from SIL International.
    """

    iso_lang = models.ForeignKey(
        ISOLanguage,
        related_name="names",
        on_delete=models.CASCADE,
    )
    """ISO Language."""
    printable = models.CharField(
        "printable translated name",
        max_length=75,
    )
    """Printable translated name."""
    inverted = models.CharField(
        "inverted translated name",
        max_length=75,
    )
    """Inverted translated name."""

    def __str__(self) -> str:
        return self.printable

    objects = ISOLanguageNameManager()

    class Meta:
        verbose_name = "ISO 639-3 language name"
