from .base import Node

class TypeNode(Node):
    def __init__(self, context):
        super(TypeNode, self).__init__(context, None, self.__class__.__name__, [], None, None)

    template = 'Object'


class IntType(TypeNode):
    template = 'long'


class FloatType(TypeNode):
    template = 'double'


class StringType(TypeNode):
    template = 'String'


class BooleanType(TypeNode):
    template = 'boolean'


class ArrayType(TypeNode):
    def __postinit__(self):
        self._dimensions = 1


    @property
    def dimensions(self):
        return self._dimensions

    @dimensions.setter
    def dimensions(self, value):
        self._dimensions = value

    def render_fields(self, fields):
        super(ArrayType, self).render_args(fields)
        fields.update(dimensions='[]' * self.dimensions)
        if not self.type:
            fields.update(type='Object')

    template = '{type}{dimensions}'

