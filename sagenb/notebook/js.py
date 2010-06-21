# -*- coding: utf-8 -*
r"""nodoctest
JavaScript (AJAX) Components of the Notebook

AUTHORS:

- William Stein

- Tom Boothby

- Alex Clemesha

This file contains some minimal code to generate the Javascript code
which is inserted to the head of the notebook web page.  All of the
interesting Javascript code is contained under
``data/sage/js/notebook_lib.js``.
"""
###########################################################################
#       Copyright (C) 2006 William Stein <wstein@gmail.com>
#                     2006 Tom Boothby <boothby@u.washington.edu>
#
#   Released under the *modified* BSD license.
#     Tom wrote in email to me at wstein@gmail.com on March 2, 2008:
#     "You have my permission to change the license on anything I've
#     contributed to the notebook, to whatever suits you."
#
###########################################################################

import os
import keyboards
from template import template
from sagenb.misc.misc import SAGE_URL
from compress.JavaScriptCompressor import JavaScriptCompressor

# Debug mode?  If sagenb lives under SAGE_ROOT/, we minify and cache
# the Notebook JS library.
try:
    from sage.misc.misc import SAGE_ROOT
    from pkg_resources import Requirement, working_set
    sagenb_path = working_set.find(Requirement.parse('sagenb')).location
    debug_mode = SAGE_ROOT not in os.path.realpath(sagenb_path)
except (AttributeError, ImportError):
    debug_mode = False

_cache_javascript = None
def javascript():
    """
    Return javascript library for the Sage Notebook.  This is done by
    reading the template ``notebook_lib.js`` where all of the
    javascript code is contained and replacing a few of the values
    specific to the running session.

    Before the code is returned (as a string), it is run through a
    JavascriptCompressor to minimize the amount of data needed to be
    sent to the browser.

    .. note::

       This the output of this function is cached so that it only
       needs to be generated once.

    EXAMPLES::

        sage: from sagenb.notebook.js import javascript
        sage: s = javascript()
        sage: s[:30]
        '/* JavaScriptCompressor 0.1 [w'

    """
    global _cache_javascript
    if _cache_javascript is not None:
        return _cache_javascript

    s = template(os.path.join('js', 'notebook_lib.js'),
                 SAGE_URL=SAGE_URL,
                 KEY_CODES=keyhandler.all_tests())

    global debug_mode
    if debug_mode:
        return s

    # TODO: use minify here, which is more standard (and usually safer
    # and with gzip compression, smaller); But first inquire about the
    # propriety of the "This software shall be used for Good, not
    # Evil" clause in the license.  Does that prevent us from
    # distributing it (i.e., it adds an extra condition to the
    # software)?  See http://www.crockford.com/javascript/jsmin.py.txt
    s = JavaScriptCompressor().getPacked(s.encode('utf-8'))
    _cache_javascript = s

    return s


class JSKeyHandler:
    """
    This class is used to make javascript functions to check 
    for specific keyevents.
    """

    def __init__(self):
        self.key_codes = {};

    def set(self, name, key='', alt=False, ctrl=False, shift=False):
        """
        Add a named keycode to the handler.  When built by
        ``all_tests()``, it can be called in javascript by
        ``key_<key_name>(event_object)``.  The function returns
        true if the keycode numbered by the ``key`` parameter was
        pressed with the appropriate modifier keys, false otherwise.
        """
        self.key_codes.setdefault(name,[])
        self.key_codes[name] = [JSKeyCode(key, alt, ctrl, shift)]

    def add(self, name, key='', alt=False, ctrl=False, shift=False):
        """
        Similar to ``set_key(...)``, but this instead checks if
        there is an existing keycode by the specified name, and
        associates the specified key combination to that name in
        addition.  This way, if different browsers don't catch one
        keycode, multiple keycodes can be assigned to the same test.
        """
        try:
            self.key_codes[name]
        except KeyError:
            self.key_codes.setdefault(name,[])
        self.key_codes[name].append(JSKeyCode(key,alt,ctrl,shift))

    def all_tests(self):
        """
        Builds all tests currently in the handler.  Returns a string
        of javascript code which defines all functions.
        """
        tests = ''
        for name, keys in self.key_codes.items():
            value = "\n||".join([k.js_test() for k in keys])
            tests += " function key_%s(e) {\n  return %s;\n}"%(name, value)
        return tests

class JSKeyCode:
    def __init__(self, key, alt, ctrl, shift):
        global key_codes
        self.key = key
        self.alt = alt
        self.ctrl = ctrl
        self.shift = shift

    def js_test(self):
        v = 0
        if self.alt:
            v+=1
        if self.ctrl:
            v+=2
        if self.shift:
            v+=4
        t = "((e.m==%s)&&(e.v==%s))"%(self.key,v)
        return t





keyhandler = JSKeyHandler()




