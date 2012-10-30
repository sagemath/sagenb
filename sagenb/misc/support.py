# -*- coding: utf-8 -*
"""
Support for Notebook Introspection and Setup

AUTHORS:

- William Stein (much of this code is from IPython).

- Nick Alexander
"""

import inspect
import os
import base64
import string
import sys
import __builtin__
from cPickle import PicklingError
import pydoc

from misc import loads, dumps, cython, session_init

import sageinspect

try:
    from sage.misc.sagedoc import format_src
except ImportError:
    # Fallback
    def format_src(s, *args, **kwds):
        return s

try:
    from sagenb.misc.sphinxify import sphinxify
except ImportError, msg:
    print msg
    print "Sphinx docstrings not available."
    # Don't do any Sphinxifying if sphinx's dependencies aren't around
    def sphinxify(s):
        return s

######################################################################
# Initialization
######################################################################
EMBEDDED_MODE = False
sage_globals = None
globals_at_init = None
global_names_at_init = None

def init(object_directory=None, globs={}):
    r"""
    Initialize Sage for use with the web notebook interface.
    """
    global sage_globals, globals_at_init, global_names_at_init
    global EMBEDDED_MODE

    os.environ['PAGER'] = 'cat'
    
    sage_globals = globs
    #globals_at_init = set(globs.keys())
    globals_at_init = globs.values()
    global_names_at_init = set(globs.keys())
    EMBEDDED_MODE = True
    
    setup_systems(globs)
    session_init(globs)

    # Ugly cruft.  Initialize the embedded mode of the old Sage
    # notebook, which is going to be included in old copies of Sage
    # forever.
    try:
        import sage.server.support
        sage.server.support.EMBEDDED_MODE = True
    except ImportError:
        pass
    # Also initialize EMBEDDED_MODE in Sage's misc.sageinspect module,
    # which is used to format docstrings in the notebook.
    try:
        import sage.misc.sageinspect
        sage.misc.sageinspect.EMBEDDED_MODE = True
    except ImportError:
        pass


def setup_systems(globs):
    from misc import InlineFortran
    fortran = InlineFortran(globs)
    globs['fortran'] = fortran


######################################################################
# Introspection
######################################################################
def help(obj):
    """
    Display HTML help for ``obj``, a Python object, module, etc.  This
    help is often more extensive than that given by 'obj?'.  This
    function does not return a value --- it prints HTML as a side
    effect.
    
    .. note::

       This a wrapper around the built-in help. If formats the output
       as HTML without word wrap, which looks better in the notebook.

    INPUT:
    
    -  ``obj`` - a Python object, module, etc.
    
    TESTS::
    
        sage: import numpy.linalg
        sage: import os, sage.misc.misc ; current_dir = os.getcwd()
        sage: os.chdir(sage.misc.misc.tmp_dir('server_doctest'))
        sage: sage.server.support.help(numpy.linalg.norm)
        <html><table notracebacks bgcolor="#386074" cellpadding=10 cellspacing=10><tr><td bgcolor="#f5f5f5"><font color="#37546d">
        &nbsp;&nbsp;&nbsp;<a target='_new' href='cell://docs-....html'>Click to open help window</a>&nbsp;&nbsp;&nbsp;
        <br></font></tr></td></table></html>
        sage: os.chdir(current_dir)
    """
    from pydoc import resolve, html, describe
    import sagenb.notebook.interact as interact

    print '<html><table notracebacks bgcolor="#386074" cellpadding=10 cellspacing=10><tr><td bgcolor="#f5f5f5"><font color="#37546d">'
    object, name = resolve(obj)
    page = html.page(describe(object), html.document(object, name))
    page = page.replace('<a href','<a ')
    n = 0
    while True:
        filename = 'docs-%s.html'%n
        if not os.path.exists(filename): break
        n += 1
    open(filename, 'w').write(page)
    print "&nbsp;&nbsp;&nbsp;<a target='_new' href='cell://%s'>Click to open help window</a>&nbsp;&nbsp;&nbsp;"%filename
    print '<br></font></tr></td></table></html>'
    
def get_rightmost_identifier(s):
    X = string.ascii_letters + string.digits + '._'
    i = len(s)-1
    while i >= 0 and s[i] in X:
        i -= 1
    return s[i+1:]
    
