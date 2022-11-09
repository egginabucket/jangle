import io
import warnings
import zipfile

import requests
from requests.compat import urljoin

if __name__ == "__main__":
    from jangle.boot_django import boot_django

    boot_django()

from jangle.models import (
    IANASubtagRegistry,
    ISOLanguage,
    ISOLanguageCodes,
    ISOLanguageName,
    Script,
)
from jangle.readers import SIL_ISO_639_DOWNLOADS_URL, SIL_ISO_639_ZIPFILE


def load_db(batch_size=128) -> None:
    print("Registering ISO 639-2 and 639-1 codes...")
    ISOLanguageCodes.objects.register(batch_size=batch_size)
    print("Requesting ISO 639-3 code tables as zip...")
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
        print(
            "Could not retrieve ISO 639-3 zip,",
            "requesting tables individually...",
        )
        zf = None
    print("Saving ISO 639-3 language codes...")
    ISOLanguage.objects.register(batch_size=batch_size, zf=zf)
    print("Saving ISO 639-3 language codes...")
    ISOLanguageName.objects.register(batch_size=batch_size, zf=zf)
    print("Registering ISO 15924 scripts...")
    Script.objects.register(batch_size=batch_size)
    print("Registering subtags and tags from IANA...")
    IANASubtagRegistry.objects.register(descriptions_batch_size=batch_size)
    print("Done!")

if __name__ == "__main__":
    load_db()
