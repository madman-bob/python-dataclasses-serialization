from dataclasses import dataclass, fields, is_dataclass
from functools import partial
from typing import Dict, TypeVar, Union, get_type_hints

from toolz import curry
from typing_inspect import get_args, get_origin, is_union_type

try:
    from typing import GenericMeta
except ImportError:
    from typing import _GenericAlias, _SpecialForm

    GenericMeta = (_GenericAlias, _SpecialForm)

__all__ = ["isinstance", "issubclass", "dataclass_field_types"]

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
        return (
            original_isinstance(cls, GenericMeta)
            and classinfo.__args__ is None
            and get_origin(cls) is classinfo
        )

    if original_isinstance(cls, GenericMeta):
        origin = get_origin(cls)
        if isinstance(origin, GenericMeta):
            origin = origin.__base__
        return origin is classinfo

    return original_issubclass(cls, classinfo)


@curry
def bind(bindings, generic):
    if isinstance(generic, GenericMeta):
        return generic[
            tuple(bindings[type_param] for type_param in generic.__parameters__)
        ]
    elif isinstance(generic, TypeVar):
        return bindings[generic]
    else:
        return generic


def dataclass_field_types(cls, require_bound=False):
    if not hasattr(cls, "__parameters__"):
        type_hints = get_type_hints(cls)
        flds = fields(cls)

        return ((fld, type_hints[fld.name]) for fld in flds)

    if require_bound and cls.__parameters__:
        raise TypeError("Cannot find types of unbound generic {}".format(cls))

    origin = get_origin(cls)
    type_mapping = dict(zip(origin.__parameters__, get_args(cls)))

    type_hints = get_type_hints(origin)
    flds = fields(origin)

    return ((fld, bind(type_mapping, type_hints[fld.name])) for fld in flds)
