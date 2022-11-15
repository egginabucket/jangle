import re
from itertools import islice
from typing import Any, Iterable, Optional, TypeVar

from django.db import models


class StrReprCls:
    """Provides __repr__ showing
    the object's module, class name and string representation.
    """

    def __repr__(self) -> str:
        return f"<{self.__module__}.{type(self).__qualname__} '{str(self)}'>"


def findattr(obj, path) -> Optional[Any]:
    """This thing is goofy. Don't use it."""
    if isinstance(path, tuple):
        for subpath in path:
            attr = findattr(obj, subpath)
            if attr is not None:
                return attr
    elif isinstance(path, list):
        if len(path) < 1:
            raise ValueError("empty path")
        obj = getattr(obj, path.pop(0))
        if not path:
            return obj
        elif len(path) > 1:
            return findattr(obj, path)
    else:
        raise TypeError(
            "path should be list[str | tuple] or tuple[str | list]"
        )


def choice_from_iana(choices: type[models.TextChoices], string: str) -> Any:
    """Chooses a Django TextChoices field from text used in the IANA registry."""
    return getattr(choices, string.upper().replace("-", "_"))


_T = TypeVar("_T", bound=models.Model)


class BatchedCreateManager(models.Manager[_T]):
    """"""

    def batched_create(self, objs: Iterable, batch_size=64, **kwargs) -> None:
        """Bulk-creates objects in batches of specified size."""
        it = iter(objs)
        while True:
            batch = list(islice(it, batch_size))
            if not batch:
                break
            self.bulk_create(batch, batch_size, **kwargs)


def split_subtags(string: str) -> list[str]:
    """Splits a tag or string of subtags."""
    return re.split(r"(?<!(?<![^\-\s])[^\-\s])[\-\s]", string.strip("-"))
