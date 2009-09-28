"""
Miscellaneous Notebook Functions
"""

#############################################################################
#       Copyright (C) 2006, 2007 William Stein <wstein@gmail.com>
#  Distributed under the terms of the GNU General Public License (GPL)
#  The full text of the GPL is available at:
#                  http://www.gnu.org/licenses/
#############################################################################


def stub(f):
    def g(*args, **kwds):
        print "Stub: ", f.func_name
        return f(*args, **kwds)
    return g


min_password_length = 1

import os, cPickle, socket, sys

def print_open_msg(address, port, secure=False, path=""):
    """
    Print a message on the screen suggesting that the user open their
    web browser to a certain URL.

    INPUT:

    - ``address`` -- a string; a computer address or name
    
    - ``port`` -- an int; a port number
    
    - ``secure`` -- a bool (default: False); whether to prefix the URL
      with 'http' or 'https'
    
    - ``path`` -- a string; the URL's path following the port.
    
    EXAMPLES::

        sage: sage.server.misc.print_open_msg('localhost', 8000, True)
        ****************************************************
        *                                                  *
        * Open your web browser to https://localhost:8000  *
        *                                                  *
        ****************************************************
        sage: sage.server.misc.print_open_msg('sagemath.org', 8000, False)
        ******************************************************
        *                                                    *
        * Open your web browser to http://sagemath.org:8000  *
        *                                                    *
        ******************************************************
        sage: sage.server.misc.print_open_msg('sagemath.org', 90, False)
        ****************************************************
        *                                                  *
        * Open your web browser to http://sagemath.org:90  *
        *                                                  *
        ****************************************************
        sage: sage.server.misc.print_open_msg('sagemath.org', 80, False)
        **************************************************
        *                                                *
        *  Open your web browser to http://sagemath.org  *
        *                                                *
        **************************************************
    """
    if port == 80:
        port = ''
    else:
        port = ':%s'%port
    s = "Open your web browser to http%s://%s%s%s"%('s' if secure else '', address, port, path)
    t = len(s)
    if t%2:
        t += 1
        s += ' '
    n = max(t+4, 50)
    k = n - t  - 1
    j = k/2 
    print '*'*n
    print '*'+ ' '*(n-2) + '*'
    print '*' + ' '*j + s + ' '*j + '*'
    print '*'+ ' '*(n-2) + '*'
    print '*'*n


def find_next_available_port(start, max_tries=100, verbose=False):
    """
    Find the next available port, that is, a port for which a
    current connection attempt returns a 'Connection refused' error
    message.  If no port is found, raise a RuntimError exception.

    INPUT:

    - ``start`` - an int; the starting port number for the scan

    - ``max_tries`` - an int (default: 100); how many ports to scan

    - ``verbose`` - a bool (default: True); whether to print information
      about the scan

    OUTPUT:

    - an int - the port number

    EXAMPLES::

        sage: sage.server.misc.find_next_available_port(9000, verbose=False)   # random output -- depends on network
        9002
    """
    alarm_count = 0  
    for port in range(start, start+max_tries+1):
        try:
            alarm(1)
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(('', port))
        except socket.error, msg:
            if msg[1] == 'Connection refused':
                if verbose: print "Using port = %s"%port
                return port
        except KeyboardInterrupt:
            if verbose: print "alarm"                   
            alarm_count += 1
            if alarm_count >= 10:
                 break
            pass 
        finally:
            cancel_alarm()
        if verbose:
            print "Port %s is already in use."%port
            print "Trying next port..."
    raise RuntimeError, "no available port."


def open_page(address, port, secure, path=""):
    if secure:
        rsrc = 'https'
    else:
        rsrc = 'http'

    os.system('%s %s://%s:%s%s 1>&2 > /dev/null &'%(browser(), rsrc, address, port, path))

def pad_zeros(s, size=3):
    """
    EXAMPLES::
    
        sage: pad_zeros(100)
        '100'
        sage: pad_zeros(10)
        '010'
        sage: pad_zeros(10, 5)
        '00010'
        sage: pad_zeros(389, 5)
        '00389'
        sage: pad_zeros(389, 10)
        '0000000389'
    """    
    return "0"*(size-len(str(s))) + str(s)


DATA = os.path.join(sys.prefix, 'lib', 'python', 'site-packages', 'sagenb', 'data')

if os.environ.has_key('DOT_SAGENB'):
    DOT_SAGENB = os.environ['DOT_SAGENB']
else:
    DOT_SAGENB = os.path.join(os.environ['HOME'], '.sagenb')

print "Using DOT_SAGENB='%s'"%DOT_SAGENB

try:
    from sage.misc.misc import SAGE_URL
except ImportError:
    SAGE_URL = 'http://sagemath.org'

