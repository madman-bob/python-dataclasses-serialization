from dataclasses import dataclass, field
from functools import partial
from operator import le
from typing import Optional, TypeVar, Generic, Dict, Callable, Any, Mapping, Set, Sequence, Iterable

from more_properties import cached_property
from toposort import toposort

__all__ = ["RefinementDict", "AmbiguousKeyError"]


class AmbiguousKeyError(KeyError):
    pass


KeyType = TypeVar("KeyType")
ValueType = TypeVar("ValType")


@dataclass
class RefinementDict(Generic[KeyType, ValueType]):
    """
    A dictionary where the keys are themselves collections

    Indexing an element of these collections returns the value associated with
    the most precise collection containing that element.

    A KeyError is raised if no such collection is found.
    """

    lookup: Dict[KeyType, ValueType] = field(default_factory=dict)
    fallback: Optional['RefinementDict[KeyType, ValueType]'] = None
    is_subset: Callable[[KeyType, KeyType], bool] = le
    is_element: Callable[[KeyType, Set[KeyType]], bool] = lambda elem, st: elem in st

    @cached_property
    def dependencies(self) -> Mapping[KeyType, Set[KeyType]]:
        return {
            st: {
                subst
                for subst in self.lookup
                if subst != st and self.is_subset(subst, st)
            }
            for st in self.lookup
        }

    @dependencies.deleter
    def dependencies(self):
        del self.dependency_orders

    @partial(cached_property, fdel=lambda self: None)
    def dependency_orders(self) -> Iterable[Set[KeyType]]:
        return list(toposort(self.dependencies))

    def __getitem__(self, key: KeyType) -> ValueType:
        for order in self.dependency_orders:
            ancestors = {st for st in order if self.is_element(key, st)}

            if len(ancestors) > 1:
                raise AmbiguousKeyError(f"{key!r} in all of {ancestors!r}")

            if ancestors:
                return self.lookup[ancestors.pop()]

        if self.fallback is not None:
            return self.fallback[key]

        raise KeyError(f"{key!r}")

    def __setitem__(self, key: KeyType, value: ValueType):
        del self.dependencies

        self.lookup[key] = value

    def setdefault(self, key: KeyType, value: ValueType):
        if self.fallback is None:
            self.fallback = RefinementDict(
                is_subset=self.is_subset, is_element=self.is_element
            )

        self.fallback[key] = value
