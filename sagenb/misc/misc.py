# -*- coding: utf-8 -*-
"""
Miscellaneous Notebook Functions

TESTS:

Check that github issue #195 is fixed::

    sage: from sagenb.misc.misc import mathjax_macros
    sage: type(mathjax_macros)
    <type 'list'>

"""

#############################################################################
#       Copyright (C) 2006, 2007 William Stein <wstein@gmail.com>
#  Distributed under the terms of the GNU General Public License (GPL)
#  The full text of the GPL is available at:
#                  http://www.gnu.org/licenses/
#############################################################################
import sys
from six import text_type, binary_type
from pkg_resources import resource_filename, Requirement, working_set

PYTHON_VERSION = sys.version[0]

if PYTHON_VERSION == '3':
    CRE = ConnectionRefusedError
else:
    CRE = tuple


def stub(f):
    def g(*args, **kwds):
        print("Stub: {}".format(f.func_name))
        return f(*args, **kwds)
    return g


min_password_length = 6

import os
import socket
import sys

try:
    import cPickle as pickle
except ImportError:
    import pickle


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

        sage: from sagenb.misc.misc import print_open_msg
        sage: print_open_msg('localhost', 8080, True)
        ┌──────────────────────────────────────────────────┐
        │                                                  │
        │ Open your web browser to https://localhost:8080  │
        │                                                  │
        └──────────────────────────────────────────────────┘
        sage: print_open_msg('sagemath.org', 8080, False)
        ┌────────────────────────────────────────────────────┐
        │                                                    │
        │ Open your web browser to http://sagemath.org:8080  │
        │                                                    │
        └────────────────────────────────────────────────────┘
        sage: print_open_msg('sagemath.org', 90, False)
        ┌──────────────────────────────────────────────────┐
        │                                                  │
        │ Open your web browser to http://sagemath.org:90  │
        │                                                  │
        └──────────────────────────────────────────────────┘
        sage: print_open_msg('sagemath.org', 80, False)
        ┌────────────────────────────────────────────────┐
        │                                                │
        │  Open your web browser to http://sagemath.org  │
        │                                                │
        └────────────────────────────────────────────────┘
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
    j = k // 2
    msg = '┌' + '─' * (n - 2) + '┐\n'
    msg += '│' + ' ' * (n - 2) + '│\n'
    msg += '│' + ' ' * j + s + ' ' * j + '│\n'
    msg += '│' + ' ' * (n - 2) + '│\n'
    msg += '└' + '─' * (n - 2) + '┘'
    print(msg)


def find_next_available_port(interface, start, max_tries=100, verbose=False):
    """
    Find the next available port at a given interface, that is, a port for
    which a current connection attempt returns a 'Connection refused'
    error message.  If no port is found, raise a RuntimeError exception.

    INPUT:

    - ``interface`` - address to check

    - ``start`` - an int; the starting port number for the scan

    - ``max_tries`` - an int (default: 100); how many ports to scan

    - ``verbose`` - a bool (default: True); whether to print information
      about the scan

    OUTPUT:

    - an int - the port number

    EXAMPLES::

        sage: from sagenb.misc.misc import find_next_available_port
        sage: find_next_available_port('127.0.0.1', 9000, verbose=False)   # random output -- depends on network
        9002
    """
    from signal import alarm

    alarm_count = 0
    for port in range(start, start+max_tries+1):
        try:
            try:
                alarm(5)
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((interface, port))
            finally:
                alarm(0)  # cancel alarm
        except socket.error as msg:
            if ((PYTHON_VERSION == '2' and msg[1] == 'Connection refused')
                    or (PYTHON_VERSION == '3' and isinstance(msg, CRE))):
                if verbose:
                    print("Using port = %s" % port)
                return port
        except KeyboardInterrupt:
            if verbose:
                print("alarm")
            alarm_count += 1
            if alarm_count >= 10:
                 break
        if verbose:
            print("Port %s is already in use." % port)
            print("Trying next port...")
    raise RuntimeError("no available port.")


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

SAGENB_ROOT = os.path.split(resource_filename(__name__, ''))[0]

DATA = os.path.join(SAGENB_ROOT, 'data')

if 'DOT_SAGENB' in os.environ:
    DOT_SAGENB = os.environ['DOT_SAGENB']
elif 'DOT_SAGE' in os.environ:
    DOT_SAGENB = os.environ['DOT_SAGE']
else:
    DOT_SAGENB = os.path.join(os.environ['HOME'], '.sagenb')

SAGE_URL = 'http://sagemath.org'


import sage.all
from sage.misc.latex_macros import sage_mathjax_macros
mathjax_macros = sage_mathjax_macros()
from sage.misc.session import init as session_init
from sage.misc.sage_eval import sage_eval
from sage.misc.viewer import browser
from sage.structure.sage_object import loads, dumps, load, save
from sage.misc.all import verbose
from sage.version import version as SAGE_VERSION
from sage.plot.colors import Color
from sage.structure.element import is_Matrix
from sage.misc.all import tmp_filename, tmp_dir
from sage.misc.inline_fortran import InlineFortran
from sage.misc.cython import cython