try:
    from sage.misc.misc import SAGE_DOC
except ImportError:
    SAGE_DOC = "stub"
    
try:
    from sage.misc.latex_macros import sage_jsmath_macros
except ImportError:
    sage_jsmath_macros = []

try:
    from sage.misc.session import init as session_init
except ImportError:
    @stub
    def session_init(*args, **kwds):
        pass
    

try:
    from sage.misc.sage_eval import sage_eval
except ImportError:
    def sage_eval(value, globs):
        # worry about ^ and preparser -- this gets used in interact.py,
        # which is a bit weird, but heh.
        return eval(value, globs)

try:
    from sage.misc.all import is_package_installed
except ImportError:
    def is_package_installed(name, *args, **kwds):
        return False


try:
    from sage.misc.viewer import browser
except ImportError:
    @stub
    def browser():
        return "open"

def load(filename):
    return cPickle.loads(open(filename).read())

def save(obj, filename):
    s = cPickle.dumps(obj, protocol=2)
    open(filename,'wb').write(s)

try:
    from sage.structure.sage_object import loads, dumps
except ImportError:
    loads = cPickle.loads
    dumps = cPickle.dumps

try:
    from sage.misc.misc import alarm, cancel_alarm, verbose
except ImportError:
    # TODO!
    @stub
    def alarm(*args, **kwds):
        pass
    @stub
    def cancel_alarm(*args, **kwds):
        pass
    @stub
    def verbose(*args, **kwds):
        pass


################################
# clocks -- easy to implement
################################
import time, resource

def cputime(t=0):
    try:
        t = float(t)
    except TypeError:
        t = 0.0
    u,s = resource.getrusage(resource.RUSAGE_SELF)[:2] 
    return u+s - t

def walltime(t=0):
    return time.time() - t

def word_wrap(s, ncols=85):
    t = []
    if ncols == 0:
        return s
    for x in s.split('\n'):
        if len(x) == 0 or x.lstrip()[:5] == 'sage:':
            t.append(x)
            continue
        while len(x) > ncols:
            k = ncols
            while k > 0 and x[k] != ' ':
                k -= 1
            if k == 0:
                k = ncols
                end = '\\'
            else:
                end = ''
            t.append(x[:k] + end)
            x = x[k:]
            k=0
            while k < len(x) and x[k] == ' ':
                k += 1
            x = x[k:]
        t.append(x)
    return '\n'.join(t)


try:
    from sage.misc.preparser import strip_string_literals
except ImportError:
    def strip_string_literals(code, state=None):
        # todo -- do we need this?
        return code

try:
    from sage.misc.banner import version
except ImportError:
    @stub
    def version():
        return " alpha"

try:
    from sage.plot.all import Color
except ImportError:
    class Color:
        def __init__(self, *args, **kwds):
            pass

########################################
# this is needed for @interact
########################################
def is_Matrix(x):
    try:
        from sage.structure.element import is_Matrix
    except ImportError:
        return False
    return is_Matrix(x)

try:
    from sage.misc.misc import srange
except ImportError:
    # TODO: need to put a really srange here!
    def srange(start, end=None, step=1, universe=None, check=True, include_endpoint=False, endpoint_tolerance=1e-5):
        v = [start]
        while v[-1] <= end:
            v.append(v[-1]+step)
        return v


def register_with_cleaner(pid):
    try:
        import sage.interfaces.cleaner
        sage.interfaces.cleaner.cleaner(pid)  # register pid of forked process with cleaner
    except ImportError:
        print "generic cleaner needs to be written"

try:
    from sage.misc.misc import tmp_filename, tmp_dir
except ImportError:
    def tmp_filename(name='tmp'):
        import tempfile
        return tempfile.mkstemp()[1]

    def tmp_dir(name='dir'):
        import tempfile
        return tempfile.mkdtemp()


try:
    from sage.misc.inline_fortran import InlineFortran
except ImportError:
    @stub
    def InlineFortran(*args, **kwds):
        pass

try:
    from sage.misc.cython import cython
except ImportError:
    @stub
    def cython(*args, **kwds):
        # TODO
        raise NotImplementedError, "Curently %cython mode requires Sage." 


#############################################################
# File permissions
# May need some changes on Windows.
#############################################################
import stat

def set_restrictive_permissions(filename, allow_execute=False):
    print "making restrictive: ", filename
    x = stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR
    if allow_execute:
        x = x | stat.S_IXGRP |  stat.S_IXOTH
    os.chmod(filename, x)
    
def set_permissive_permissions(filename):
    os.chmod(filename, stat.S_IROTH | stat.S_IWOTH | stat.S_IXOTH | \
             stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR | \
             stat.S_IRGRP | stat.S_IWGRP | stat.S_IXGRP)
