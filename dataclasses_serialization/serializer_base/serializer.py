from dataclasses import dataclass
from typing import Union

from toolz import curry

from dataclasses_serialization.serializer_base.dataclasses import dict_to_dataclass
from dataclasses_serialization.serializer_base.dictionary import dict_serialization
from dataclasses_serialization.serializer_base.errors import (
    DeserializationError,
    SerializationError,
)
from dataclasses_serialization.serializer_base.refinement_dict import RefinementDict
from dataclasses_serialization.serializer_base.typing import isinstance, issubclass
from dataclasses_serialization.serializer_base.union import union_deserialization

__all__ = ["Serializer"]


@dataclass
class Serializer:
    serialization_functions: RefinementDict
    deserialization_functions: RefinementDict

    def __init__(self, serialization_functions: dict, deserialization_functions: dict):
        self.serialization_functions = RefinementDict(
            serialization_functions, is_subset=issubclass, is_element=isinstance
        )
        self.deserialization_functions = RefinementDict(
            deserialization_functions, is_subset=issubclass, is_element=issubclass
        )

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

        try:
            serialization_func = self.serialization_functions[obj]
        except KeyError:
            raise SerializationError("Cannot serialize type {}".format(type(obj)))

        return serialization_func(obj)

    @curry
    def deserialize(self, cls, serialized_obj):
        """
        Attempt to deserialize serialized object as given type
        """

        try:
            deserialization_func = self.deserialization_functions[cls]
        except KeyError:
            raise DeserializationError("Cannot deserialize type {}".format(cls))

        return deserialization_func(cls, serialized_obj)

    @curry
    def register_serializer(self, cls, func):
        self.serialization_functions[cls] = func

    @curry
    def register_deserializer(self, cls, func):
        self.deserialization_functions[cls] = func

    def register(self, cls, serialization_func, deserialization_func):
        self.register_serializer(cls, serialization_func)
        self.register_deserializer(cls, deserialization_func)
