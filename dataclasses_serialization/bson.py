from datetime import datetime

from dataclasses_serialization.serializer_base import isinstance, noop_serialization, noop_deserialization, dict_serialization, dict_deserialization, list_deserialization, Serializer, DeserializationError

try:
    import bson

    try:
        # Assume py-bson version of bson installed
        bson_loads = bson.loads
        bson_dumps = bson.dumps

    except AttributeError:
        # Fallback to pymongo version of bson
        bson_loads = lambda bson_str: bson.BSON(bson_str).decode()
        bson_dumps = bson.BSON.encode

except ImportError:
    raise ImportError("bson module required for BSON serialization")

__all__ = [
    "BSONSerializer",
    "BSONSerializerMixin",
    "BSONStrSerializer",
    "BSONStrSerializerMixin"
]


def bson_int_deserializer(cls, obj):
    """
    Mongo implicitly converts ints to floats

    Attempt to coerce back
    Fail if coercion lossy
    """

    if isinstance(obj, cls):
        return obj

    try:
        coerced_obj = cls(obj)
    except:
        coerced_obj = None

    if coerced_obj == obj:
        return coerced_obj

    raise DeserializationError("Cannot deserialize {} {!r} to type {}".format(
        type(obj).__name__,
        obj,
        cls.__name__
    ))


BSONSerializer = Serializer(
    serialization_functions={
        dict: lambda dct: dict_serialization(dct, key_serialization_func=BSONSerializer.serialize, value_serialization_func=BSONSerializer.serialize),
        list: lambda lst: list(map(BSONSerializer.serialize, lst)),
        (str, int, float, datetime, bytes, bson.ObjectId, bool, type(None)): noop_serialization
    },
    deserialization_functions={
        dict: lambda cls, dct: dict_deserialization(cls, dct, key_deserialization_func=BSONSerializer.deserialize, value_deserialization_func=BSONSerializer.deserialize),
        list: lambda cls, lst: list_deserialization(cls, lst, deserialization_func=BSONSerializer.deserialize),
        int: bson_int_deserializer,
        bool: noop_deserialization,
        (str, float, datetime, bytes, bson.ObjectId, type(None)): noop_deserialization
    }
)


class BSONSerializerMixin:
    def as_bson(self):
        return BSONSerializer.serialize(self)

    @classmethod
    def from_bson(cls, serialized_obj):
        return BSONSerializer.deserialize(cls, serialized_obj)


BSONStrSerializer = Serializer(
    serialization_functions={
        object: lambda obj: bson_dumps(BSONSerializer.serialize(obj))
    },
    deserialization_functions={
        object: lambda cls, serialized_obj: BSONSerializer.deserialize(cls, bson_loads(serialized_obj))
    }
)


class BSONStrSerializerMixin:
    def as_bson_str(self):
        return BSONStrSerializer.serialize(self)

    @classmethod
    def from_bson_str(cls, serialized_obj):
        return BSONStrSerializer.deserialize(cls, serialized_obj)
