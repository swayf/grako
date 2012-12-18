import functools
from collections import OrderedDict, Mapping

class AST(Mapping):
    def __init__(self):
        self.elements = OrderedDict()

    def __iter__(self):
        return iter(self.elements)

    def __contains__(self, value):
        return value in self.elements

    def __len__(self):
        return len(self.elements)

    def __getitem__(self, key):
        if key not in self.elements:
            self.elements[key] = list()
        return self.elements[key]

    def __getattr__(self, name):
        if name in self:
            return self[name]

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
            result += '\n' + indent + 'ast{\n'
            for k in arg.keys():
                result += indent1 + str(k) + ':'
                value = arg[k]
                result += AST.pprint(value, depth + 1) + '\n'
            result += indent + '}\n'
            return result
        else:
            return indent1 + str(arg)

    def __repr__(self):
        return self.pprint(self)


def memoize(func):
    func.cache = {}
    def memoize(*args, **kw):
        if kw: # frozenset is used to ensure hashability
            key = args, frozenset(kw.iteritems())
        else:
            key = args
        cache = func.cache
        if key in cache:
            result = cache[key]
            if isinstance(result, Exception):
                raise result
            return result
        else:
            try:
                cache[key] = result = func(*args, **kw)
                return result
            except Exception as e:
                cache[key] = e
                raise
    return functools.update_wrapper(memoize, func)

