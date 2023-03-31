from dataclasses import asdict, dataclass
from typing import Optional, Union, List
from unittest import TestCase

from dataclasses_serialization.serializer_base import (
    DeserializationError,
    SerializationError,
    Serializer,
    dict_serialization,
    noop_deserialization,
    noop_serialization,
)


class TestSerializer(TestCase):
    def test_serializer_serialization_basic(self):
        int_serializer = Serializer({(int, str): int}, {})

        with self.subTest("Serialize int -> int"):
            self.assertEqual(1, int_serializer.serialize(1))

        with self.subTest("Serialize str -> int"):
            self.assertEqual(1, int_serializer.serialize("1"))

        with self.subTest("Attempt to serialize object -> int"), self.assertRaises(
            SerializationError
        ):
            int_serializer.serialize(object())

    def test_serializer_deserialization_basic(self):
        int_deserializer = Serializer({}, {int: lambda cls, obj: str(obj)})

        with self.subTest("Deserialize int -> str"):
            self.assertEqual("1", int_deserializer.deserialize(int, 1))

        with self.subTest("Attempt to deserialize object -> str"), self.assertRaises(
            DeserializationError
        ):
            int_deserializer.deserialize(str, object())

    def test_serializer_dataclass_serialization(self):
        @dataclass
        class ExampleDataclass:
            int_field: int

        dataclass_serializer = Serializer(
            {ExampleDataclass: lambda obj: obj.int_field},
            {ExampleDataclass: lambda cls, obj: ExampleDataclass(obj)},
        )

        with self.subTest("Serialize"):
            self.assertEqual(1, dataclass_serializer.serialize(ExampleDataclass(1)))

        with self.subTest("Deserialize"):
            self.assertEqual(
                ExampleDataclass(1),
                dataclass_serializer.deserialize(ExampleDataclass, 1),
            )

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
                dataclass: lambda obj: asdict(obj),
            },
            {
                ExampleDataclass: lambda cls, obj: ExampleDataclass(obj),
                dataclass: lambda cls, obj: cls(**obj),
            },
        )

        with self.subTest("Serialize known dataclass"):
            self.assertEqual(1, dataclass_serializer.serialize(ExampleDataclass(1)))

        with self.subTest("Serialize unknown dataclass"):
            self.assertEqual(
                {"str_field": "Hello, world"},
                dataclass_serializer.serialize(AnotherDataclass("Hello, world")),
            )

        with self.subTest("Deserialize known dataclass"):
            self.assertEqual(
                ExampleDataclass(1),
                dataclass_serializer.deserialize(ExampleDataclass, 1),
            )

        with self.subTest("Deserialize unknown dataclass"):
            self.assertEqual(
                AnotherDataclass("Hello, world"),
                dataclass_serializer.deserialize(
                    AnotherDataclass, {"str_field": "Hello, world"}
                ),
            )

    def test_serializer_unpickleable_dataclass(self):
        from _thread import LockType
        from threading import Lock

        locks = [Lock(), Lock()]

        @dataclass
        class UnpickleableDataclass:
            lock: LockType

        dataclass_serializer = Serializer(
            {
                LockType: locks.index,
                dict: lambda obj: dict_serialization(
                    obj, value_serialization_func=dataclass_serializer.serialize
                ),
            },
            {LockType: lambda cls, lock_index: locks[lock_index]},
        )

        with self.subTest("Serialize unpickleable dataclass"):
            self.assertEqual(
                {"lock": 0},
                dataclass_serializer.serialize(UnpickleableDataclass(locks[0])),
            )

        with self.subTest("Deserialize unpickleable dataclass"):
            self.assertEqual(
                UnpickleableDataclass(locks[1]),
                dataclass_serializer.deserialize(UnpickleableDataclass, {"lock": 1}),
            )

    def test_serializer_union_deserialization_basic(self):
        serializer = Serializer({}, {(str, int): noop_deserialization})

        with self.subTest("Deserialize str as part of union"):
            self.assertEqual(
                "Hello, world", serializer.deserialize(Union[str, int], "Hello, world")
            )

        with self.subTest("Deserialize int as part of union"):
            self.assertEqual(1, serializer.deserialize(Union[str, int], 1))

        with self.subTest("Fail invalid union deserialization"), self.assertRaises(
            DeserializationError
        ):
            serializer.deserialize(Union[str, int], None)

        with self.subTest("Non-trivial union deserialization"):

            @dataclass
            class ExampleDataclass:
                int_field: int

            self.assertEqual(
                ExampleDataclass(1),
                serializer.deserialize(Union[str, ExampleDataclass], {"int_field": 1}),
            )

    def test_serializer_union_deserialization_custom(self):
        serializer = Serializer(
            {},
            {
                (str, int): noop_deserialization,
                Union: lambda cls, obj: (type(obj), obj),
            },
        )

        with self.subTest("Deserialize int"):
            self.assertEqual(1, serializer.deserialize(int, 1))

        with self.subTest("Deserialize custom union"):
            self.assertEqual((int, 1), serializer.deserialize(Union[str, int], 1))

    def test_serializer_optional_deserialization(self):
        serializer = Serializer({}, {(int, type(None)): noop_deserialization})

        with self.subTest("Deserialize present optional"):
            self.assertEqual(1, serializer.deserialize(Optional[int], 1))

        with self.subTest("Deserialize non-present optional"):
            self.assertEqual(None, serializer.deserialize(Optional[int], None))

        with self.subTest(
            "Fail non-present non-optional deserialization"
        ), self.assertRaises(DeserializationError):
            serializer.deserialize(int, None)

    def test_serializer_serializer_registration(self):
        serializer = Serializer({}, {})

        with self.subTest("Fail serialization before registration"), self.assertRaises(
            SerializationError
        ):
            serializer.serialize(0)

        serializer.register_serializer(int, noop_serialization)

        with self.subTest("Succeed at serialization after registration"):
            self.assertEqual(0, serializer.serialize(0))

    def test_serializer_deserializer_registration(self):
        serializer = Serializer({}, {})

        with self.subTest(
            "Fail deserialization before registration"
        ), self.assertRaises(DeserializationError):
            serializer.deserialize(int, 0)

        serializer.register_deserializer(int, noop_deserialization)

        with self.subTest("Succeed at deserialization after registration"):
            self.assertEqual(0, serializer.deserialize(int, 0))

    def test_serializer_registration(self):
        serializer = Serializer({}, {})

        with self.subTest("Fail serialization before registration"), self.assertRaises(
            SerializationError
        ):
            serializer.serialize(0)

        with self.subTest(
            "Fail deserialization before registration"
        ), self.assertRaises(DeserializationError):
            serializer.deserialize(int, "0")

        serializer.register(int, lambda obj: str(obj), lambda cls, obj: cls(obj))

        with self.subTest("Succeed at serialization after registration"):
            self.assertEqual("0", serializer.serialize(0))

        with self.subTest("Succeed at deserialization after registration"):
            self.assertEqual(0, serializer.deserialize(int, "0"))

    def test_simple_custom_serializer(self):

        @dataclass
        class Point:
            x: float
            y: float

        point_to_string = Serializer[Point, str](
            serialization_functions={Point: lambda p: f"{p.x},{p.y}"},
            deserialization_functions={Point: lambda cls, serialized: Point(*(float(s) for s in serialized.split(',')))}
        )
        serialized = point_to_string.serialize(Point(1.5, 2.5))
        assert serialized == '1.5,2.5'
        assert point_to_string.deserialize(Point, serialized) == Point(1.5, 2.5)

    def test_nested_custom_serializer_example(self):

        @dataclass
        class Point:
            x: float
            y: float
            label: str

        def str_to_point(string: str) -> Point:
            x_str, y_str, lab_str = string.split(',')
            return Point(float(x_str), float(y_str), lab_str)

        point_to_csv_serializer = Serializer[List[Point], str](
            serialization_functions={
                Point: lambda p: f"{p.x},{p.y},{p.label}",
                list: lambda l: '\n'.join(point_to_csv_serializer.serialize(item) for item in l)
            },
            deserialization_functions={
                Point: lambda cls, serialized: str_to_point(serialized),
                list: lambda cls, ser: list(point_to_csv_serializer.deserialize(Point, substring) for substring in ser.split('\n'))
            },
        )
        points = [Point(2.5, 3.5, 'point_A'), Point(-1.5, 0.0, 'point_B')]
        ser_point = point_to_csv_serializer.serialize(points)
        assert ser_point == '2.5,3.5,point_A\n-1.5,0.0,point_B'
        recon_points = point_to_csv_serializer.deserialize(List[Point], ser_point)
        print(recon_points)
        assert points == recon_points, f"Point {points} did not equal recon point {recon_points}"
