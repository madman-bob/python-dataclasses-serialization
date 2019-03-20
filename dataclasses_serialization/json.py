import json

from toolz import valmap

from dataclasses_serialization.serializer_base import noop_serialization, noop_deserialization, Serializer

__all__ = [
    "JSONSerializer",
    "JSONSerializerMixin",
    "JSONStrSerializer",
    "JSONStrSerializerMixin"
]

JSONSerializer = Serializer(
    serialization_functions={
        dict: lambda dct: valmap(JSONSerializer.serialize, dct),
        list: lambda lst: list(map(JSONSerializer.serialize, lst)),
        (str, int, float, bool, type(None)): noop_serialization
    },
    deserialization_functions={
        (dict, list, str, int, float, bool, type(None)): noop_deserialization
    }
)


class JSONSerializerMixin:
    def as_json(self):
        return JSONSerializer.serialize(self)

    @classmethod
    def from_json(cls, serialized_obj):
        return JSONSerializer.deserialize(cls, serialized_obj)


JSONStrSerializer = Serializer(
    serialization_functions={
        object: lambda obj: json.dumps(JSONSerializer.serialize(obj))
    },
    deserialization_functions={
        object: lambda cls, serialized_obj: JSONSerializer.deserialize(cls, json.loads(serialized_obj))
    }
)


class JSONStrSerializerMixin:
    def as_json_str(self):
        return JSONStrSerializer.serialize(self)

    @classmethod
    def from_json_str(cls, serialized_obj):
        return JSONStrSerializer.deserialize(cls, serialized_obj)
