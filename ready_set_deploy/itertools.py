from typing import TypeVar, Optional
from collections.abc import Iterable, Callable
from collections import defaultdict

_K = TypeVar("_K")
_V = TypeVar("_V")


def dict_matching(*dicts: dict[_K, _V], default: Optional[_V] = None) -> Iterable[tuple[_K, list[Optional[_V]]]]:
    seen: set[_K] = set()
    for d in dicts:
        for key in d:
            if key in seen:
                continue
            seen.add(key)

            # get elements from each dict
            yield key, [od.get(key, default) for od in dicts]


def iter_matching(*iters: Iterable[_V], key: Callable[[_V], _K], default: Optional[_V] = None) -> Iterable[tuple[_K, list[Optional[_V]]]]:
    by_key = defaultdict(lambda: [default] * len(iters))
    for i, items in enumerate(iters):
        for item in items:
            k = key(item)
            result = by_key[k]
            result[i] = item

    for k, items in by_key.items():
        yield k, items
