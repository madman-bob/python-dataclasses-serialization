from dataclasses import dataclass
from os import environ
from typing import Dict, Generic, List, TypeVar
from unittest import TestCase

from dataclasses_serialization.serializer_base import (
    DeserializationError,
    dict_deserialization,
    dict_to_dataclass,
    list_deserialization,
)

postponed_annotations = bool(
    environ.get("POSTPONED_ANNOTATIONS", "annotations" in globals())
)

if postponed_annotations:
    # __future__.annotations require type variables used be in global scope
    # See PEP 563
    # > Annotations can only use names present in the module scope

    T = TypeVar("T")


class TestDictToDataclass(TestCase):
    def test_dict_to_dataclass_basic(self):
        @dataclass
        class ExampleDataclass:
            int_field: int
            str_field: str
            optional_field: str = ""

        with self.subTest("Deserialize basic dict"):
            self.assertEqual(
                ExampleDataclass(1, "Hello, world", "Lorem ipsum"),
                dict_to_dataclass(
                    ExampleDataclass,
                    {
                        "int_field": 1,
                        "str_field": "Hello, world",
                        "optional_field": "Lorem ipsum",
                    },
                ),
            )

        with self.subTest("Fill in optional field"):
            self.assertEqual(
                ExampleDataclass(1, "Hello, world"),
                dict_to_dataclass(
                    ExampleDataclass, {"int_field": 1, "str_field": "Hello, world"}
                ),
            )

        with self.subTest("Fail missing field deserialization"), self.assertRaises(
            DeserializationError
        ):
            dict_to_dataclass(ExampleDataclass, {"int_field": 1})

        with self.subTest("Fail non-dict deserialization"), self.assertRaises(
            DeserializationError
        ):
            dict_to_dataclass(ExampleDataclass, 1)

    def test_dict_to_dataclass_deserialization_func(self):
        @dataclass
        class ExampleDataclass:
            int_field: int

        with self.subTest("Invalid deserialization"), self.assertRaises(
            DeserializationError
        ):
            dict_to_dataclass(ExampleDataclass, {"int_field": "1"})

        with self.subTest("Using deserialization func"):
            self.assertEqual(
                ExampleDataclass(1),
                dict_to_dataclass(
                    ExampleDataclass,
                    {"int_field": "1"},
                    deserialization_func=lambda cls, obj: int(obj),
                ),
            )

    def test_dict_to_dataclass_generics(self):
        # Shadowing a non-identical TypeVar of the same name interacts strangely with postponing annotations
        # So use the one in outer scope (if it exists)
        T = globals().get("T", TypeVar("T"))

        @dataclass
        class ExampleRedundantGenericDataclass(Generic[T]):
            s: str

        @dataclass
        class ExampleGenericTypeVarDataclass(Generic[T]):
            t: T

        @dataclass
        class ExampleGenericCompoundDataclass(Generic[T]):
            t_dict: Dict[str, T]

        with self.subTest("Fail generic deserialization"):
            with self.assertRaises(DeserializationError):
                dict_to_dataclass(ExampleRedundantGenericDataclass, {"s": "a"})

            with self.assertRaises(DeserializationError):
                dict_to_dataclass(ExampleGenericTypeVarDataclass, {"t": "a"})

            with self.assertRaises(DeserializationError):
                dict_to_dataclass(ExampleGenericCompoundDataclass, {"t_dict": {}})

        with self.subTest("Deserialize bound generics"):
            self.assertEqual(
                ExampleRedundantGenericDataclass("a"),
                dict_to_dataclass(ExampleRedundantGenericDataclass[int], {"s": "a"}),
            )

            self.assertEqual(
                ExampleGenericTypeVarDataclass("a"),
                dict_to_dataclass(ExampleGenericTypeVarDataclass[str], {"t": "a"}),
            )
            self.assertEqual(
                ExampleGenericTypeVarDataclass(1),
                dict_to_dataclass(ExampleGenericTypeVarDataclass[int], {"t": 1}),
            )

            self.assertEqual(
                ExampleGenericCompoundDataclass({"a": "b"}),
                dict_to_dataclass(
                    ExampleGenericCompoundDataclass[str], {"t_dict": {"a": "b"}}
                ),
            )
            self.assertEqual(
                ExampleGenericCompoundDataclass({"a": 1}),
                dict_to_dataclass(
                    ExampleGenericCompoundDataclass[int], {"t_dict": {"a": 1}}
                ),
            )

        with self.subTest("Deserialize indirectly bound generics"):
            self.assertEqual(
                ExampleGenericTypeVarDataclass(["a", "b"]),
                dict_to_dataclass(
                    ExampleGenericTypeVarDataclass[List[T]][str],
                    {"t": ["a", "b"]},
                    deserialization_func=list_deserialization,
                ),
            )

            self.assertEqual(
                ExampleGenericCompoundDataclass({"a": ["a", "b"]}),
                dict_to_dataclass(
                    ExampleGenericCompoundDataclass[List[T]][str],
                    {"t_dict": {"a": ["a", "b"]}},
                    deserialization_func=dict_deserialization(
                        value_deserialization_func=list_deserialization
                    ),
                ),
            )

        with self.subTest("Fail bound generic incorrect type"):
            with self.assertRaises(DeserializationError):
                dict_to_dataclass(ExampleGenericTypeVarDataclass[str], {"t": 1})

            with self.assertRaises(DeserializationError):
                dict_to_dataclass(
                    ExampleGenericCompoundDataclass[str], {"t_dict": {"a": 1}}
                )
