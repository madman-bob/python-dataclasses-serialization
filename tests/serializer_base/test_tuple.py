from typing import Tuple
from unittest import TestCase

from dataclasses_serialization.serializer_base import DeserializationError
from dataclasses_serialization.serializer_base.tuple import tuple_deserialization


class TestTupleSerialization(TestCase):

    def test_tuple_deserialization(self):

        with self.subTest("Deserialize tuple noop"):
            self.assertEqual((1, 2), tuple_deserialization(tuple, (1, 2)))
            self.assertEqual((1, 2), tuple_deserialization(Tuple, (1, 2)))

        with self.subTest("Deserialize typed tuple"):
            self.assertEqual((1, 2), tuple_deserialization(Tuple[int, int], (1, 2)))
            self.assertEqual((1, 2), tuple_deserialization(Tuple[int, ...], (1, 2)))
            self.assertEqual((1, 2, 3), tuple_deserialization(Tuple[int, ...], (1, 2, 3)))
            self.assertEqual((1, 'abc', True), tuple_deserialization(Tuple[int, str, bool], (1, 'abc', True)))
            self.assertEqual(('aa', 'bb', 'cc'), tuple_deserialization(Tuple[str, str, str], ('aa', 'bb', 'cc')))
            self.assertEqual((), tuple_deserialization(Tuple[()], ()))

        with self.subTest("Catch mismatches"):
            with self.assertRaises(DeserializationError):
                tuple_deserialization(Tuple[int, int, int], (1, 2))
            with self.assertRaises(DeserializationError):
                tuple_deserialization(Tuple[int], (1, 2))
            with self.assertRaises(DeserializationError):
                tuple_deserialization(Tuple[int, int], (1, 'Hi I do not belong here'))
            with self.assertRaises(DeserializationError):
                tuple_deserialization(Tuple[int, ...], (1, 'Hi I do not belong here'))
            with self.assertRaises(DeserializationError):
                tuple_deserialization(Tuple[int, str, str], (1, 'abc', True))
