from dataclasses import dataclass
from datetime import datetime
from os import environ
from typing import Dict
from unittest import TestCase, skipIf

from dataclasses_serialization.serializer_base import DeserializationError

try:
    import bson

    bson_installed = True
except ImportError:
    bson_installed = False

try:
    from dataclasses_serialization.bson import BSONSerializer, BSONSerializerMixin, BSONStrSerializer, BSONStrSerializerMixin
except ImportError:
    BSONSerializer, BSONSerializerMixin, BSONStrSerializer, BSONStrSerializerMixin = [None] * 4

if 'OPTIONAL_MODULES' in environ:
    bson_installed = (
        'bson' in environ['OPTIONAL_MODULES'] or
        'pymongo' in environ['OPTIONAL_MODULES']
    )


@dataclass
class Person:
    name: str


@dataclass
class Song:
    artist: Person


@skipIf(not bson_installed, "BSON not installed")
class TestBSON(TestCase):
    def test_bson_serialization_basic(self):
        obj = Person("Fred")
        serialized_obj = {'name': "Fred"}

        with self.subTest("Serialize dataclass -> BSON"):
            self.assertEqual(serialized_obj, BSONSerializer.serialize(obj))

        with self.subTest("Deserialize BSON -> dataclass"):
            self.assertEqual(obj, BSONSerializer.deserialize(Person, serialized_obj))

    def test_bson_serialization_types(self):
        test_cases = [
            (int, 1, 1),
            (float, 1.0, 1.0),
            (str, "Fred", "Fred"),
            (datetime, datetime(2000, 1, 1), datetime(2000, 1, 1)),
            (bytes, b'Hello, world', b'Hello, world'),
            (bson.ObjectId, bson.ObjectId('0' * 24), bson.ObjectId('0' * 24)),
            (bool, True, True),
            (dict, {'name': "Fred"}, {'name': "Fred"}),
            (Dict, {'name': "Fred"}, {'name': "Fred"}),
            (Dict[str, Person], {'abc123': Person("Fred")}, {'abc123': {'name': "Fred"}}),
            (list, [], []),
            (type(None), None, None)
        ]

        for type_, obj, serialized_obj in test_cases:
            with self.subTest("Serialize object", obj=obj):
                self.assertEqual(serialized_obj, BSONSerializer.serialize(obj))

            with self.subTest("Deserialize object", obj=obj):
                self.assertEqual(obj, BSONSerializer.deserialize(type_, serialized_obj))

    def test_bson_int_coercion(self):
        with self.subTest("Coerce integer float -> int"):
            i = BSONSerializer.deserialize(int, 1.0)

            self.assertIsInstance(i, int)
            self.assertEqual(1, i)

        with self.subTest("Fail to coerce non-integer float -> int"), self.assertRaises(DeserializationError):
            BSONSerializer.deserialize(int, 1.5)

    def test_bson_serialization_nested(self):
        obj = Song(Person("Fred"))
        serialized_obj = {'artist': {'name': "Fred"}}

        with self.subTest("Serialize nested dataclass -> BSON"):
            self.assertEqual(serialized_obj, BSONSerializer.serialize(obj))

        with self.subTest("Deserialize BSON -> nested dataclass"):
            self.assertEqual(obj, BSONSerializer.deserialize(Song, serialized_obj))

    def test_bson_serializer_mixin(self):
        @dataclass
        class Artist(BSONSerializerMixin):
            name: str

        obj = Artist("Fred")
        serialized_obj = {'name': "Fred"}

        with self.subTest("Serialize dataclass -> BSON with as_bson mixin"):
            self.assertEqual(serialized_obj, obj.as_bson())

        with self.subTest("Deserialize BSON -> dataclass with from_bson mixin"):
            self.assertEqual(obj, Artist.from_bson(serialized_obj))

    def test_bson_str_serialization(self):
        obj = Person("Fred")
        serialized_obj = b'\x14\x00\x00\x00\x02name\x00\x05\x00\x00\x00Fred\x00\x00'

        with self.subTest("Serialize dataclass -> BSON string"):
            self.assertEqual(serialized_obj, BSONStrSerializer.serialize(obj))

        with self.subTest("Deserialize BSON string -> dataclass"):
            self.assertEqual(obj, BSONStrSerializer.deserialize(Person, serialized_obj))

    def test_bson_str_serializer_mixin(self):
        @dataclass
        class Artist(BSONStrSerializerMixin):
            name: str

        obj = Artist("Fred")
        serialized_obj = b'\x14\x00\x00\x00\x02name\x00\x05\x00\x00\x00Fred\x00\x00'

        with self.subTest("Serialize dataclass -> BSON string with as_bson_str mixin"):
            self.assertEqual(serialized_obj, obj.as_bson_str())

        with self.subTest("Deserialize BSON string -> dataclass with from_bson_str mixin"):
            self.assertEqual(obj, Artist.from_bson_str(serialized_obj))


@skipIf(bson_installed, "BSON installed")
class TestBSONNotInstalled(TestCase):
    def test_bson_raises_import_error(self):
        with self.assertRaises(ImportError):
            import dataclasses_serialization.bson
