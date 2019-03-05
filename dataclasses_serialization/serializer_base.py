from dataclasses import dataclass, fields, is_dataclass

__all__ = [
    "isinstance",
    "noop_serialization",
    "noop_deserialization",
    "dict_to_dataclass",
    "Serializer",
    "SerializationError",
    "DeserializationError"
]

original_isinstance = isinstance


def isinstance(o, t):
    if t is dataclass:
        return original_isinstance(o, type) and is_dataclass(o)

    return original_isinstance(o, t)


def noop_serialization(obj):
    return obj


def noop_deserialization(cls, obj):
    if not isinstance(obj, cls):
        raise DeserializationError("Cannot deserialize {} {!r} to type {}".format(
            type(obj).__name__,
            obj,
            cls.__name__
        ))

    return obj


def dict_to_dataclass(cls, dct, deserialization_func=noop_deserialization):
    return cls(**{
        fld.name: deserialization_func(fld.type, dct[fld.name])
        for fld in fields(cls)
        if fld.name in dct
    })


@dataclass
class Serializer:
    serialization_functions: dict
    deserialization_functions: dict

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

    def deserialize(self, cls, serialized_obj):
        """
        Attempt to deserialize serialized object as given type
        """

        for type_, func in self.deserialization_functions.items():
            if type_ is dataclass:
                continue

            if issubclass(cls, type_):
                return func(cls, serialized_obj)

        if is_dataclass(cls) and dataclass in self.deserialization_functions:
            return self.deserialization_functions[dataclass](cls, serialized_obj)

        raise DeserializationError("Cannot deserialize type {}".format(cls.__name__))


class SerializationError(TypeError):
    pass


class DeserializationError(TypeError):
    pass
