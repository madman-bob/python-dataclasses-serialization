from dataclasses import dataclass, asdict
from datetime import datetime

from toolz import valmap

from dataclasses_serialization.serializer_base import noop_serialization, noop_deserialization, Serializer

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

BSONSerializer = Serializer(
    serialization_functions={
        dataclass: lambda datacls: BSONSerializer.serialize(asdict(datacls)),
        dict: lambda dct: valmap(BSONSerializer.serialize, dct),
        list: lambda lst: list(map(BSONSerializer.serialize, lst)),
        (str, int, float, datetime, bytes, bson.ObjectId, bool, type(None)): noop_serialization
    },
    deserialization_functions={
        (dict, list, str, int, float, datetime, bytes, bson.ObjectId, bool, type(None)): noop_deserialization
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
