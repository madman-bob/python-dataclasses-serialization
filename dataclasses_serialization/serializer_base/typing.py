from dataclasses import dataclass, fields, is_dataclass
from functools import partial
from typing import TypeVar, get_type_hints

from toolz import curry
from typing_inspect import get_args, get_generic_bases, get_origin

try:
    from typing import GenericMeta
except ImportError:
    from typing import _GenericAlias, _SpecialForm

    GenericMeta = (_GenericAlias, _SpecialForm)

__all__ = [
    "isinstance",
    "issubclass",
    "register_generic_isinstance",
    "register_generic_issubclass",
    "dataclass_field_types",
]

get_args = partial(get_args, evaluate=True)

original_isinstance = isinstance
original_issubclass = issubclass

isinstance_generic_funcs = {}
issubclass_generic_funcs = {}


@curry
def register_generic_isinstance(origin, func):
    isinstance_generic_funcs[origin] = func

    return func


@curry
def register_generic_issubclass(origin, func):
    issubclass_generic_funcs[origin] = func

    return func


def isinstance(o, t):
    if t is dataclass:
        return not original_isinstance(o, type) and is_dataclass(o)

    t_origin = get_origin(t)
    if t_origin in isinstance_generic_funcs:
        return isinstance_generic_funcs[t_origin](o, t)

    return original_isinstance(o, t)


def issubclass(cls, classinfo):
    if classinfo is dataclass:
        return original_isinstance(cls, type) and is_dataclass(cls)

    if cls is dataclass:
        return issubclass(object, classinfo)

    if original_isinstance(classinfo, GenericMeta):
        return (
            original_isinstance(cls, GenericMeta)
            and not get_args(classinfo)
            and get_origin(cls) is classinfo
        )

    if original_isinstance(cls, GenericMeta):
        origin = get_origin(cls)
        bases = get_generic_bases(origin) or (origin,)
        return classinfo in bases

    classinfo_origin = get_origin(classinfo)
    if classinfo_origin in issubclass_generic_funcs:
        return issubclass_generic_funcs[classinfo_origin](cls, classinfo)

    if not original_isinstance(cls, type):
        return False

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
