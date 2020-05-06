__all__ = ["SerializationError", "DeserializationError"]


class SerializationError(TypeError):
    pass


class DeserializationError(TypeError):
    pass
