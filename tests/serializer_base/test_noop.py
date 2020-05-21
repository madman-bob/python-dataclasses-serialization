from unittest import TestCase

from dataclasses_serialization.serializer_base import (
    DeserializationError,
    noop_deserialization,
    noop_serialization,
)


class TestNoopSerialization(TestCase):
    def test_noop_serialization(self):
        obj = object()
        self.assertEqual(obj, noop_serialization(obj))

    def test_noop_deserialization(self):
        obj = object()

        with self.subTest("Valid noop deserialization"):
            self.assertEqual(obj, noop_deserialization(object, obj))

        with self.subTest("Invalid noop deserialization"), self.assertRaises(
            DeserializationError
        ):
            noop_deserialization(int, obj)
