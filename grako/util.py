# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import, unicode_literals

__all__ = ['simplify', 'memoize', 'trim', 'indent']

def simplify(x):
    if isinstance(x, list) and len(x) == 1:
        return simplify(x[0])
    return x

def trim(docstring):
    """
    Definition of the trim algorithm from Python's PEP 257. It is used
    to trim the templates used by the nodes.

    http://www.python.org/dev/peps/pep-0257/
    """
    if not docstring:
        return ''
    # Convert tabs to spaces (following the normal Python rules)
    # and split into a list of lines:
    lines = docstring.expandtabs().splitlines()
    # Determine minimum indentation (first line doesn't count):
    maxindent = len(docstring)  # a reasonable large value
    indent = maxindent
    for line in lines[1:]:
        stripped = line.lstrip()
        if stripped:
            indent = min(indent, len(line) - len(stripped))
    # Remove indentation (first line is special):
    trimmed = [lines[0].strip()]
    if indent < maxindent:
        for line in lines[1:]:
            trimmed.append(line[indent:].rstrip())
    # Strip off trailing and leading blank lines:
#    while trimmed and not trimmed[-1]:
#        trimmed.pop()
    while trimmed and not trimmed[0]:
        trimmed.pop(0)
    # Return a single string:
    return '\n'.join(trimmed)

def indent(text, indent=1):
    """ Indent the given block of text by indent*4 spaces
    """
    if text is None:
        return ''
    text = str(text)
    if indent >= 0:
        lines = [' ' * 4 * indent + t for t in text.split('\n')]
        text = '\n'.join(lines)
    return text
