# -*- coding: utf-8 -*-
"""
HTML Templating for the Notebook

AUTHORS:

- Bobby Moretti (2007-07-18): initial version

- Timothy Clemans and Mike Hansen (2008-10-27): major update
"""
#############################################################################
#       Copyright (C) 2007 William Stein <wstein@gmail.com>
#  Distributed under the terms of the GNU General Public License (GPL)
#  The full text of the GPL is available at:
#                  http://www.gnu.org/licenses/
#############################################################################

import jinja

from jinja.filters import stringfilter, simplefilter

import os, re, sys

from sagenb.misc.misc import SAGE_VERSION, DATA
from sagenb.notebook.cell import number_of_rows
from sagenb.notebook.jsmath import math_parse


TEMPLATE_PATH = os.path.join(DATA, 'sage')
env = jinja.Environment(loader=jinja.FileSystemLoader(TEMPLATE_PATH))

css_illegal_re = re.compile(r'[^-A-Za-z_0-9]')

@stringfilter
def css_escape(string):
    r"""
    Returns a string with all characters not legal in a css name
    replaced with hyphens (-).

    INPUT:

    - ``string`` -- the string to be escaped.

    EXAMPLES::

        sage: from sagenb.notebook.template import env, css_escape
        sage: escaper = css_escape()
        sage: print(escaper(env, {}, '12abcd'))
        12abcd
        sage: print(escaper(env, {}, 'abcd'))
        abcd
        sage: print(escaper(env, {}, r'\'"abcd\'"'))
        ---abcd---
        sage: print(escaper(env, {}, 'my-invalid/identifier'))
        my-invalid-identifier
        sage: print(escaper(env, {}, r'quotes"mustbe!escaped'))
        quotes-mustbe-escaped

    The following doctests originally accompanied #7269's support for
    Jinja2.

        sage: from sagenb.notebook.template import css_escape # not tested
        sage: css_escape('abcd')                              # not tested
        'abcd'
        sage: css_escape('12abcd')                            # not tested
        '12abcd'
        sage: css_escape(r'\'"abcd\'"')                       # not tested
        '---abcd---'
        sage: css_escape('my-invalid/identifier')             # not tested
        'my-invalid-identifier'
        sage: css_escape(r'quotes"mustbe!escaped')            # not tested
        'quotes-mustbe-escaped'
    """
    return css_illegal_re.sub('-', string)

def prettify_time_ago(t):
    """
    Converts seconds to a meaningful string.

    INPUT

    - t -- time in seconds

    """
    if t < 60:
        s = int(t)
        if s == 1:
            return "1 second"
        return "%d seconds"%s
    if t < 3600:
        m = int(t/60)
        if m == 1:
            return "1 minute"
        return "%d minutes"%m
    if t < 3600*24:
        h = int(t/3600)
        if h == 1:
            return "1 hour"
        return "%d hours"%h
    d = int(t/(3600*24))
    if d == 1:
        return "1 day"
    return "%d days"%d

def clean_name(name):
    """
    Converts a string to a safe/clean name by converting non-alphanumeric characters to underscores.

    INPUT:

    - name -- a string

    EXAMPLES::

        sage: from sagenb.notebook.template import clean_name
        sage: print clean_name('this!is@bad+string')
        this_is_bad_string
    """
    return ''.join([x if x.isalnum() else '_' for x in name])

env.filters['css_escape'] = css_escape
env.filters['number_of_rows'] = simplefilter(number_of_rows)
env.filters['clean_name'] = stringfilter(clean_name)
env.filters['prettify_time_ago'] = simplefilter(prettify_time_ago)
env.filters['math_parse'] = stringfilter(math_parse)
env.filters['max'] = simplefilter(max)

def template(filename, **user_context):
    """
    Returns HTML, CSS, etc., for a template file rendered in the given
    context.

    INPUT:

    - ``filename`` - a string; the filename of the template relative
      to ``sagenb/data/templates``

    - ``user_context`` - a dictionary; the context in which to evaluate
      the file's template variables

    OUTPUT:
    
    - a string - the rendered HTML, CSS, etc.

    EXAMPLES::

        sage: from sagenb.notebook.template import template
        sage: s = template(os.path.join('html', 'yes_no.html')); type(s)
        <type 'unicode'>
        sage: 'Yes' in s
        True
        sage: u = unicode('Are Gröbner bases awesome?','utf-8')
        sage: s = template(os.path.join('html', 'yes_no.html'), message=u)
        sage: 'Gr\xc3\xb6bner' in s.encode('utf-8')
        True
    """
    from sagenb.notebook.notebook import JSMATH, JEDITABLE_TINYMCE
    from twist import notebook
    #A dictionary containing the default context
    default_context = {'sitename': 'Sage Notebook',
                       'sage_version': SAGE_VERSION,
                       'JSMATH': JSMATH,
                       'JEDITABLE_TINYMCE': JEDITABLE_TINYMCE,
                       'conf': notebook.conf() if notebook else None}
    try:
        tmpl = env.get_template(filename)
    except jinja.exceptions.TemplateNotFound:
        return "Notebook Bug -- missing template %s"%filename
    context = dict(default_context)
    context.update(user_context)
    r = tmpl.render(**context)
    return r
