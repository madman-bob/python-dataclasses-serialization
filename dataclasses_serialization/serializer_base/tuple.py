from functools import partial
from typing import List, Tuple

from toolz import curry
from typing_inspect import get_args

from dataclasses_serialization.serializer_base.errors import DeserializationError
from dataclasses_serialization.serializer_base.noop import noop_deserialization
from dataclasses_serialization.serializer_base.typing import isinstance

__all__ = ["tuple_deserialization"]

get_args = partial(get_args, evaluate=True)


@curry
def tuple_deserialization(type_, obj, deserialization_func=noop_deserialization):
    if not isinstance(obj, (list, tuple)):
        raise DeserializationError(
            "Cannot deserialize {} {!r} using tuple deserialization".format(
                type(obj), obj
            )
        )

    if type_ is tuple or type_ is Tuple:
        return obj

    value_types = get_args(type_)

    if len(value_types) == 1 and value_types[0] == ():  # See PEP-484: Tuple[()] means (empty tuple).
        value_types = ()

    if len(value_types) == 2 and value_types[1] is ...:  # The elipsis object - Tuple[int, ...], see PEP-484
        value_types = (value_types[0], )*len(obj)

    if len(value_types) != len(obj):
        raise DeserializationError(f"You are trying to deserialize a {len(obj)}-tuple: {obj}\n.. but the type signature expects a {len(value_types)}-tuple: {type_}")

    return tuple(deserialization_func(value_type, value) for value, value_type in zip(obj, value_types))