def completions(s, globs, format=False, width=90, system="None"):
    """
    Return a list of completions in the given context.

    INPUT:

    - ``globs`` - a string:object dictionary; context in which to
      search for completions, e.g., :func:`globals()`

    - ``format`` - a bool (default: False); whether to tabulate the
      list
    
    - ``width`` - an int; character width of the table
    
    - ``system`` - a string (default: 'None'); system prefix for the
      completions

    OUTPUT:

    - a list of strings, if ``format`` is False, or a string
    """
    if system not in ['sage', 'python']:
        prepend = system + '.'
        s = prepend + s
    else:
        prepend = ''
    n = len(s)
    if n == 0:
        return '(empty string)'
    try:
        if not '.' in s and not '(' in s:
            v = [x for x in globs.keys() if x[:n] == s] + \
                [x for x in __builtins__.keys() if x[:n] == s] 
        else:
            if not ')' in s:
                i = s.rfind('.')
                method = s[i+1:]
                obj = s[:i]
                n = len(method)
            else:
                obj = preparse(s)
                method = ''
            try:
                O = eval(obj, globs)
                D = dir(O)
                try:
                    D += O.trait_names()
                except (AttributeError, TypeError):
                    pass
                if method == '':
                    v = [obj + '.'+x for x in D if x and x[0] != '_']
                else:
                    v = [obj + '.'+x for x in D if x[:n] == method]
            except Exception, msg:
                v = []
        v = list(set(v))   # make unique
        v.sort()
    except Exception, msg:
        v = []

    if prepend:
        i = len(prepend)
        v = [x[i:] for x in v]
        
    if format:
        if len(v) == 0:
            return "No completions of '%s' currently defined"%s
        else:
            return tabulate(v, width)
    return v    

def docstring(obj_name, globs, system='sage'):
    r"""
    Format an object's docstring to process and display in the Sage
    notebook.
    
    INPUT:

    - ``obj_name`` - a string; a name of an object

    - ``globs`` - a string:object dictionary; a context in which to
      evaluate ``obj_name``

    - ``system`` - a string (default: 'sage'); the system to which to
      confine the search

    OUTPUT:

    - a string containing the object's file, type, definition, and
      docstring or a message stating the object is not defined

    AUTHORS:

    - William Stein: partly taken from IPython for use in Sage

    - Nick Alexander: extensions

    TESTS:

    Check that Trac 10860 is fixed and we can handle Unicode help
    strings in the notebook::

        sage: from sagenb.misc.support import docstring
        sage: D = docstring("r.lm", globs=globals())
    """
    if system not in ['sage', 'python']:
        obj_name = system + '.' + obj_name
    try:
        obj = eval(obj_name, globs)
    except (AttributeError, NameError, SyntaxError):
        return "No object '%s' currently defined."%obj_name
    s  = ''
    newline = "\n\n"  # blank line to start new paragraph
    try:
        filename = sageinspect.sage_getfile(obj)
        #i = filename.find('site-packages/sage/')
        #if i == -1:
        s += '**File:** %s'%filename
        s += newline
        #else:
        #    file = filename[i+len('site-packages/sage/'):]
        #    s += 'File:        <html><a href="src_browser?%s">%s</a></html>\n'%(file,file)
    except TypeError:
        pass
    s += '**Type:** %s'%type(obj)
    s += newline
    s += '**Definition:** %s'%sageinspect.sage_getdef(obj, obj_name)
    s += newline
    s += '**Docstring:**'
    s += newline
    s += sageinspect.sage_getdoc(obj, obj_name)
    s = s.rstrip()
    return html_markup(s.decode('utf-8'))

def html_markup(s):
    try:
        from sagenb.misc.sphinxify import sphinxify
        return sphinxify(s)
    except ImportError, msg:
        pass
    # Not in ReST format, so use docutils
    # to process the preamble ("**File:**" etc.)  and put
    # everything else in a <pre> block.
    i = s.find("**Docstring:**")
    if i != -1:
        preamble = s[:i+14]
        from docutils.core import publish_parts
        preamble = publish_parts(s[:i+14], writer_name='html')['body']
        s = s[i+14:]
    else:
        preamble = ""
    return '<div class="docstring">' + preamble + '<pre>' + s + '</pre></div>'

