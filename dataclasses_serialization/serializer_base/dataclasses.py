from toolz import curry

from dataclasses_serialization.serializer_base.errors import DeserializationError
from dataclasses_serialization.serializer_base.noop import noop_deserialization
from dataclasses_serialization.serializer_base.typing import (
    dataclass_field_types,
    isinstance,
)

__all__ = ["dict_to_dataclass"]


@curry
def dict_to_dataclass(cls, dct, deserialization_func=noop_deserialization):
    if not isinstance(dct, dict):
        raise DeserializationError(
            "Cannot deserialize {} {!r} using {}".format(
                type(dct), dct, dict_to_dataclass
            )
        )

    try:
        fld_types = dataclass_field_types(cls, require_bound=True)
    except TypeError:
        raise DeserializationError("Cannot deserialize unbound generic {}".format(cls))

    try:
        return cls(
            **{
                fld.name: deserialization_func(fld_type, dct[fld.name])
                for fld, fld_type in fld_types
                if fld.name in dct
            }
        )
    except TypeError:
        raise DeserializationError(
            "Missing one or more required fields to deserialize {!r} as {}".format(
                dct, cls
            )
        )
