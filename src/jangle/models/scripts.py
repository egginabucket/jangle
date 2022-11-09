import csv

import requests
from django.db import models

from .utils import BatchedCreateManager


class ScriptManager(BatchedCreateManager["Script"]):
    def register(self, clear=True, batch_size=64) -> None:
        """Saves IS0 15924 scripts from unicode.org to the database."""
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
    """Represents an ISO 15924 script.
    From https://www.unicode.org/iso15924/,
    """

    code = models.CharField("ISO 15924 code", unique=True, max_length=4)
    no = models.PositiveSmallIntegerField("ISO 15924 number", unique=True)
    names_en = models.CharField("English name", unique=True, max_length=75)
    names_fr = models.CharField("nom français", unique=True, max_length=75)
    pva = models.CharField("property value alias", null=True, max_length=150)
    unicode_version = models.CharField(null=True, max_length=12)
    script_date = models.DateField()

    @property
    def no_str(self) -> str:
        return "{:03d}".format(self.no)

    def __str__(self) -> str:
        return self.code

    objects = ScriptManager()

    class Meta:
        verbose_name = "ISO 15924 script"