def source_code(s, globs, system='sage'):
    r"""
    Format an object's source code to process and display in the
    Sage notebook.
    
    INPUT:

    - ``s`` - a string; a name of an object

    - ``globs`` - a string:object dictionary; a context in which to
      evaluate ``s``

    - ``system`` - a string (default: 'sage'); the system to which to
      confine the search

    OUTPUT:

    - a string containing the object's file, starting line number, and
      source code

    AUTHORS:

    - William Stein: partly taken from IPython for use in Sage

    - Nick Alexander: extensions
    """
    if system not in ['sage', 'python']:
        s = system + '.' + s

    try:
        obj = eval(s, globs)
    except NameError:
        return html_markup("No object %s"%s)
    
    try:
        try:
            return html_markup(obj._sage_src_())
        except:
            pass
        newline = "\n\n"  # blank line to start new paragraph
        indent = "    "   # indent source code to mark it as a code block

        filename = sageinspect.sage_getfile(obj)
        try:
            lines, lineno = sageinspect.sage_getsourcelines(obj)
        except IOError as msg:
            return html_markup(str(msg))
        src = indent.join(lines)
        src = indent + format_src(src)
        if not lineno is None:
            output = "**File:** %s"%filename
            output += newline
            output += "**Source Code** (starting at line %s)::"%lineno
            output += newline
            output += src
        return html_markup(output)
    
    except (TypeError, IndexError), msg:
        return html_markup("Source code for %s not available."%obj)
    
def tabulate(v, width=90, ncols=3):
    e = len(v)
    if e == 0:
        return ''
    while True:
        col_widths = []
        nrows = e//ncols + 1
        for c in range(ncols):
            m = max([0] + [len(v[r+c*nrows]) for r in range(nrows) if r+c*nrows < e])
            col_widths.append(m+3)
        if ncols > 1 and max(col_widths + [0]) > width//ncols:
            ncols -= 1
        else:
            break
    n = max(len(x) for x in v)
    s = ''
    for r in range(nrows):
        for c in range(ncols):
            i = r + c*nrows
            if i < e:
                w = v[i]
                s += w + ' '*(col_widths[c] - len(w))
        s += '\n'
    return s

def save_session(filename):
    D = {}
    v = variables(with_types=False)
    for k in v:
        x = sage_globals[k]
        try:
            _ = loads(dumps(x))
        except (IOError, TypeError, PicklingError):
            if k != 'fortran':  # this is a hack to get around the inline fortran object being
                                # *incredibly* hackish in how it is implemented; the right
                                # fix is to rewrite the fortran inline to *not* be so incredibly
                                # hackish.  See trac #2891.
                print "Unable to save %s"%k
        else:
            D[k] = x
    print "Saving variables to object %s.sobj"%filename
    save(D, filename)

def load_session(v, filename, state):
    D = {}
    for k, x in v.iteritems():
        try:
            _ = loads(dumps(x))
        except (IOError, TypeError):
            print "Unable to save %s"%k
        else:
            D[k] = x
    print "Saving variables to %s"%filename
    save(D, filename)

def _is_new_var(x, v):
    if x[:2] == '__':
        return False
    if not x in global_names_at_init:
        return True

    # You might think this would take a long time
    # since globals_at_init has several thousand entries.
    # However, it takes 0.0 seconds, which is not noticeable
    # given that there is at least 0.1 seconds delay
    # when refreshing the web page!
    for y in globals_at_init:
        if v is y:
            return False
    return True

def variables(with_types=True):
    if with_types:
        w = ['%s-%s'%(x,type(v)) for x, v in sage_globals.iteritems() if \
             _is_new_var(x, v)]
    else:
        w = [x for x, v in sage_globals.iteritems() if \
             _is_new_var(x, v)]
    w.sort()
    return w



