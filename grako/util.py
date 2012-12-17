import functools
from collections import OrderedDict

class AttributeDict(OrderedDict):
    def __missing__(self, name):
        return list()

    def __getattribute__(self, name):
        if name in self:
            return self[name]
        else:
            return object.__getattribute__(self, name)


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

