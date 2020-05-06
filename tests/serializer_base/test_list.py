from typing import Dict, List, TypeVar
from unittest import TestCase

from dataclasses_serialization.serializer_base import (
    DeserializationError,
    list_deserialization,
)


class TestListSerialization(TestCase):
    def test_list_deserialization_basic(self):
        T = TypeVar("T")

        with self.subTest("Deserialize list noop"):
            self.assertEqual([1, 2], list_deserialization(list, [1, 2]))
            self.assertEqual([1, 2], list_deserialization(List, [1, 2]))

        with self.subTest("Deserialize list"):
            self.assertEqual([1, 2], list_deserialization(List[int], [1, 2]))

        with self.subTest("Deserialize generic list"):
            self.assertEqual(
                [{"a": 1}, {"b": 2}],
                list_deserialization(List[Dict[str, T]][int], [{"a": 1}, {"b": 2}]),
            )

        with self.subTest("Fail invalid value deserialization"), self.assertRaises(
            DeserializationError
        ):
            list_deserialization(List[str], [1, 2])

        with self.subTest("Fail invalid generic deserialization"), self.assertRaises(
            DeserializationError
        ):
            list_deserialization(List[Dict[str, T]][int], [1, 2])

    def test_list_deserialization_deserialization_func(self):
        self.assertEqual(
            [0, 1],
            list_deserialization(
                List[int], [1, 2], deserialization_func=lambda cls, obj: obj - 1
            ),
        )
