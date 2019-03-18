from dataclasses import dataclass, fields, is_dataclass
from typing import Union, Dict

from toolz import curry

__all__ = [
    "isinstance",
    "issubclass",
    "noop_serialization",
    "noop_deserialization",
    "dict_to_dataclass",
    "union_deserialization",
    "dict_serialization",
    "dict_deserialization",
    "Serializer",
    "SerializationError",
    "DeserializationError"
]

original_isinstance = isinstance
original_issubclass = issubclass


def isinstance(o, t):
    if t is dataclass:
        return original_isinstance(o, type) and is_dataclass(o)

    if original_isinstance(t, type(Dict)):
        if t is Dict:
            return original_isinstance(o, dict)

        if t.__base__ is Dict:
            return original_isinstance(o, dict) and all(
                isinstance(key, t.__args__[0]) and isinstance(value, t.__args__[1])
                for key, value in o.items()
            )

    return original_isinstance(o, t)


def issubclass(cls, classinfo):
    if classinfo is dataclass:
        return False

    if classinfo is Union or original_isinstance(cls, type(Union)):
        return classinfo is Union and original_isinstance(cls, type(Union))

    return original_issubclass(cls, classinfo)


def noop_serialization(obj):
    return obj


@curry
def noop_deserialization(cls, obj):
    if not isinstance(obj, cls):
        raise DeserializationError("Cannot deserialize {} {!r} to type {}".format(
            type(obj).__name__,
            obj,
            cls.__name__
        ))

    return obj


@curry
def dict_to_dataclass(cls, dct, deserialization_func=noop_deserialization):
    return cls(**{
        fld.name: deserialization_func(fld.type, dct[fld.name])
        for fld in fields(cls)
        if fld.name in dct
    })


@curry
def union_deserialization(type_, obj, deserialization_func=noop_deserialization):
    for arg in type_.__args__:
        try:
            return deserialization_func(arg, obj)
        except DeserializationError:
            pass

    raise DeserializationError("Cannot deserialize {} {!r} to type {}".format(
        type(obj).__name__,
        obj,
        type_
    ))


@curry
def dict_serialization(obj, key_serialization_func=noop_serialization, value_serialization_func=noop_serialization):
    if not isinstance(obj, dict):
        raise SerializationError("Cannot serialize {} {!r} using dict serialization".format(
            type(obj).__name__,
            obj
        ))

    return {
        key_serialization_func(key): value_serialization_func(value)
        for key, value in obj.items()
    }


@curry
def dict_deserialization(type_, obj, key_deserialization_func=noop_deserialization, value_deserialization_func=noop_deserialization):
    if not isinstance(obj, dict):
        raise DeserializationError("Cannot deserialize {} {!r} using dict deserialization".format(
            type(obj).__name__,
            obj
        ))

    if type_ is dict or type_ is Dict:
        return obj

    return {
        key_deserialization_func(type_.__args__[0], key): value_deserialization_func(type_.__args__[1], value)
        for key, value in obj.items()
    }


@dataclass
class Serializer:
    serialization_functions: dict
    deserialization_functions: dict

    def __post_init__(self):
        self.deserialization_functions.setdefault(dataclass, dict_to_dataclass(deserialization_func=self.deserialize))
        self.deserialization_functions.setdefault(Union, union_deserialization(deserialization_func=self.deserialize))

    def serialize(self, obj):
        """
        Serialize given Python object
        """

        for type_, func in self.serialization_functions.items():
            if isinstance(obj, type_):
                return func(obj)

        if is_dataclass(obj) and dataclass in self.serialization_functions:
            return self.serialization_functions[dataclass](obj)

        raise SerializationError("Cannot serialize type {}".format(type(obj).__name__))

    @curry
    def deserialize(self, cls, serialized_obj):
        """
        Attempt to deserialize serialized object as given type
        """

        for type_, func in self.deserialization_functions.items():
            if issubclass(cls, type_):
                return func(cls, serialized_obj)

        if is_dataclass(cls) and dataclass in self.deserialization_functions:
            return self.deserialization_functions[dataclass](cls, serialized_obj)

        raise DeserializationError("Cannot deserialize type {}".format(cls.__name__))


class SerializationError(TypeError):
    pass


class DeserializationError(TypeError):
    pass
