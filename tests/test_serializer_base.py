from dataclasses import dataclass, asdict
from unittest import TestCase

from dataclasses_serialization.serializer_base import (
    isinstance,
    noop_serialization, noop_deserialization,
    dict_to_dataclass,
    Serializer,
    SerializationError, DeserializationError
)


class TestSerializerBase(TestCase):
    def test_isinstance(self):
        @dataclass
        class ExampleDataclass:
            int_field: int

        positive_test_cases = [
            (1, int),
            ("Hello, world", str),
            (ExampleDataclass(1), ExampleDataclass),
            (ExampleDataclass, dataclass)
        ]

        for obj, type_ in positive_test_cases:
            with self.subTest(obj=obj, type_=type_):
                self.assertTrue(isinstance(obj, type_))

        negative_test_cases = [
            (1, str),
            ("Hello, world", int),
            (ExampleDataclass(1), dataclass),
            (ExampleDataclass, ExampleDataclass)
        ]

        for obj, type_ in negative_test_cases:
            with self.subTest(obj=obj, type_=type_):
                self.assertFalse(isinstance(obj, type_))

    def test_noop_serialization(self):
        obj = object()
        self.assertEqual(obj, noop_serialization(obj))

    def test_noop_deserialization(self):
        obj = object()

        with self.subTest("Valid noop deserialization"):
            self.assertEqual(obj, noop_deserialization(object, obj))

        with self.subTest("Invalid noop deserialization"), self.assertRaises(DeserializationError):
            noop_deserialization(int, obj)

    def test_dict_to_dataclass_basic(self):
        @dataclass
        class ExampleDataclass:
            int_field: int
            str_field: str

        self.assertEqual(
            ExampleDataclass(1, "Hello, world"),
            dict_to_dataclass(ExampleDataclass, {'int_field': 1, 'str_field': "Hello, world"})
        )

    def test_dict_to_dataclass_deserialization_func(self):
        @dataclass
        class ExampleDataclass:
            int_field: int

        with self.subTest("Invalid deserialization"), self.assertRaises(DeserializationError):
            dict_to_dataclass(ExampleDataclass, {'int_field': "1"})

        with self.subTest("Using deserialization func"):
            self.assertEqual(
                ExampleDataclass(1),
                dict_to_dataclass(ExampleDataclass, {'int_field': "1"}, deserialization_func=lambda cls, obj: int(obj))
            )

    def test_serializer_serialization_basic(self):
        int_serializer = Serializer({(int, str): int}, {})

        with self.subTest("Serialize int -> int"):
            self.assertEqual(1, int_serializer.serialize(1))

        with self.subTest("Serialize str -> int"):
            self.assertEqual(1, int_serializer.serialize("1"))

        with self.subTest("Attempt to serialize object -> int"), self.assertRaises(SerializationError):
            int_serializer.serialize(object())

    def test_serializer_deserialization_basic(self):
        int_deserializer = Serializer({}, {int: lambda cls, obj: str(obj)})

        with self.subTest("Deserialize int -> str"):
            self.assertEqual("1", int_deserializer.deserialize(int, 1))

        with self.subTest("Attempt to deserialize object -> str"), self.assertRaises(DeserializationError):
            int_deserializer.deserialize(str, object())

    def test_serializer_dataclass_serialization(self):
        @dataclass
        class ExampleDataclass:
            int_field: int

        dataclass_serializer = Serializer({ExampleDataclass: lambda obj: obj.int_field}, {ExampleDataclass: lambda cls, obj: ExampleDataclass(obj)})

        with self.subTest("Serialize"):
            self.assertEqual(1, dataclass_serializer.serialize(ExampleDataclass(1)))

        with self.subTest("Deserialize"):
            self.assertEqual(ExampleDataclass(1), dataclass_serializer.deserialize(ExampleDataclass, 1))

    def test_serializer_dataclass_fallback_serialization(self):
        @dataclass
        class ExampleDataclass:
            int_field: int

        @dataclass
        class AnotherDataclass:
            str_field: str

        dataclass_serializer = Serializer(
            {
                ExampleDataclass: lambda obj: obj.int_field,
                dataclass: lambda obj: asdict(obj)
            },
            {
                ExampleDataclass: lambda cls, obj: ExampleDataclass(obj),
                dataclass: lambda cls, obj: cls(**obj)
            }
        )

        with self.subTest("Serialize known dataclass"):
            self.assertEqual(1, dataclass_serializer.serialize(ExampleDataclass(1)))

        with self.subTest("Serialize unknown dataclass"):
            self.assertEqual({'str_field': "Hello, world"}, dataclass_serializer.serialize(AnotherDataclass("Hello, world")))

        with self.subTest("Deserialize known dataclass"):
            self.assertEqual(ExampleDataclass(1), dataclass_serializer.deserialize(ExampleDataclass, 1))

        with self.subTest("Deserialize unknown dataclass"):
            self.assertEqual(AnotherDataclass("Hello, world"), dataclass_serializer.deserialize(AnotherDataclass, {'str_field': "Hello, world"}))
