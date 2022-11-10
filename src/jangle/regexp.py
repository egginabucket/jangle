import re
from typing import Tuple

INCOMPLIANT = 0
COMPLIANT = 1

_SUBTAG_SPLITTER = re.compile(r"(?<!(?<![^-\s])[^-\s])[-\s]")


def split_subtags(string: str) -> list[str]:
    """Splits a tag or string of subtags."""
    return _SUBTAG_SPLITTER.split(string.strip("-"))


def rfc_re_compile(pattern: str) -> Tuple[re.Pattern[str], re.Pattern[str]]:
    """Compiles one case sensitive regex (useful for making inferences),
    and another one case insensitive (RFC5646 compilant).
    """
    return (re.compile(pattern), re.compile(pattern, flags=re.I))


SUBTAG_LOOKAHEAD_P = r"(?![^-\s])"
"""Checks if there is no subtag immediately ahead."""

# From RFC5646 ABNF definition
SINGLETON_P = r"[a-wy-zA-WY-Z\d]"
"""A pattern for `singleton` as defined in the RFC 5646 ABNF."""
PRIVATE_USE_P = r"x(?:-[a-zA-Z\d]{1,8})+"
"""A pattern for `private-use` as defined in the RFC 5646 ABNF."""
EXTENSION_P = (
    r"(?P<singleton>%s)(?P<ext_text>(?:-[a-zA-Z\d]{2,8})+)" % SINGLETON_P
)
"""A pattern for `extension` as defined in the RFC 5646 ABNF."""
VARIANT_P = r"[a-z\d]{5,8}|\d[a-z\d]{3}"
"""A pattern for `variant` as defined in the RFC 5646 ABNF."""
REGION_P = r"(?P<iso_3166>[A-Z]{2})|(?P<un_m49>\d{3})"
"""A pattern for `singleton` as defined in the RFC 5646 ABNF."""
SCRIPT_P = r"[A-Z][a-z]{3}"
"""A pattern for `script` as defined in the RFC 5646 ABNF,
with title-casing for making inferences."""
EXTLANG_P = (
    r"(?P<extlang_iso_639>[a-z]{3})(?P<extlang_reserved>(?:-[a-zA-Z]{3}){0,2})"
)
"""A pattern for `extlang` as defined in the RFC 5646 ABNF."""
LANGUAGE_P = r"(?P<iso_639>[a-z]{2,3})(?:-(?P<extlang>%s))?" % EXTLANG_P
"""A pattern for `language` as defined in the RFC 5646 ABNF."""
LANGTAG_P = (
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
"""A pattern for `langtag` as defined in the RFC 5646 ABNF."""
LANGUAGE_TAG_P = r"%s|(?P<private_tag>%s)" % (LANGTAG_P, PRIVATE_USE_P)
"""A pattern for `Language-Tag` as defined in the RFC 5646 ABNF."""

LANGUAGE_TAG_RE = rfc_re_compile(LANGUAGE_TAG_P)
"""Compliant and incompliant compiled patterns
for `Language-Tag` as defined in the RFC 5646 ABNF.
Does not check for grandfathered tags;
query the database for these before doing anything else.
"""
