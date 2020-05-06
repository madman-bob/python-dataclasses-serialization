from dataclasses import dataclass, is_dataclass
from typing import Union

from toolz import curry

from dataclasses_serialization.serializer_base.dataclasses import dict_to_dataclass
from dataclasses_serialization.serializer_base.dictionary import dict_serialization
from dataclasses_serialization.serializer_base.errors import (
    DeserializationError,
    SerializationError,
)
from dataclasses_serialization.serializer_base.typing import isinstance, issubclass
from dataclasses_serialization.serializer_base.union import union_deserialization

__all__ = ["Serializer"]


@dataclass
class Serializer:
    serialization_functions: dict_serialization
    deserialization_functions: dict_serialization

    def __post_init__(self):
        self.serialization_functions.setdefault(
            dataclass, lambda obj: self.serialize(dict_serialization(obj.__dict__))
        )

        self.deserialization_functions.setdefault(
            dataclass, dict_to_dataclass(deserialization_func=self.deserialize)
        )
        self.deserialization_functions.setdefault(
            Union, union_deserialization(deserialization_func=self.deserialize)
        )

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
