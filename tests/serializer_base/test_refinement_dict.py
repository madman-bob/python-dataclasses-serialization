from dataclasses import dataclass
from operator import le
from unittest import TestCase

from dataclasses_serialization.serializer_base.refinement_dict import (
    AmbiguousKeyError,
    RefinementDict,
)


@dataclass(frozen=True)
class LatticePoint:
    x: int
    y: int

    def __le__(self, other):
        return self.x <= other.x and self.y <= other.y


a, b, c, d = [
    frozenset({1}),
    frozenset({2}),
    frozenset({1, 2}),
    frozenset({2, 3}),
]

w, x, y, z = [
    LatticePoint(-1, 0),
    LatticePoint(0, -1),
    LatticePoint(-1, -1),
    LatticePoint(-2, -2),
]


class TestRefinementDict(TestCase):
    def test_refinement_dict_basic(self):
        dct = RefinementDict({a: "a", b: "b"})

        self.assertEqual("a", dct[1])
        self.assertEqual("b", dct[2])

        with self.assertRaises(KeyError):
            dct[3]

    def test_refinement_dict_refinement(self):
        dct = RefinementDict({a: "a", c: "c"})

        self.assertEqual("a", dct[1])
        self.assertEqual("c", dct[2])

    def test_refinement_dict_ambiguous(self):
        dct = RefinementDict({c: "c", d: "d"})

        with self.subTest("With ambiguity"):
            with self.assertRaises(AmbiguousKeyError):
                dct[2]

        with self.subTest("Resolve ambiguity"):
            dct[b] = "b"

            self.assertEqual("b", dct[2])

    def test_refinement_dict_lattice(self):
        dct = RefinementDict({w: "w", x: "x"}, is_element=le)

        self.assertEqual("w", dct[w])
        self.assertEqual("x", dct[x])

    def test_refinement_dict_lattice_refinement(self):
        dct = RefinementDict({w: "w"}, is_element=le)

        self.assertEqual("w", dct[y])

    def test_refinement_dict_lattice_ambiguous(self):
        dct = RefinementDict({w: "w", x: "x"}, is_element=le)

        with self.subTest("With ambiguity"):
            with self.assertRaises(AmbiguousKeyError):
                dct[z]

        with self.subTest("Resolve ambiguity"):
            dct[y] = "y"

            self.assertEqual("y", dct[z])

    def test_refinement_dict_setdefault(self):
        dct = RefinementDict({w: "w"}, is_element=le)

        dct.setdefault(x, "x")

        with self.subTest("Existing values ignore default"):
            self.assertEqual("w", dct[w])
            self.assertEqual("w", dct[y])
            self.assertEqual("w", dct[z])

        with self.subTest("Fall back to default value"):
            self.assertEqual("x", dct[x])
