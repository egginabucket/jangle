from pathlib import Path

import django
from django.conf import settings

BASE_DIR = Path(__file__).resolve().parents[1]


def boot_django() -> None:
    """Boots Django with jangle and a sqlite DB for development."""
    settings.configure(
        BASE_DIR=BASE_DIR,
        DEBUG=True,
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": BASE_DIR.parent / "db.sqlite3",
            },
        },
        INSTALLED_APPS=[
            "jangle",
        ],
        LANGUAGE_CODE="en-US",
        TIME_ZONE="UTC",
        USE_TZ=True,
    )

    django.setup()
