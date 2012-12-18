from collections import OrderedDict, Mapping

class AST(Mapping):
    def __init__(self, **kwargs):
        self._elements = OrderedDict(**kwargs)

    def add(self, key, value):
        previous = self._elements.get(key, None)
        if previous is None:
            self._elements[key] = value
        elif isinstance(previous, list):
            previous.append(value)
        else:
            self._elements[key] = [previous, value]

    def first(self):
        key = self.elements.keys[0]
        return self.elements[key]

    def __iter__(self):
        return iter(self._elements)

    def __contains__(self, value):
        return value in self._elements

    def __len__(self):
        return len(self._elements)

    def __getitem__(self, key):
        if key not in self._elements:
            self._elements[key] = list()
        return self._elements[key]

    def __getattr__(self, key):
        return self.__getitem__(key)

    @staticmethod
    def pprint(arg, depth=0):
        indent = ' ' * 4 * depth
        indent1 = ' ' * 4 * (depth + 1)
        result = ''
        if isinstance(arg, list):
            result += '\n' + indent + '[\n'
            for e in arg:
                result += AST.pprint(e, depth + 1) + '\n'
            result += indent + ']\n'
            return result
        elif isinstance(arg, AST):
            result += '\n' + indent + '{\n'
            for k in arg.keys():
                result += indent1 + str(k) + ':'
                value = arg[k]
                result += AST.pprint(value, depth + 1) + '\n'
            result += indent + '}'
            return result
        else:
            return str(arg)

    def __repr__(self):
        return self.pprint(self)

