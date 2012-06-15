# -*- coding: utf-8 -*
"""
This is a stand-in for Sage's inspection code in
sage.misc.sageinspect.  If Sage is available, that code will be used
here. Otherwise, use simple-minded replacements based on Python's
inspect module.

AUTHORS:

- John Palmieri, Simon King
"""
def sagenb_getdef(obj, obj_name=''):
    r"""
    Return the definition header for any callable object.

    INPUT:

    - ``obj`` - function
    - ``obj_name`` - string (optional, default '')

    This calls inspect.getargspec, formats the result, and prepends
    ``obj_name``.

    EXAMPLES::

        sage: from sagenb.misc.sageinspect import sagenb_getdef
        sage: def f(a, b=0, *args, **kwds): pass
        sage: sagenb_getdef(f, 'hello')
        'hello(a, b=0, *args, **kwds)'
    """
    from inspect import formatargspec, getargspec
    return obj_name + formatargspec(*getargspec(obj))

def sagenb_getdoc(obj, obj_name=''):
    r"""
    Return the docstring associated to ``obj`` as a string.
    This is essentially a front end for inspect.getdoc.

    INPUT: ``obj``, a function, module, etc.: something with a docstring.
    If "self" is present in the docmentation, then replace it with `obj_name`.

    EXAMPLES::

        sage: from sagenb.misc.sageinspect import sagenb_getdoc
        sage: sagenb_getdoc(sagenb.misc.sageinspect.sagenb_getdoc)[0:55]
        'Return the docstring associated to ``obj`` as a string.'
    """
    from inspect import getdoc
    s = getdoc(obj)
    if obj_name != '':
        i = obj_name.find('.')
        if i != -1:
            obj_name = obj_name[:i]
        s = s.replace('self.','%s.'%obj_name)
    return s

try:
    # If Sage is available, use sage.misc.sageinspect.
    import sage.misc.sageinspect as si
    sage_getargspec = si.sage_getargspec
    sage_getdef = si.sage_getdef
    sage_getdoc = si.sage_getdoc
    sage_getfile = si.sage_getfile
    sage_getsourcelines = si.sage_getsourcelines
except ImportError:
    # If Sage is not available, use Python's inspect module where
    # possible, and slight variants on its functions where needed.
    import inspect
    sage_getargspec = inspect.getargspec
    sage_getfile = inspect.getfile
    sage_getsourcelines = inspect.getsourcelines
    sage_getdef = sagenb_getdef
    sage_getdoc = sagenb_getdoc
