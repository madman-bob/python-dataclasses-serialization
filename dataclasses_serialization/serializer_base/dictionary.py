from functools import partial
from typing import Dict

from toolz import curry
from typing_inspect import get_args

from dataclasses_serialization.serializer_base.errors import (
    DeserializationError,
    SerializationError,
)
from dataclasses_serialization.serializer_base.noop import (
    noop_deserialization,
    noop_serialization,
)
from dataclasses_serialization.serializer_base.typing import isinstance

__all__ = ["dict_serialization", "dict_deserialization"]

get_args = partial(get_args, evaluate=True)


@curry
def dict_serialization(
    obj,
    key_serialization_func=noop_serialization,
    value_serialization_func=noop_serialization,
):
    if not isinstance(obj, dict):
        raise SerializationError(
            "Cannot serialize {} {!r} using dict serialization".format(type(obj), obj)
        )

    return {
        key_serialization_func(key): value_serialization_func(value)
        for key, value in obj.items()
    }


@curry
def dict_deserialization(
    type_,
    obj,
    key_deserialization_func=noop_deserialization,
    value_deserialization_func=noop_deserialization,
):
    if not isinstance(obj, dict):
        raise DeserializationError(
            "Cannot deserialize {} {!r} using dict deserialization".format(
                type(obj), obj
            )
        )

    if type_ is dict or type_ is Dict:
        return obj

    key_type, value_type = get_args(type_)

    return {
        key_deserialization_func(key_type, key): value_deserialization_func(
            value_type, value
        )
        for key, value in obj.items()
    }
