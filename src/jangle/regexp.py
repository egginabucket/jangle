import re
from typing import Tuple

INCOMPLIANT = 0
COMPLIANT = 1

_SUBTAG_SPLITTER = re.compile(r"(?<!(?<![^-\s])[^-\s])[-\s]")


def split_subtags(string: str) -> list[str]:
    return _SUBTAG_SPLITTER.split(string.strip("-"))


def rfc_re_compile(pattern: str) -> Tuple[re.Pattern[str], re.Pattern[str]]:
    """Compiles one case sensitive regex (useful for making inferences),
    and another one case insensitive (RFC5646 compilant).
    """
    return (re.compile(pattern), re.compile(pattern, flags=re.I))


SUBTAG_LOOKAHEAD_P = r"(?![^-\s])"

# From RFC5646 ABNF definition
SINGLETON_P = r"[a-wy-zA-WY-Z\d]"
PRIVATE_USE_P = r"x(?:-[a-zA-Z\d]{1,8})+"
EXTENSION_P = (
    r"(?P<singleton>%s)(?P<ext_text>(?:-[a-zA-Z\d]{2,8})+)" % SINGLETON_P
)
VARIANT_P = r"[a-z\d]{5,8}|\d[a-z\d]{3}"
REGION_P = r"(?P<iso_3166>[A-Z]{2})|(?P<un_m49>\d{3})"
SCRIPT_P = r"[A-Z][a-z]{3}"
EXTLANG_P = (
    r"(?P<extlang_iso_639>[a-z]{3})(?P<extlang_reserved>(?:-[a-zA-Z]{3}){0,2})"
)
LANGUAGE_P = r"(?P<iso_639>[a-z]{2,3})(?:-(?P<extlang>%s))?" % EXTLANG_P
LANG_TAG_P = (
    r"%s%s(?:-(?P<script>%s)%s)?(?:-(?P<region>%s)%s)?(?P<variants>(?:-(?:%s))*)(?P<extensions>(?:-%s)*)(?:-(?P<private_subtag>%s))?"
    % (
        LANGUAGE_P,
        SUBTAG_LOOKAHEAD_P,
        SCRIPT_P,
        SUBTAG_LOOKAHEAD_P,
        REGION_P,
        SUBTAG_LOOKAHEAD_P,
        VARIANT_P,
        EXTENSION_P,
        PRIVATE_USE_P,
    )
)


LANGUAGE_TAG_RE = rfc_re_compile(
    r"%s|(?P<private_tag>%s)" % (LANG_TAG_P, PRIVATE_USE_P)
)
"""Does not check for grandfathered tags..
Query the database for these before doing anything else.
"""
