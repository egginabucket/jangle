from typing import TypeVar, Any, Optional, Iterable
from itertools import islice
from django.db import models


def findattr(obj, path) -> Optional[Any]:
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
        raise ValueError("path should be list[str | tuple] or tuple[str | list]")


def choice_from_iana(choices: type[models.TextChoices], string: str):
    return getattr(choices, string.upper().replace("-", "_"))


_T = TypeVar("_T", bound=models.Model)


class BatchedCreateManager(models.Manager[_T]):
    def batched_create(self, objs: Iterable, batch_size=64, **kwargs) -> None:
        while True:
            batch = list(islice(objs, batch_size))
            if not batch:
                break
            self.bulk_create(batch, batch_size, **kwargs)
