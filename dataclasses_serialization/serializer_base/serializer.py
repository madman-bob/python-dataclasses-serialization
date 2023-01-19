from dataclasses import dataclass
from typing import Union, Tuple, Mapping, Callable, TypeVar, Any, Generic, Dict, List

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


DataType = TypeVar("DataType")
SerializedType = TypeVar("SerializedType")
TypeType = Union[type, type(dataclass), type(Any), type(List)]
# TypeType is the type of a type.  Note that type(Any) resolves to typing._SpecialForm, type(List) resolves to typing._GenericAlias
# ... These may change in future versions of python so we leave it as is.
TypeOrTypeTuple = Union[TypeType, Tuple[TypeType, ...]]


@dataclass
class Serializer(Generic[DataType, SerializedType]):
    """
    An object which implements custom serialization / deserialization of a class of objects.
    For many cases, you can just the already-defined JSONStrSerializer.
    Use this class if you want to customize the serialized representation, or handle a data type
    that is not supported in JSONStrSerializer.

    Example (see test_serializer.py for more):

        @dataclass
        class Point:
            x: float
            y: float

        point_to_string = Serializer[Point, str](
            serialization_functions={Point: lambda p: f"{p.x},{p.y}"},
            deserialization_functions={Point: lambda cls, serialized: Point(*(float(s) for s in serialized.split(',')))}
        )
        serialized = point_to_string.serialize(Point(1.5, 2.5))
        assert serialized == '1.5,2.5'
        assert point_to_string.deserialize(Point, serialized) == Point(1.5, 2.5)
    """
    serialization_functions: RefinementDict[TypeOrTypeTuple, Callable[[DataType], SerializedType]]
    deserialization_functions: RefinementDict[TypeOrTypeTuple, Callable[[TypeType, SerializedType], DataType]]

    def __init__(self,
                 serialization_functions: Dict[TypeOrTypeTuple, Callable[[DataType], SerializedType]],
                 deserialization_functions: Dict[TypeOrTypeTuple, Callable[[TypeType, SerializedType], DataType]]
                 ):
        """
        serialization_functions: A dict of serialization functions, indexed by the type-annotation of the field to be serialized
        deserialization_functions: A dict of deserialization functions, indexed by the type-annotation of the field to be deserialized
            The function is called with the type-annotation along with the serialized object
        """
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

    def serialize(self, obj: DataType) -> SerializedType:
        """
        Serialize given Python object
        """

        try:
            serialization_func = self.serialization_functions[obj]
        except KeyError:
            raise SerializationError("Cannot serialize type {}".format(type(obj)))

        return serialization_func(obj)

    @curry
    def deserialize(self, cls: TypeType, serialized_obj: SerializedType) -> DataType:
        """
        Attempt to deserialize serialized object as given type
        """

        try:
            deserialization_func = self.deserialization_functions[cls]
        except KeyError:
            raise DeserializationError("Cannot deserialize type {}".format(cls))

        return deserialization_func(cls, serialized_obj)

    @curry
    def register_serializer(self, cls: TypeOrTypeTuple, func: Callable[[DataType], SerializedType]) -> None:
        self.serialization_functions[cls] = func

    @curry
    def register_deserializer(self, cls: TypeOrTypeTuple, func: Callable[[TypeType, SerializedType], DataType]) -> None:
        self.deserialization_functions[cls] = func

    def register(self,
                 cls: TypeOrTypeTuple,
                 serialization_func: Callable[[DataType], SerializedType],
                 deserialization_func: Callable[[TypeType, SerializedType], DataType]):
        self.register_serializer(cls, serialization_func)
        self.register_deserializer(cls, deserialization_func)
