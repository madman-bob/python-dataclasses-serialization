from dataclasses import dataclass
from typing import Union, Dict, List, Tuple, Optional
from unittest import TestCase

from dataclasses_serialization.json import JSONSerializer, JSONSerializerMixin, JSONStrSerializer, JSONStrSerializerMixin


@dataclass
class Person:
    name: str


@dataclass
class Song:
    artist: Person


class TestJSON(TestCase):
    def test_json_serialization_basic(self):
        obj = Person("Fred")
        serialized_obj = {'name': "Fred"}

        with self.subTest("Serialize dataclass -> JSON"):
            self.assertEqual(serialized_obj, JSONSerializer.serialize(obj))

        with self.subTest("Deserialize JSON -> dataclass"):
            self.assertEqual(obj, JSONSerializer.deserialize(Person, serialized_obj))

    def test_json_serialization_types(self):
        """ Each tuple in test_cases is of the form (type, obj, serialized_obj)"""
        test_cases = [
            (int, 1, 1),
            (float, 1.0, 1.0),
            (str, "Fred", "Fred"),
            (bool, True, True),
            (dict, {'name': "Fred"}, {'name': "Fred"}),
            (Dict, {'name': "Fred"}, {'name': "Fred"}),
            (Dict[str, Person], {'abc123': Person("Fred")}, {'abc123': {'name': "Fred"}}),
            (list, [{'name': "Fred"}], [{'name': "Fred"}]),
            (List, [{'name': "Fred"}], [{'name': "Fred"}]),
            (Tuple[int, bool, Person], (3, True, Person("Lucy")), [3, True, {'name': "Lucy"}]),
            (Tuple[float, ...], (3.5, -2.75, 0.), [3.5, -2.75, 0.]),
            (List[Person], [Person("Fred")], [{'name': "Fred"}]),
            (Union[int, Person], 1, 1),
            (Union[int, Person], Person("Fred"), {'name': "Fred"}),
            (Union[Song, Person], Person("Fred"), {'name': "Fred"}),
            (type(None), None, None),
            (Optional[Tuple[float, float]], None, None),
            (Optional[Tuple[float, float]], (0.5, -0.75), [0.5, -0.75]),
        ]

        for type_, obj, serialized_obj in test_cases:
            with self.subTest("Serialize object", obj=obj):
                self.assertEqual(serialized_obj, JSONSerializer.serialize(obj))

            with self.subTest("Deserialize object", obj=obj):
                self.assertEqual(obj, JSONSerializer.deserialize(type_, serialized_obj))

    def test_json_serialization_nested(self):
        obj = Song(Person("Fred"))
        serialized_obj = {'artist': {'name': "Fred"}}

        with self.subTest("Serialize nested dataclass -> JSON"):
            self.assertEqual(serialized_obj, JSONSerializer.serialize(obj))

        with self.subTest("Deserialize JSON -> nested dataclass"):
            self.assertEqual(obj, JSONSerializer.deserialize(Song, serialized_obj))

    def test_json_serializer_mixin(self):
        @dataclass
        class Artist(JSONSerializerMixin):
            name: str

        obj = Artist("Fred")
        serialized_obj = {'name': "Fred"}

        with self.subTest("Serialize dataclass -> JSON with as_json mixin"):
            self.assertEqual(serialized_obj, obj.as_json())

        with self.subTest("Deserialize JSON -> dataclass with from_json mixin"):
            self.assertEqual(obj, Artist.from_json(serialized_obj))

    def test_json_str_serialization(self):
        obj = Person("Fred")
        serialized_obj = '{"name": "Fred"}'

        with self.subTest("Serialize dataclass -> JSON string"):
            self.assertEqual(serialized_obj, JSONStrSerializer.serialize(obj))

        with self.subTest("Deserialize JSON string -> dataclass"):
            self.assertEqual(obj, JSONStrSerializer.deserialize(Person, serialized_obj))

    def test_json_str_serializer_mixin(self):
        @dataclass
        class Artist(JSONStrSerializerMixin):
            name: str

        obj = Artist("Fred")
        serialized_obj = '{"name": "Fred"}'

        with self.subTest("Serialize dataclass -> JSON string with as_json_str mixin"):
            self.assertEqual(serialized_obj, obj.as_json_str())

        with self.subTest("Deserialize JSON string -> dataclass with from_json_str mixin"):
            self.assertEqual(obj, Artist.from_json_str(serialized_obj))
