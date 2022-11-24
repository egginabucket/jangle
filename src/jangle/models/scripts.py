import csv

import requests
from django.db import models

from jangle.utils import BatchedCreateManager


class ScriptManager(BatchedCreateManager["Script"]):
    def register(self, clear=True, batch_size=64) -> None:
        """Saves IS0 15924 scripts from unicode.org to the database.
        See https://www.unicode.org/iso15924/iso15924.txt.
        """
        r = requests.get("https://www.unicode.org/iso15924/iso15924.txt")
        r.raise_for_status()

        def line_is_valid(line: str) -> bool:
            line = line.strip()
            return bool(line and not line.startswith("#"))

        if clear:
            self.all().delete()
        fieldnames = [
            "code",
            "no",
            "names_en",
            "names_fr",
            "pva",
            "unicode_version",
            "script_date",
        ]
        self.batched_create(
            (
                self.model(
                    **{key: val or None for key, val in row.items()},
                )
                for row in csv.DictReader(
                    filter(line_is_valid, r.iter_lines(decode_unicode=True)),
                    fieldnames,
                    delimiter=";",
                )
            ),
            batch_size,
        )


class Script(models.Model):
    """Represents an ISO 15924 script,
    saved from https://www.unicode.org/iso15924/.
    """

    code = models.CharField(
        "ISO 15924 code",
        unique=True,
        max_length=4,
    )
    """ISO 15924 code."""
    no = models.PositiveSmallIntegerField(
        "ISO 15924 number",
        unique=True,
    )
    """ISO 15924 number."""
    names_en = models.CharField(
        "English names",
        unique=True,
        max_length=254,
    )
    """English names."""
    names_fr = models.CharField(
        "noms français",
        unique=True,
        max_length=254,
    )
    """French names."""
    pva = models.CharField(
        "property value alias",
        null=True,
        max_length=150,
    )
    """Unicode property value alias.
    See https://www.unicode.org/Public/UCD/latest/ucd/PropertyValueAliases.txt.
    """
    unicode_version = models.CharField(null=True, max_length=12)
    """"""
    script_date = models.DateField("date")
    """Date."""

    @property
    def no_str(self) -> str:
        """Formatted string of ISO 15924 number."""
        return "{:03d}".format(self.no)

    def __str__(self) -> str:
        return self.code

    objects = ScriptManager()

    class Meta:
        verbose_name = "ISO 15924 script"
