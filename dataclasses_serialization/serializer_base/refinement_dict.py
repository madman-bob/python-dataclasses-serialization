from dataclasses import dataclass, field
from functools import partial
from operator import le
from typing import Optional

from more_properties import cached_property
from toposort import toposort

__all__ = ["RefinementDict", "AmbiguousKeyError"]


class AmbiguousKeyError(KeyError):
    pass


@dataclass
class RefinementDict:
    """
    A dictionary where the keys are themselves collections

    Indexing an element of these collections returns the value associated with
    the most precise collection containing that element.

    A KeyError is raised if no such collection is found.
    """

    lookup: dict = field(default_factory=dict)
    fallback: "Optional[RefinementDict]" = None

    is_subset: callable = le
    is_element: callable = lambda elem, st: elem in st

    @cached_property
    def dependencies(self):
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
    def dependency_orders(self):
        return list(toposort(self.dependencies))

    def __getitem__(self, key):
        for order in self.dependency_orders:
            ancestors = {st for st in order if self.is_element(key, st)}

            if len(ancestors) > 1:
                raise AmbiguousKeyError(f"{key!r} in all of {ancestors!r}")

            if ancestors:
                return self.lookup[ancestors.pop()]

        if self.fallback is not None:
            return self.fallback[key]

        raise KeyError(f"{key!r}")

    def __setitem__(self, key, value):
        del self.dependencies

        self.lookup[key] = value

    def setdefault(self, key, value):
        if self.fallback is None:
            self.fallback = RefinementDict(
                is_subset=self.is_subset, is_element=self.is_element
            )

        self.fallback[key] = value
