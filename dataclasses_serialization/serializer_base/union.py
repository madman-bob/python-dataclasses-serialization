from functools import partial
from typing import Union

from toolz import curry
from typing_inspect import get_args, is_union_type

from dataclasses_serialization.serializer_base.errors import DeserializationError
from dataclasses_serialization.serializer_base.noop import noop_deserialization
from dataclasses_serialization.serializer_base.typing import register_generic_issubclass

__all__ = ["union_deserialization"]

get_args = partial(get_args, evaluate=True)


@register_generic_issubclass(Union)
def union_issubclass(cls, classinfo):
    return classinfo is Union and is_union_type(cls)


@curry
def union_deserialization(type_, obj, deserialization_func=noop_deserialization):
    for arg in get_args(type_):
        try:
            return deserialization_func(arg, obj)
        except DeserializationError:
            pass

    raise DeserializationError(
        "Cannot deserialize {} {!r} to type {}".format(type(obj), obj, type_)
    )
