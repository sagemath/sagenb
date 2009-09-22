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
    

@stub
def sage_eval(value, globs):
    # worry about ^ and preparser -- this gets used in interact.py,
    # which is a bit weird, but heh.
    return eval(value, globs)

@stub
def is_package_installed(name):
    pass


@stub
def browser():
    return "open"

@stub
def remote_file(filename, verbose=True):
    pass

@stub
def cython(*args, **kwds):
    pass


def load(filename):
    return cPickle.loads(open(filename).read())

def save(obj, filename):
    s = cPickle.dumps(obj, protocol=2)
    open(filename,'wb').write(s)

@stub
def loads(*args, **kwds):
    pass

@stub
def dumps(*args, **kwds):
    pass

@stub
def alarm(*args, **kwds):
    pass

@stub
def cancel_alarm(*args, **kwds):
    pass


@stub
def verbose(*args, **kwds):
    pass


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

@stub
def sagedoc(*args, **kwds):
    pass

@stub
def cython(*args, **kwds):
    pass

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
    #@stub
    def strip_string_literals(code, state=None):
        # todo -- mini implementation?
        return code

@stub
def version():
    pass

@stub
def Color(*args, **kwds):
    # from sage.plot
    pass

@stub
def is_Matrix(*args, **kwds):
    # from sage.structure.element import is_Matrix
    pass

def register_with_cleaner(pid):
    try:
        import sage.interfaces.cleaner
        sage.interfaces.cleaner.cleaner(pid)  # register pid of forked process with cleaner
    except ImportError:
        print "generic cleaner needs to be written"

@stub
def tmp_filename():
    pass

@stub
def tmp_dir():
    pass

@stub
def InlineFortran(*args):
    pass

@stub
def srange(*args, **kwds):
    pass
