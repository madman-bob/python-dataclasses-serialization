from typing import TypeVar, Union
from unittest import TestCase

from dataclasses_serialization.serializer_base import (
    DeserializationError,
    union_deserialization,
)


class TestUnion(TestCase):
    def test_union_deserialization_basic(self):
        with self.subTest("Deserialize union first argument"):
            self.assertEqual(1, union_deserialization(Union[int, str], 1))

        with self.subTest("Deserialize union second argument"):
            self.assertEqual(1, union_deserialization(Union[str, int], 1))

        with self.subTest("Deserialize union many arguments"):
            self.assertEqual(
                1, union_deserialization(Union[str, list, dict, int, tuple], 1)
            )

        with self.subTest("Deserialize generic union"):
            T = TypeVar("T")

            self.assertEqual(1, union_deserialization(Union[str, T][int], 1))
            self.assertEqual(1, union_deserialization(Union[T, int][str], 1))

        with self.subTest("Invalid union deserialization"), self.assertRaises(
            DeserializationError
        ):
            union_deserialization(Union[str, list], 1)

    def test_union_deserialization_deserialization_func(self):
        self.assertEqual(
            1,
            union_deserialization(
                Union[int, str], "1", deserialization_func=lambda cls, obj: int(obj)
            ),
        )
