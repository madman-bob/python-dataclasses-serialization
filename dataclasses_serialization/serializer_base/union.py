from functools import partial

from toolz import curry
from typing_inspect import get_args

from dataclasses_serialization.serializer_base.errors import DeserializationError
from dataclasses_serialization.serializer_base.noop import noop_deserialization

__all__ = ["union_deserialization"]

get_args = partial(get_args, evaluate=True)


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
