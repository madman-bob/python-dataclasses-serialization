from dataclasses import dataclass, fields, asdict, is_dataclass
from functools import partial
from typing import TypeVar, Union, Dict, List

from typing_inspect import is_union_type, get_origin, get_args

from toolz import curry

try:
    from typing import GenericMeta
except ImportError:
    from typing import _GenericAlias, _SpecialForm

    GenericMeta = (_GenericAlias, _SpecialForm)

__all__ = [
    "isinstance",
    "issubclass",
    "noop_serialization",
    "noop_deserialization",
    "dict_to_dataclass",
    "union_deserialization",
    "dict_serialization",
    "dict_deserialization",
    "list_deserialization",
    "Serializer",
    "SerializationError",
    "DeserializationError"
]

get_args = partial(get_args, evaluate=True)

original_isinstance = isinstance
original_issubclass = issubclass


def isinstance(o, t):
    if t is dataclass:
        return original_isinstance(o, type) and is_dataclass(o)

    if original_isinstance(t, GenericMeta):
        if t is Dict:
            return original_isinstance(o, dict)

        if get_origin(t) in (dict, Dict):
            key_type, value_type = get_args(t)

            return original_isinstance(o, dict) and all(
                isinstance(key, key_type) and isinstance(value, value_type)
                for key, value in o.items()
            )

    return original_isinstance(o, t)


def issubclass(cls, classinfo):
    if classinfo is dataclass:
        return False

    if classinfo is Union or is_union_type(cls):
        return classinfo is Union and is_union_type(cls)

    if original_isinstance(classinfo, GenericMeta):
        return original_isinstance(cls, GenericMeta) and classinfo.__args__ is None and get_origin(cls) is classinfo

    if original_isinstance(cls, GenericMeta):
        origin = get_origin(cls)
        if isinstance(origin, GenericMeta):
            origin = origin.__base__
        return origin is classinfo

    return original_issubclass(cls, classinfo)


def noop_serialization(obj):
    return obj


@curry
def noop_deserialization(cls, obj):
    if not isinstance(obj, cls):
        raise DeserializationError("Cannot deserialize {} {!r} to type {}".format(
            type(obj),
            obj,
            cls
        ))

    return obj


@curry
def dict_to_dataclass(cls, dct, deserialization_func=noop_deserialization):
    if hasattr(cls, '__parameters__'):
        if cls.__parameters__:
            raise DeserializationError("Cannot deserialize unbound generic {}".format(
                cls
            ))

        origin = get_origin(cls)
        type_mapping = dict(zip(origin.__parameters__, get_args(cls)))

        flds = fields(origin)
        fld_types = (
            fld.type[tuple(type_mapping[type_param] for type_param in fld.type.__parameters__)]
            if isinstance(fld.type, GenericMeta) else
            type_mapping[fld.type]
            if isinstance(fld.type, TypeVar) else
            fld.type
            for fld in flds
        )
    else:
        flds = fields(cls)
        fld_types = (fld.type for fld in flds)

    return cls(**{
        fld.name: deserialization_func(fld_type, dct[fld.name])
        for fld, fld_type in zip(flds, fld_types)
        if fld.name in dct
    })


@curry
def union_deserialization(type_, obj, deserialization_func=noop_deserialization):
    for arg in get_args(type_):
        try:
            return deserialization_func(arg, obj)
        except DeserializationError:
            pass

    raise DeserializationError("Cannot deserialize {} {!r} to type {}".format(
        type(obj),
        obj,
        type_
    ))


@curry
def dict_serialization(obj, key_serialization_func=noop_serialization, value_serialization_func=noop_serialization):
    if not isinstance(obj, dict):
        raise SerializationError("Cannot serialize {} {!r} using dict serialization".format(
            type(obj),
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
            type(obj),
            obj
        ))

    if type_ is dict or type_ is Dict:
        return obj

    key_type, value_type = get_args(type_)

    return {
        key_deserialization_func(key_type, key): value_deserialization_func(value_type, value)
        for key, value in obj.items()
    }


@curry
def list_deserialization(type_, obj, deserialization_func=noop_deserialization):
    if not isinstance(obj, list):
        raise DeserializationError("Cannot deserialize {} {!r} using list deserialization".format(
            type(obj),
            obj
        ))

    if type_ is list or type_ is List:
        return obj

    value_type, = get_args(type_)

    return [
        deserialization_func(value_type, value)
        for value in obj
    ]


@dataclass
class Serializer:
    serialization_functions: dict
    deserialization_functions: dict

    def __post_init__(self):
        self.serialization_functions.setdefault(dataclass, lambda obj: self.serialize(asdict(obj)))

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

        raise SerializationError("Cannot serialize type {}".format(type(obj)))

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

        raise DeserializationError("Cannot deserialize type {}".format(cls))

    @curry
    def register_serializer(self, cls, func):
        self.serialization_functions[cls] = func

    @curry
    def register_deserializer(self, cls, func):
        self.deserialization_functions[cls] = func

    def register(self, cls, serialization_func, deserialization_func):
        self.register_serializer(cls, serialization_func)
        self.register_deserializer(cls, deserialization_func)


class SerializationError(TypeError):
    pass


class DeserializationError(TypeError):
    pass
