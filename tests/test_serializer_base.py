from dataclasses import dataclass, asdict
from typing import Generic, TypeVar, Union, Optional, Dict, List
from unittest import TestCase

from dataclasses_serialization.serializer_base import (
    isinstance, issubclass,
    noop_serialization, noop_deserialization,
    dict_to_dataclass, union_deserialization, dict_serialization, dict_deserialization, list_deserialization,
    Serializer,
    SerializationError, DeserializationError
)


class TestSerializerBase(TestCase):
    def test_isinstance(self):
        @dataclass
        class ExampleDataclass:
            int_field: int

        T = TypeVar('T')

        positive_test_cases = [
            (1, int),
            ("Hello, world", str),
            ({'key': "Value"}, dict),
            ({'key': "Value"}, Dict),
            ({'key': "Value"}, Dict[str, str]),
            ({'key': 1}, Dict[str, int]),
            ({1: 2}, Dict[T, T][int]),
            (ExampleDataclass(1), ExampleDataclass),
            (ExampleDataclass, dataclass)
        ]

        for obj, type_ in positive_test_cases:
            with self.subTest(obj=obj, type_=type_):
                self.assertTrue(isinstance(obj, type_))

        negative_test_cases = [
            (1, str),
            ("Hello, world", int),
            ({'key': "Value"}, Dict[str, int]),
            ({'key': "Value"}, Dict[int, str]),
            ({'key': 1}, Dict[str, str]),
            ({1: 2}, Dict[T, T][str]),
            (ExampleDataclass(1), dataclass),
            (ExampleDataclass, ExampleDataclass)
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
            (Union[str, int], Union)
        ]

        for cls, supercls in positive_test_cases:
            with self.subTest(cls=cls, supercls=supercls):
                self.assertTrue(issubclass(cls, supercls))

        negative_test_cases = [
            (int, str),
            (int, dataclass),
            (ExampleDataclass, dataclass),
            (Union, Union[str, int])
        ]

        for cls, supercls in negative_test_cases:
            with self.subTest(cls=cls, supercls=supercls):
                self.assertFalse(issubclass(cls, supercls))

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
            optional_field: str = ""

        with self.subTest("Deserialize basic dict"):
            self.assertEqual(
                ExampleDataclass(1, "Hello, world", "Lorem ipsum"),
                dict_to_dataclass(ExampleDataclass, {'int_field': 1, 'str_field': "Hello, world", 'optional_field': "Lorem ipsum"})
            )

        with self.subTest("Fill in optional field"):
            self.assertEqual(
                ExampleDataclass(1, "Hello, world"),
                dict_to_dataclass(ExampleDataclass, {'int_field': 1, 'str_field': "Hello, world"})
            )

        with self.subTest("Fail missing field deserialization"), self.assertRaises(DeserializationError):
            dict_to_dataclass(ExampleDataclass, {'int_field': 1})

        with self.subTest("Fail non-dict deserialization"), self.assertRaises(DeserializationError):
            dict_to_dataclass(ExampleDataclass, 1)

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

    def test_dict_to_dataclass_generics(self):
        T = TypeVar('T')

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
                dict_to_dataclass(ExampleRedundantGenericDataclass, {'s': "a"})

            with self.assertRaises(DeserializationError):
                dict_to_dataclass(ExampleGenericTypeVarDataclass, {'t': "a"})

            with self.assertRaises(DeserializationError):
                dict_to_dataclass(ExampleGenericCompoundDataclass, {'t_dict': {}})

        with self.subTest("Deserialize bound generics"):
            self.assertEqual(
                ExampleRedundantGenericDataclass("a"),
                dict_to_dataclass(ExampleRedundantGenericDataclass[int], {'s': "a"})
            )

            self.assertEqual(
                ExampleGenericTypeVarDataclass("a"),
                dict_to_dataclass(ExampleGenericTypeVarDataclass[str], {'t': "a"})
            )
            self.assertEqual(
                ExampleGenericTypeVarDataclass(1),
                dict_to_dataclass(ExampleGenericTypeVarDataclass[int], {'t': 1})
            )

            self.assertEqual(
                ExampleGenericCompoundDataclass({'a': "b"}),
                dict_to_dataclass(ExampleGenericCompoundDataclass[str], {'t_dict': {'a': "b"}})
            )
            self.assertEqual(
                ExampleGenericCompoundDataclass({'a': 1}),
                dict_to_dataclass(ExampleGenericCompoundDataclass[int], {'t_dict': {'a': 1}})
            )

        with self.subTest("Deserialize indirectly bound generics"):
            self.assertEqual(
                ExampleGenericTypeVarDataclass(["a", "b"]),
                dict_to_dataclass(ExampleGenericTypeVarDataclass[List[T]][str], {'t': ["a", "b"]}, deserialization_func=list_deserialization)
            )

            self.assertEqual(
                ExampleGenericCompoundDataclass({'a': ["a", "b"]}),
                dict_to_dataclass(ExampleGenericCompoundDataclass[List[T]][str], {'t_dict': {'a': ["a", "b"]}}, deserialization_func=dict_deserialization(value_deserialization_func=list_deserialization))
            )

        with self.subTest("Fail bound generic incorrect type"):
            with self.assertRaises(DeserializationError):
                dict_to_dataclass(ExampleGenericTypeVarDataclass[str], {'t': 1})

            with self.assertRaises(DeserializationError):
                dict_to_dataclass(ExampleGenericCompoundDataclass[str], {'t_dict': {'a': 1}})

    def test_union_deserialization_basic(self):
        with self.subTest("Deserialize union first argument"):
            self.assertEqual(1, union_deserialization(Union[int, str], 1))

        with self.subTest("Deserialize union second argument"):
            self.assertEqual(1, union_deserialization(Union[str, int], 1))

        with self.subTest("Deserialize union many arguments"):
            self.assertEqual(1, union_deserialization(Union[str, list, dict, int, tuple], 1))

        with self.subTest("Deserialize generic union"):
            T = TypeVar('T')

            self.assertEqual(1, union_deserialization(Union[str, T][int], 1))
            self.assertEqual(1, union_deserialization(Union[T, int][str], 1))

        with self.subTest("Invalid union deserialization"), self.assertRaises(DeserializationError):
            union_deserialization(Union[str, list], 1)

    def test_union_deserialization_deserialization_func(self):
        self.assertEqual(1, union_deserialization(Union[int, str], "1", deserialization_func=lambda cls, obj: int(obj)))

    def test_dict_serialization_basic(self):
        self.assertEqual(
            {'key': "Value"},
            dict_serialization({'key': "Value"})
        )

    def test_dict_serialization_serialization_func(self):
        with self.subTest("Serialize dict key serialization function"):
            self.assertEqual(
                {'0': 1},
                dict_serialization({0: 1}, key_serialization_func=str)
            )

        with self.subTest("Serialize dict value serialization function"):
            self.assertEqual(
                {0: "1"},
                dict_serialization({0: 1}, value_serialization_func=str)
            )

    def test_dict_deserialization_basic(self):
        T = TypeVar('T')

        with self.subTest("Deserialize dict noop"):
            self.assertEqual({'key': "Value"}, dict_deserialization(dict, {'key': "Value"}))
            self.assertEqual({'key': "Value"}, dict_deserialization(Dict, {'key': "Value"}))

        with self.subTest("Deserialize dict"):
            self.assertEqual({'key': "Value"}, dict_deserialization(Dict[str, str], {'key': "Value"}))

        with self.subTest("Deserialize generic dict"):
            self.assertEqual({'key': "Value"}, dict_deserialization(Dict[T, T][str], {'key': "Value"}))

        with self.subTest("Fail invalid key deserialization"), self.assertRaises(DeserializationError):
            dict_deserialization(Dict[str, str], {0: "Value"})

        with self.subTest("Fail invalid value deserialization"), self.assertRaises(DeserializationError):
            dict_deserialization(Dict[str, str], {'key': 1})

        with self.subTest("Fail invalid generic deserialization"), self.assertRaises(DeserializationError):
            dict_deserialization(Dict[T, str][int], {0: 1})

    def test_dict_deserialization_deserialization_func(self):
        with self.subTest("Deserialize dict key deserialization function"):
            self.assertEqual(
                {'0': 1},
                dict_deserialization(Dict[str, int], {0: 1}, key_deserialization_func=lambda cls, obj: str(obj))
            )

        with self.subTest("Deserialize dict value deserialization function"):
            self.assertEqual(
                {0: "1"},
                dict_deserialization(Dict[int, str], {0: 1}, value_deserialization_func=lambda cls, obj: str(obj))
            )

    def test_list_deserialization_basic(self):
        T = TypeVar('T')

        with self.subTest("Deserialize list noop"):
            self.assertEqual([1, 2], list_deserialization(list, [1, 2]))
            self.assertEqual([1, 2], list_deserialization(List, [1, 2]))

        with self.subTest("Deserialize list"):
            self.assertEqual([1, 2], list_deserialization(List[int], [1, 2]))

        with self.subTest("Deserialize generic list"):
            self.assertEqual([{'a': 1}, {'b': 2}], list_deserialization(List[Dict[str, T]][int], [{'a': 1}, {'b': 2}]))

        with self.subTest("Fail invalid value deserialization"), self.assertRaises(DeserializationError):
            list_deserialization(List[str], [1, 2])

        with self.subTest("Fail invalid generic deserialization"), self.assertRaises(DeserializationError):
            list_deserialization(List[Dict[str, T]][int], [1, 2])

    def test_list_deserialization_deserialization_func(self):
        self.assertEqual(
            [0, 1],
            list_deserialization(List[int], [1, 2], deserialization_func=lambda cls, obj: obj - 1)
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

    def test_serializer_unpickleable_dataclass(self):
        from _thread import LockType
        from threading import Lock

        locks = [Lock(), Lock()]

        @dataclass
        class UnpickleableDataclass:
            lock: LockType

        dataclass_serializer = Serializer({
            LockType: locks.index,
            dict: lambda obj: dict_serialization(obj, value_serialization_func=dataclass_serializer.serialize)
        }, {
            LockType: lambda cls, lock_index: locks[lock_index]
        })

        with self.subTest("Serialize unpickleable dataclass"):
            self.assertEqual({'lock': 0}, dataclass_serializer.serialize(UnpickleableDataclass(locks[0])))

        with self.subTest("Deserialize unpickleable dataclass"):
            self.assertEqual(UnpickleableDataclass(locks[1]), dataclass_serializer.deserialize(UnpickleableDataclass, {'lock': 1}))

    def test_serializer_union_deserialization_basic(self):
        serializer = Serializer({}, {(str, int): noop_deserialization})

        with self.subTest("Deserialize str as part of union"):
            self.assertEqual("Hello, world", serializer.deserialize(Union[str, int], "Hello, world"))

        with self.subTest("Deserialize int as part of union"):
            self.assertEqual(1, serializer.deserialize(Union[str, int], 1))

        with self.subTest("Fail invalid union deserialization"), self.assertRaises(DeserializationError):
            serializer.deserialize(Union[str, int], None)

        with self.subTest("Non-trivial union deserialization"):
            @dataclass
            class ExampleDataclass:
                int_field: int

            self.assertEqual(
                ExampleDataclass(1),
                serializer.deserialize(Union[str, ExampleDataclass], {'int_field': 1})
            )

    def test_serializer_union_deserialization_custom(self):
        serializer = Serializer({}, {
            (str, int): noop_deserialization,
            Union: lambda cls, obj: (type(obj), obj)
        })

        with self.subTest("Deserialize int"):
            self.assertEqual(1, serializer.deserialize(int, 1))

        with self.subTest("Deserialize custom union"):
            self.assertEqual((int, 1), serializer.deserialize(Union[str, int], 1))

    def test_serializer_optional_deserialization(self):
        serializer = Serializer({}, {
            (int, type(None)): noop_deserialization
        })

        with self.subTest("Deserialize present optional"):
            self.assertEqual(1, serializer.deserialize(Optional[int], 1))

        with self.subTest("Deserialize non-present optional"):
            self.assertEqual(None, serializer.deserialize(Optional[int], None))

        with self.subTest("Fail non-present non-optional deserialization"), self.assertRaises(DeserializationError):
            serializer.deserialize(int, None)

    def test_serializer_serializer_registration(self):
        serializer = Serializer({}, {})

        with self.subTest("Fail serialization before registration"), self.assertRaises(SerializationError):
            serializer.serialize(0)

        serializer.register_serializer(int, noop_serialization)

        with self.subTest("Succeed at serialization after registration"):
            self.assertEqual(0, serializer.serialize(0))

    def test_serializer_deserializer_registration(self):
        serializer = Serializer({}, {})

        with self.subTest("Fail deserialization before registration"), self.assertRaises(DeserializationError):
            serializer.deserialize(int, 0)

        serializer.register_deserializer(int, noop_deserialization)

        with self.subTest("Succeed at deserialization after registration"):
            self.assertEqual(0, serializer.deserialize(int, 0))

    def test_serializer_registration(self):
        serializer = Serializer({}, {})

        with self.subTest("Fail serialization before registration"), self.assertRaises(SerializationError):
            serializer.serialize(0)

        with self.subTest("Fail deserialization before registration"), self.assertRaises(DeserializationError):
            serializer.deserialize(int, "0")

        serializer.register(int, lambda obj: str(obj), lambda cls, obj: cls(obj))

        with self.subTest("Succeed at serialization after registration"):
            self.assertEqual("0", serializer.serialize(0))

        with self.subTest("Succeed at deserialization after registration"):
            self.assertEqual(0, serializer.deserialize(int, "0"))
