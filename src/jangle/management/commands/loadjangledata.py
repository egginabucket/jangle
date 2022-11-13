from django.core.management.base import BaseCommand, CommandParser

import io
import warnings
import zipfile

import requests
from requests.compat import urljoin

from jangle.models import (
    IANASubtagRegistry,
    ISOLanguage,
    ISOLanguageCodes,
    ISOLanguageName,
    LanguageTag,
    Script,
)
from jangle.readers import SIL_ISO_639_DOWNLOADS_URL, SIL_ISO_639_ZIPFILE


class Command(BaseCommand):
    help = "Saves Jangle data from various sources to the database."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "-c",
            "--clear",
            action="store_true",
            help="Deletes existing data",
        )
        parser.add_argument(
            "-C",
            "--clear-tags",
            action="store_true",
            help="Deletes existing data and language tags",
        )
        parser.add_argument(
            "-b",
            "--batch-size",
            default=128,
            help="Insert batch size",
        )

    def handle(self, *args, **options) -> None:
        if options["clear_tags"]:
            LanguageTag.objects.all().delete()
        clear = options["clear"] or options["clear_tags"]
        batch_size = options["batch_size"]
        self.stdout.write("Registering ISO 639-2 and 639-1 codes...")
        ISOLanguageCodes.objects.register(clear, batch_size)
        self.stdout.write("Requesting ISO 639-3 code tables as zip...")
        r = requests.get(
            urljoin(
                SIL_ISO_639_DOWNLOADS_URL,
                SIL_ISO_639_ZIPFILE + ".zip",
            ),
            stream=True,
        )
        try:
            r.raise_for_status()
            zf = zipfile.ZipFile(io.BytesIO(r.content))
        except requests.HTTPError as err:
            warnings.warn(err.args[0])
            self.stdout.write(
                self.style.WARNING(
                    "Could not retrieve ISO 639-3 zip, "
                    "requesting tables individually...",
                )
            )
            zf = None
        self.stdout.write("Saving ISO 639-3 language codes...")
        ISOLanguage.objects.register(clear, batch_size, zf)
        self.stdout.write("Saving ISO 639-3 language names...")
        ISOLanguageName.objects.register(clear, batch_size, zf)
        self.stdout.write("Registering ISO 15924 scripts...")
        Script.objects.register(clear, batch_size)
        self.stdout.write("Registering subtags and tags from IANA...")
        IANASubtagRegistry.objects.register(clear, batch_size)
        self.stdout.write(self.style.SUCCESS("Done!"))