def syseval(system, cmd, dir=None):
    """
    Evaluate an input with a "system" object that can evaluate inputs
    (e.g., python, gap).

    INPUT:
        
    - ``system`` - an object with an eval method that takes an input

    - ``cmd`` - a string input

    - ``sage_globals`` - a string:object dictionary

    - dir - a string (default: None); an optional directory to change
      to before calling :func:`system.eval`

    OUTPUT:

    - :func:`system.eval`'s output
                  
    EXAMPLES::

        sage: from sage.misc.python import python
        sage: sage.server.support.syseval(python, '2+4/3')
        3
        ''
        sage: sage.server.support.syseval(python, 'import os; os.chdir(".")')
        ''
        sage: sage.server.support.syseval(python, 'import os; os.chdir(1,2,3)')
        Traceback (most recent call last):
        ...
        TypeError: chdir() takes exactly 1 argument (3 given)
        sage: sage.server.support.syseval(gap, "2+3")
        '5'
    """
    if dir:
        if hasattr(system.__class__, 'chdir'):
            system.chdir(dir)
    if isinstance(cmd, unicode):
        cmd = cmd.encode('utf-8', 'ignore')
    return system.eval(cmd, sage_globals, locals = sage_globals)

######################################################################
# Cython
######################################################################
def cython_import(filename, verbose=False, compile_message=False,
                 use_cache=False, create_local_c_file=True):
    """
    Compile a file containing Cython code, then import and return the
    module.  Raises an ``ImportError`` if anything goes wrong.

    INPUT:
    
    - ``filename`` - a string; name of a file that contains Cython
      code
    
    OUTPUT:
    
    - the module that contains the compiled Cython code.
    """
    name, build_dir = cython(filename, verbose=verbose,
                             compile_message=compile_message,
                                            use_cache=use_cache,
                                            create_local_c_file=create_local_c_file)
    sys.path.append(build_dir)
    return __builtin__.__import__(name)


def cython_import_all(filename, globals, verbose=False, compile_message=False,
                     use_cache=False, create_local_c_file=True):
    """
    Imports all non-private (i.e., not beginning with an underscore)
    attributes of the specified Cython module into the given context.
    This is similar to::

        from module import *

    Raises an ``ImportError`` exception if anything goes wrong.

    INPUT:
    
    - ``filename`` - a string; name of a file that contains Cython
      code
    """
    m = cython_import(filename, verbose=verbose, compile_message=compile_message,
                     use_cache=use_cache,
                     create_local_c_file=create_local_c_file)
    for k, x in m.__dict__.iteritems():
        if k[0] != '_':
            globals[k] = x
            


###################################################
# Preparser
###################################################
try:
    from sage.misc.preparser import preparse, preparse_file
    def do_preparse():
        """
        Return True if the preparser is set to on, and False otherwise.
        """
        import sage.misc.interpreter
        return sage.misc.interpreter.do_preparse
    
except ImportError:
    def preparse(line, *args, **kwds):
        return line
    def preparse_file(contents, *args, **kwds):
        return contents
    def do_preparse():
        """
        Return True if the preparser is set to on, and False otherwise.
        """
        return False


########################################################################
#
# Automatic Creation of Variable Names
#
# See the docstring for automatic_names below for an explanation of how
# this works. 
#
########################################################################

