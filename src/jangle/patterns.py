import re
import tempfile

_SUBTAG_LOOKAHEAD = r"(?![^\-\s])"
"""Checks if there is no subtag immediately ahead."""

_ALPHANUM = r"[A-Za-z\d]"
_REGULAR = r"|".join(
    map(
        re.escape,
        [
            "art-lojban",
            "cel-gaulish",
            "no-bok",
            "no-nyn",
            "zh-guoyo",
            "zh-hakka",
            "zh-min",
            "zh-min-nan",
            "zh-xiang",
        ],
    )
)
_IRREGULAR = (
    r"en\-GB\-oed|i\-(?:%s)|sgn\-(?:BE\-FR|BE\-NL|CH\-DE)"
    % r"|".join(
        [
            "ami",
            "bnn",
            "default",
            "enochian",
            "hak",
            "klingon",
            "lux",
            "mingo",
            "navajo",
            "tao",
            "tay",
            "tsu",
        ]
    )
)
_GRANDFATHERED = r"(?P<regular>%s)|(?P<irregular>%s)" % (_REGULAR, _IRREGULAR)
_SINGLETON = r"[A-WY-Za-wy-z\d]"
_PRIVATEUSE = r"x(?:\-%s{1,8})+" % _ALPHANUM
_EXTENSION = r"(?P<singleton>%s)(?P<ext_text>(?:\-%s{2,8})+)" % (
    _SINGLETON,
    _ALPHANUM,
)
_VARIANT = r"%s{5,8}|\d%s{3}" % (_ALPHANUM, _ALPHANUM)
_REGION = r"(?P<iso_3166>[A-Za-z]{2})|(?P<un_m49>\d{3})"
_SCRIPT = r"[A-Za-z]{4}"
_EXTLANG = r"(?P<extlang_iso_639>[A-Za-z]{3})(?P<extlang_reserved>(?:\-[A-Za-z]{3}){0,2})"
_LANGUAGE = r"(?P<iso_639>[A-Za-z]{2,3})(?:\-(?P<extlang>%s))?" % _EXTLANG
_LANGTAG = (
    r"%s%s(?:\-(?P<script>%s)%s)?(?:\-(?P<region>%s)%s)?(?P<variants>(?:\-(?:%s))*)(?P<extensions>(?:\-%s)*)(?:\-(?P<private_subtag>%s))?"
    % (
        _LANGUAGE,
        _SUBTAG_LOOKAHEAD,
        _SCRIPT,
        _SUBTAG_LOOKAHEAD,
        _REGION,
        _SUBTAG_LOOKAHEAD,
        _VARIANT,
        _EXTENSION,
        _PRIVATEUSE,
    )
)

RULES: dict[str, re.Pattern[str]] = {
    key: re.compile(pattern, flags=re.I)
    for key, pattern in {
        "Language-Tag": r"(?P<grandfathered>%s)|(?P<private_tag>%s)|(?P<langtag>%s)"
        % (_GRANDFATHERED, _PRIVATEUSE, _LANGTAG),
        "langtag": _LANGTAG,
        "language": _LANGUAGE,
        "extlang": _EXTLANG,
        "script": _SCRIPT,
        "region": _REGION,
        "variant": _VARIANT,
        "extension": _EXTENSION,
        "singleton": _SINGLETON,
        "privateuse": _PRIVATEUSE,
        "grandfathered": _GRANDFATHERED,
        "regular": _REGULAR,
        "irregular": _IRREGULAR,
        "alphanum": _ALPHANUM,
    }.items()
}
"""RegEx patterns for rules from the
RFC 5646 ABNF syntax definition.
See https://www.rfc-editor.org/rfc/rfc5646.html#section-2.1.
"""


def match_rule(rule: str, string: str) -> re.Match[str]:
    match = RULES[rule].fullmatch(string)
    if match is None:
        raise ValueError(f"invalid {rule}: {string}")
    return match


def rules_rst() -> str:
    """Saves a temporary reStructuredText file
    documenting all rule patterns, used in `docs/source/patterns.rst`
    """
    _, temp = tempfile.mkstemp(
        text=True,
        prefix="jangle_rfc5646_rules_",
        suffix=".rst",
    )
    with open(temp, "w") as f:
        for rule, pattern in RULES.items():
            f.write(f"{rule}:\r\n\r\n")
            f.write(
                ":regexp:`%s`\r\n\r\n" % pattern.pattern.replace("\\", r"\\")
            )
    return temp
