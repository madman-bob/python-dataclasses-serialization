from dataclasses import dataclass
from typing import Dict, TypeVar, Union
from unittest import TestCase

from dataclasses_serialization.serializer_base import isinstance, issubclass


class TestTyping(TestCase):
    def test_isinstance(self):
        @dataclass
        class ExampleDataclass:
            int_field: int

        T = TypeVar("T")

        positive_test_cases = [
            (1, int),
            ("Hello, world", str),
            ({"key": "Value"}, dict),
            ({"key": "Value"}, Dict),
            ({"key": "Value"}, Dict[str, str]),
            ({"key": 1}, Dict[str, int]),
            ({1: 2}, Dict[T, T][int]),
            (ExampleDataclass(1), ExampleDataclass),
            (ExampleDataclass(1), dataclass),
        ]

        for obj, type_ in positive_test_cases:
            with self.subTest(obj=obj, type_=type_):
                self.assertTrue(isinstance(obj, type_))

        negative_test_cases = [
            (1, str),
            ("Hello, world", int),
            ({"key": "Value"}, Dict[str, int]),
            ({"key": "Value"}, Dict[int, str]),
            ({"key": 1}, Dict[str, str]),
            ({1: 2}, Dict[T, T][str]),
            (ExampleDataclass, dataclass),
            (ExampleDataclass, ExampleDataclass),
        ]

        for obj, type_ in negative_test_cases:
            with self.subTest(obj=obj, type_=type_):
                self.assertFalse(isinstance(obj, type_))

    def test_issubclass(self):
        @dataclass
        class ExampleDataclass:
            int_field: int

        @dataclass
        class AnotherDataclass(ExampleDataclass):
            str_field: str

        positive_test_cases = [
            (int, object),
            (AnotherDataclass, ExampleDataclass),
            (ExampleDataclass, dataclass),
            (Union[str, int], Union),
        ]

        for cls, supercls in positive_test_cases:
            with self.subTest(cls=cls, supercls=supercls):
                self.assertTrue(issubclass(cls, supercls))

        negative_test_cases = [
            (int, str),
            (int, dataclass),
            (dataclass, ExampleDataclass),
            (Union, Union[str, int]),
        ]

        for cls, supercls in negative_test_cases:
            with self.subTest(cls=cls, supercls=supercls):
                self.assertFalse(issubclass(cls, supercls))
