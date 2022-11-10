# jangle

IETF BCP 47 / RFC 5646 language tags in Django

---

[![PyPI Version](https://img.shields.io/pypi/v/django-jangle.svg)](https://pypi.org/project/django-jangle/)
[![License](https://img.shields.io/pypi/l/django-jangle.svg)](https://pypi.org/project/django-jangle/)
[![Python Versions](https://img.shields.io/pypi/pyversions/django-jangle.svg)](https://pypi.org/project/django-jangle/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Use in your project!

- install: `pip install django-jangle`
- add `jangle` to `settings.INSTALLED_APPS` and apply migrations
- run `manage.py loadjangledata` to populate database

## Documentation

Documentation is available at [jangle.readthedocs.io](https://jangle.readthedocs.io/en/latest/). Currently a work in progress.

## Data provided

- [ISO 15924 scripts](https://www.unicode.org/iso15924/) from unicode.org
- [ISO 639-1, 639-2/b, 639-2/t](https://www.loc.gov/standards/iso639-2/langhome.html) and [639-5](https://www.loc.gov/standards/iso639-5/) codes and names from the Library of Congress
- [ISO 639-3 code set, names and macrolanguages](https://iso639-3.sil.org/code_tables/download_tables) from SIL International
- ISO 3166-1 and UN M.49 regions - currently a WIP
- Full [IANA subtag registry](https://www.iana.org/assignments/language-subtag-registry/language-subtag-registry) saved across various tables, including grandfathered and redundant tags. Linked with other standards and used to construct and verify language tags

## Example usage

TODO
