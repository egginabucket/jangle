from __future__ import annotations

import csv
import io
import os
import warnings
from typing import Generator, Iterable, Optional, TypeVar
from zipfile import ZipFile

import requests
from requests.compat import urljoin
from requests.models import ITER_CHUNK_SIZE

T = TypeVar("T")

IANA_ASSIGNMENTS_URL = "https://www.iana.org/assignments/"
SIL_ISO_639_DOWNLOADS_URL = (
    "https://iso639-3.sil.org/sites/iso639-3/files/downloads/"
)
SIL_ISO_639_LATEST = "20220311"
SIL_ISO_639_ZIPFILE = f"iso-639-3_Code_Tables_{SIL_ISO_639_LATEST}"


class Record(dict[str, list[str]]):
    """Used for working with record-jar records."""

    def add(self, key: str, val: str) -> None:
        """Adds a value to a field."""
        if key in self:
            self[key].append(val)
        else:
            self[key] = [val]

    def one(self, key: str) -> str:
        """Return a single value from a field.

        Raises
        ------
        ValueError
            If the field has multiple values.
        KeyError
            If the field has no values.
        """
        vals = self[key]
        if len(vals) > 1:
            raise ValueError(f"key '{key}' has multiple values {vals}")
        if not vals:
            raise KeyError(f"key '{key}' has an empty list of values")
        return vals[0]

    def get_one(self, key: str, default: T = None) -> str | T:
        """Return a single value from a field, or `default`.

        Raises
        ------
        ValueError
            If the field has multiple values.
        """
        try:
            return self.one(key)
        except KeyError:
            return default


def parse_record_jar(
    lines: Iterable[str], indent="\t", multiline_separator="\r\n"
) -> Generator[Record, None, None]:
    """Yields records from a set of lines.
    See https://datatracker.ietf.org/doc/pdf/draft-phillips-record-jar-02.
    """
    record = Record()
    key = None
    for line in lines:
        line_text = line.strip()
        if not line_text:
            continue
        if line.startswith(indent):
            if key is None:
                continue
            record[key][-1] += multiline_separator + line_text
        elif line_text == "%%":
            yield record
            record = Record()
        elif ":" in line:
            key, val = line_text.split(":", 1)
            record.add(key.strip(), val.strip())
    yield record


class SilTableReader:
    """Uses `csv.DictReader` to read tab-delimited data
    from https://iso639-3.sil.org/sites/iso639-3/files/downloads/,
    or a ZipFile to minimize requests.

    More information is available at
    https://iso639-3.sil.org/code_tables/download_tables.
    """

    chunk_size = ITER_CHUNK_SIZE

    def __init__(self, fn: str, zf: Optional[ZipFile] = None) -> None:
        self._f = None
        if zf:
            try:
                self._f = zf.open(
                    os.path.join(
                        SIL_ISO_639_ZIPFILE,
                        f"{fn}_{SIL_ISO_639_LATEST}.tab",
                    ),
                    "r",
                )
            except Exception as exc:  # TODO
                warnings.warn(str(exc))
        if self._f is None:
            self._r = requests.get(
                urljoin(SIL_ISO_639_DOWNLOADS_URL, fn + ".tab"), stream=True
            )
            self._r.raise_for_status()
            self._r.encoding = "utf-8"

    def __iter__(self) -> csv.DictReader:
        if self._f:
            it = io.TextIOWrapper(self._f).readlines()
        else:
            it = self._r.iter_lines(self.chunk_size, decode_unicode=True)
        return csv.DictReader(it, dialect="excel-tab")

    def close(self) -> None:
        if self._f:
            self._f.close()
        elif self._r:
            self._r.close()

    def __enter__(self) -> SilTableReader:
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()


class IANARegistryReader:
    """Provides a file date and an iterable of records from an IANA registry."""

    chunk_size = ITER_CHUNK_SIZE
    records: Generator[Record, None, None]
    file_date: str

    def __init__(self, fn: str) -> None:
        response = requests.get(
            urljoin(IANA_ASSIGNMENTS_URL, "/".join([fn, fn])),
            stream=True,
        )
        response.raise_for_status()
        self.records = parse_record_jar(
            response.iter_lines(self.chunk_size, decode_unicode=True),
            indent=" " * 2,
            multiline_separator=" ",
        )
        self.file_date = next(self.records).one("File-Date")


class IANASubtagRegistryReader(IANARegistryReader):
    """Reads https://www.iana.org/assignments/language-subtag-registry/language-subtag-registry."""

    def __init__(self) -> None:
        super().__init__("language-subtag-registry")


class IANAExtensionsRegistryReader(IANARegistryReader):
    def __init__(self) -> None:
        super().__init__("language-extensions-registry")
