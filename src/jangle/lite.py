from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from jangle.patterns import RULES, match_rule
from jangle.utils import StrReprCls, split_subtags


@dataclass(repr=False)
class Extension(StrReprCls):
    singleton: str
    texts: list[str]

    @classmethod
    def from_match(cls, match: re.Match) -> Extension:
        return cls(
            singleton=match.group("singleton"),
            texts=split_subtags(match.group("ext_text")),
        )

    @classmethod
    def from_str(cls, string: str) -> Extension:
        return cls.from_match(match_rule("extension", string))

    def __str__(self) -> str:
        return "-".join([self.singleton, *self.texts])


@dataclass(repr=False)
class LangTag(StrReprCls):
    lang: str
    extlang: Optional[str] = None
    script: Optional[str] = None
    region: Optional[str] = None
    variants: list[str] = field(default_factory=list)
    extensions: list[Extension] = field(default_factory=list)
    private: Optional[str] = None

    @classmethod
    def from_groups(cls, groups: dict[str, str]) -> LangTag:
        langtag = cls(
            lang=groups["iso_639"].lower(),
            extlang=groups["extlang"].lower() or None,
            script=groups["script"].title() or None,
            region=groups["region"].upper() or None,
            private=groups["private_subtag"].lower().removeprefix("x-")
            or None,
        )
        if groups["variants"]:
            langtag.variants = split_subtags(groups["variants"].lower())
        langtag.extensions = list(
            map(
                Extension.from_match,
                RULES["extension"].finditer(groups["extensions"].lower()),
            )
        )
        return langtag

    @classmethod
    def from_match(cls, match: re.Match[str]) -> LangTag:
        return cls.from_groups(match.groupdict(""))

    @classmethod
    def from_str(cls, string: str) -> LangTag:
        return cls.from_match(match_rule("langtag", string))

    def __str__(self) -> str:
        subtags = [self.lang]
        subtags.extend(
            filter(
                None,
                [
                    self.extlang,
                    self.script,
                    self.region,
                ],
            )
        )
        subtags.extend(self.variants)
        subtags.extend(map(str, self.extensions))
        if self.private:
            subtags.extend(["x", self.private])
        return "-".join(subtags)

    def __contains__(self, val: LangTag | re.Match[str] | str) -> bool:
        if isinstance(val, re.Match):
            val = self.__class__.from_match(val)
        elif isinstance(val, str):
            val = self.__class__.from_str(val)
        if val.lang != self.lang:
            return False
        for attr_name in ["script", "extlang", "region", "private"]:
            attr = getattr(val, attr_name)
            if attr and attr != getattr(self, attr_name):
                return False
        for variant in val.variants:
            if variant not in self.variants:
                return False
        self_extensions = set(map(str, self.extensions))
        for extension in val.extensions:
            if str(extension) not in self_extensions:
                return False
        return True


@dataclass(repr=False)
class LanguageTag(StrReprCls):
    langtag: Optional[LangTag]
    private: Optional[str]
    grandfathered: Optional[str]

    @classmethod
    def from_match(cls, match: re.Match) -> LanguageTag:
        groups = match.groupdict("")
        lite = cls(
            langtag=None,
            private=groups["private_tag"].lower().removeprefix("x-") or None,
            grandfathered=groups["grandfathered"].lower() or None,
        )
        if groups["langtag"]:
            lite.langtag = LangTag.from_groups(groups)
        return lite

    @classmethod
    def from_str(cls, string: str) -> LanguageTag:
        return cls.from_match(match_rule("Language-Tag", string))

    def __str__(self) -> str:
        if self.grandfathered:
            return self.grandfathered
        if self.private:
            return "-".join(["x", self.private])
        return str(self.langtag)
