from typing import Dict, TypeVar
from unittest import TestCase

from dataclasses_serialization.serializer_base import (
    DeserializationError,
    dict_deserialization,
    dict_serialization,
)


class TestDictSerialization(TestCase):
    def test_dict_serialization_basic(self):
        self.assertEqual({"key": "Value"}, dict_serialization({"key": "Value"}))

    def test_dict_serialization_serialization_func(self):
        with self.subTest("Serialize dict key serialization function"):
            self.assertEqual(
                {"0": 1}, dict_serialization({0: 1}, key_serialization_func=str)
            )

        with self.subTest("Serialize dict value serialization function"):
            self.assertEqual(
                {0: "1"}, dict_serialization({0: 1}, value_serialization_func=str)
            )

    def test_dict_deserialization_basic(self):
        T = TypeVar("T")

        with self.subTest("Deserialize dict noop"):
            self.assertEqual(
                {"key": "Value"}, dict_deserialization(dict, {"key": "Value"})
            )
            self.assertEqual(
                {"key": "Value"}, dict_deserialization(Dict, {"key": "Value"})
            )

        with self.subTest("Deserialize dict"):
            self.assertEqual(
                {"key": "Value"}, dict_deserialization(Dict[str, str], {"key": "Value"})
            )

        with self.subTest("Deserialize generic dict"):
            self.assertEqual(
                {"key": "Value"},
                dict_deserialization(Dict[T, T][str], {"key": "Value"}),
            )

        with self.subTest("Fail invalid key deserialization"), self.assertRaises(
            DeserializationError
        ):
            dict_deserialization(Dict[str, str], {0: "Value"})

        with self.subTest("Fail invalid value deserialization"), self.assertRaises(
            DeserializationError
        ):
            dict_deserialization(Dict[str, str], {"key": 1})

        with self.subTest("Fail invalid generic deserialization"), self.assertRaises(
            DeserializationError
        ):
            dict_deserialization(Dict[T, str][int], {0: 1})

    def test_dict_deserialization_deserialization_func(self):
        with self.subTest("Deserialize dict key deserialization function"):
            self.assertEqual(
                {"0": 1},
                dict_deserialization(
                    Dict[str, int],
                    {0: 1},
                    key_deserialization_func=lambda cls, obj: str(obj),
                ),
            )

        with self.subTest("Deserialize dict value deserialization function"):
            self.assertEqual(
                {0: "1"},
                dict_deserialization(
                    Dict[int, str],
                    {0: 1},
                    value_deserialization_func=lambda cls, obj: str(obj),
                ),
            )