def register_with_cleaner(pid):
    import sage.interfaces.cleaner
    sage.interfaces.cleaner.cleaner(pid)  # register pid of forked process with cleaner


################################
# clocks -- easy to implement
################################
import time, resource

def cputime(t=0):
    try:
        t = float(t)
    except TypeError:
        t = 0.0
    u, s = resource.getrusage(resource.RUSAGE_SELF)[:2]
    return u + s - t

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


from sage.repl.preparse import strip_string_literals

try:
    SAGENB_VERSION = working_set.find(Requirement.parse('sagenb')).version
except AttributeError:
    SAGENB_VERSION = ""

#############################################################
# File permissions
# May need some changes on Windows.
#############################################################
import stat

def set_restrictive_permissions(filename, allow_execute=False):
    x = stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR
    if allow_execute:
        x = x | stat.S_IXGRP |  stat.S_IXOTH
    os.chmod(filename, x)

def set_permissive_permissions(filename):
    os.chmod(filename, stat.S_IROTH | stat.S_IWOTH | stat.S_IXOTH | \
             stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR | \
             stat.S_IRGRP | stat.S_IWGRP | stat.S_IXGRP)

def encoded_str(obj, encoding='utf-8'):
    r"""
    Takes an object and returns an encoded str human-readable representation.

    string to bytes

    EXAMPLES::

        sage: from sagenb.misc.misc import encoded_str
        sage: encoded_str(u'\u011b\u0161\u010d\u0159\u017e\xfd\xe1\xed\xe9\u010f\u010e') == 'ěščřžýáíéďĎ'
        True
        sage: encoded_str(u'abc')
        'abc'
        sage: encoded_str(123)
        '123'
    """
    if isinstance(obj, text_type):
        return obj.encode(encoding, 'ignore')
    return binary_type(obj)


def unicode_str(obj, encoding='utf-8'):
    r"""
    Takes an object and returns a unicode human-readable representation.

    (bytes or string) to string

    EXAMPLES::

        sage: from sagenb.misc.misc import unicode_str
        sage: unicode_str('ěščřžýáíéďĎ') == u'\u011b\u0161\u010d\u0159\u017e\xfd\xe1\xed\xe9\u010f\u010e'
        True
        sage: unicode_str('abc')
        u'abc'
        sage: unicode_str(123)
        u'123'
    """
    if isinstance(obj, binary_type):
        return obj.decode(encoding, 'ignore')
    elif isinstance(obj, text_type):
        return obj
    return text_type(obj)


def ignore_nonexistent_files(curdir, dirlist):
    """
    Returns a list of non-existent files, given a directory and its
    contents.  The returned list includes broken symbolic links.  Use
    this, e.g., with :func:`shutil.copytree`, as shown below.

    INPUT:

    - ``curdir`` - a string; the name of the current directory

    - ``dirlist`` - a list of strings; names of ``curdir``'s contents

    OUTPUT:

    - a list of strings; names of ``curdir``'s non-existent files

    EXAMPLES::

        sage: import os, shutil
        sage: from sagenb.misc.misc import ignore_nonexistent_files
        sage: opj = os.path.join; ope = os.path.exists; t = tmp_dir()
        sage: s = opj(t, 'src'); t = opj(t, 'trg'); hi = opj(s, 'hi.txt');
        sage: os.makedirs(s)
        sage: f = open(hi, 'w'); f.write('hi'); f.close()
        sage: os.symlink(hi, opj(s, 'good.txt'))
        sage: os.symlink(opj(s, 'bad'), opj(s, 'bad.txt'))
        sage: slist = sorted(os.listdir(s)); slist
        ['bad.txt', 'good.txt', 'hi.txt']
        sage: [ope(opj(s, x)) for x in slist]
        [False, True, True]
        sage: [os.path.islink(opj(s, x)) for x in slist]
        [True, True, False]
        sage: shutil.copytree(s, t)
        Traceback (most recent call last):
        ...
        Error: [('.../src/bad.txt', '.../trg/bad.txt', "[Errno 2] No such file or directory: '.../src/bad.txt'")]
        sage: shutil.rmtree(t); ope(t)
        False
        sage: shutil.copytree(s, t, ignore = ignore_nonexistent_files)
        sage: tlist = sorted(os.listdir(t)); tlist
        ['good.txt', 'hi.txt']
        sage: [ope(opj(t, x)) for x in tlist]
        [True, True]
        sage: [os.path.islink(opj(t, x)) for x in tlist]  # Note!
        [False, False]
    """
    ignore = []
    for x in dirlist:
        if not os.path.exists(os.path.join(curdir, x)):
            ignore.append(x)
    return ignore


def translations_path():
    return os.path.join(SAGENB_ROOT, 'translations')


def get_languages():
    from babel import Locale
    from babel.core import UnknownLocaleError
    langs = []
    dir_names = [lang for lang in os.listdir(translations_path())
                       if lang != 'en_US']
    for name in dir_names:
        try:
            Locale.parse(name)
        except UnknownLocaleError:
            pass
        else:
            langs.append(name)
    langs.sort()
    langs.insert(0, 'en_US')
    return langs

def N_(message):
    return message
def nN_(message_singular, message_plural):
    return [message_singular, message_plural]
