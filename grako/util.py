import functools

def memoize(func):
    func.cache = {}
    def memoize(*args, **kw):
        if kw: # frozenset is used to ensure hashability
            key = args, frozenset(kw.iteritems())
        else:
            key = args
        cache = func.cache
        if key in cache:
            return cache[key]
        else:
            cache[key] = result = func(*args, **kw)
            return result
    return functools.update_wrapper(memoize, func)