_automatic_names = False
# We wrap everything in a try/catch, in case this is being imported
# without the sage library present, e.g., in FEMhub.
try:
    from sage.symbolic.all import Expression, SR
    class AutomaticVariable(Expression):
        """
        An automatically created symbolic variable with an additional
        :meth:`__call__` method designed so that doing self(foo,...)
        results in foo.self(...).
        """
        def __call__(self, *args, **kwds):
            """
            Call method such that self(foo, ...) is transformed into
            foo.self(...).  Note that self(foo=...,...) is not
            transformed, it is treated as a normal symbolic
            substitution.
            """
            if len(args) == 0:
                return Expression.__call__(self, **kwds)
            return args[0].__getattribute__(str(self))(*args[1:], **kwds)

    def automatic_name_eval(s, globals, max_names=10000):
        """
        Exec the string ``s`` in the scope of the ``globals``
        dictionary, and if any :exc:`NameError`\ s are raised, try to
        fix them by defining the variable that caused the error to be
        raised, then eval again.  Try up to ``max_names`` times.
        
        INPUT:

           - ``s`` -- a string
           - ``globals`` -- a dictionary
           - ``max_names`` -- a positive integer (default: 10000)
        """
        # This entire automatic naming system really boils down to
        # this bit of code below.  We simply try to exec the string s
        # in the globals namespace, defining undefined variables and
        # functions until everything is defined.
        for _ in range(max_names):
            try:
                exec s in globals
                return
            except NameError, msg:
                # Determine if we hit a NameError that is probably
                # caused by a variable or function not being defined:
                if len(msg.args) == 0: raise  # not NameError with
                                              # specific variable name
                v = msg.args[0].split("'")
                if len(v) < 2: raise  # also not NameError with
                                      # specific variable name We did
                                      # find an undefined variable: we
                                      # simply define it and try
                                      # again.
                nm = v[1]
                globals[nm] = AutomaticVariable(SR, SR.var(nm))
        raise NameError, "Too many automatic variable names and functions created (limit=%s)"%max_names

    def automatic_name_filter(s):
        """
        Wrap the string ``s`` in a call that will cause evaluation of
        ``s`` to automatically create undefined variable names.

        INPUT:

           - ``s`` -- a string

        OUTPUT:

           - a string
        """
        return '_support_.automatic_name_eval(_support_.base64.b64decode("%s"),globals())'%base64.b64encode(s)

    def automatic_names(state=None):
        """
        Turn automatic creation of variables and functional calling of
        methods on or off.  Returns the current ``state`` if no
        argument is given.

        This ONLY works in the Sage notebook.  It is not supported on
        the command line.

        INPUT:

        - ``state`` -- a boolean (default: None); whether to turn
          automatic variable creation and functional calling on or off

        OUTPUT:

        - a boolean, if ``state`` is None; otherwise, None

        EXAMPLES::

            sage: automatic_names(True)      # not tested
            sage: x + y + z                  # not tested
            x + y + z

        Here, ``trig_expand``, ``y``, and ``theta`` are all
        automatically created::
        
            sage: trig_expand((2*x + 4*y + sin(2*theta))^2)   # not tested
            4*(sin(theta)*cos(theta) + x + 2*y)^2
           
        IMPLEMENTATION: Here's how this works, internally.  We define
        an :class:`AutomaticVariable` class derived from
        :class:`~sage.symbolic.all.Expression`.  An instance of
        :class:`AutomaticVariable` is a specific symbolic variable,
        but with a special :meth:`~AutomaticVariable.__call__` method.
        We overload the call method so that ``foo(bar, ...)`` gets
        transformed to ``bar.foo(...)``.  At the same time, we still
        want expressions like ``f^2 - b`` to work, i.e., we don't want
        to have to figure out whether a name appearing in a
        :exc:`NameError` is meant to be a symbolic variable or a
        function name. Instead, we just make an object that is both!

        This entire approach is very simple---we do absolutely no
        parsing of the actual input.  The actual real work amounts to
        only a few lines of code.  The primary catch to this approach
        is that if you evaluate a big block of code in the notebook,
        and the first few lines take a long time, and the next few
        lines define 10 new variables, the slow first few lines will
        be evaluated 10 times.  Of course, the advantage of this
        approach is that even very subtle code that might inject
        surprisingly named variables into the namespace will just work
        correctly, which would be impossible to guarantee with static
        parsing, no matter how sophisticated it is.  Finally, given
        the target audience: people wanting to simplify use of Sage
        for Calculus for undergrads, I think this is an acceptable
        tradeoff, especially given that this implementation is so
        simple.
        """
        global _automatic_names
        if state is None:
            return _automatic_names
        _automatic_names = bool(state)
        
except ImportError:
    pass

from sagenb.misc.format import displayhook_hack

def preparse_worksheet_cell(s, globals):
    """
    Preparse the contents of a worksheet cell in the notebook,
    respecting the user using ``preparser(False)`` to turn off the
    preparser.  This function calls
    :func:`~sage.misc.preparser.preparse_file` which also reloads
    attached files.  It also does displayhook formatting by calling
    the :func:`~sagenb.notebook.interfaces.format.displayhook_hack`
    function.

    INPUT:

    - ``s`` - a string containing code

    - ``globals`` - a string:object dictionary; passed directly to
      :func:`~sage.misc.preparser.preparse_file`

    OUTPUT:

        - a string
    """
    if do_preparse(): 
        s = preparse_file(s, globals=globals)
    s = displayhook_hack(s)
    if _automatic_names:
        s = automatic_name_filter(s)
    return s
