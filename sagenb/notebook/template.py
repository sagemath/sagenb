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

# TODO get rid of this. Some helper functions may still be used.

import jinja2

import os, re, sys, json

from sagenb.misc.misc import SAGE_VERSION, DATA, unicode_str
from sagenb.notebook.cell import number_of_rows
from flaskext.babel import gettext, ngettext, lazy_gettext

from webassets.ext.jinja2 import AssetsExtension
from webassets import Environment as AssetsEnvironment

if os.environ.has_key('SAGENB_TEMPLATE_PATH'):
    if not os.path.isdir(os.environ['SAGENB_TEMPLATE_PATH']):
        raise ValueError("Enviromental variable SAGENB_TEMPLATE_PATH points to\
                         a non-existant directory")
    TEMPLATE_PATH = os.environ['SAGENB_TEMPLATE_PATH']
else:
    TEMPLATE_PATH = os.path.join(DATA, 'sage')

env = jinja2.Environment(loader=jinja2.FileSystemLoader(TEMPLATE_PATH), extensions=[AssetsExtension])
env.assets_environment = AssetsEnvironment(DATA, '/data')

css_illegal_re = re.compile(r'[^-A-Za-z_0-9]')

def css_escape(string):
    r"""
    Returns a string with all characters not legal in a css name
    replaced with hyphens (-).

    INPUT:

    - ``string`` -- the string to be escaped.

    EXAMPLES::

        sage: from sagenb.notebook.template import css_escape
        sage: css_escape('abcd')
        'abcd'
        sage: css_escape('12abcd')
        '12abcd'
        sage: css_escape(r'\'"abcd\'"')
        '---abcd---'
        sage: css_escape('my-invalid/identifier')
        'my-invalid-identifier'
        sage: css_escape(r'quotes"mustbe!escaped')
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
        return ngettext('%(num)d second', '%(num)d seconds', s)
    if t < 3600:
        m = int(t/60)
        return ngettext('%(num)d minute', '%(num)d minutes', m)
    if t < 3600*24:
        h = int(t/3600)
        return ngettext('%(num)d hour', '%(num)d hours', h)
    d = int(t/(3600*24))
    return ngettext('%(num)d day', '%(num)d days', d)

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
env.filters['number_of_rows'] = number_of_rows
env.filters['clean_name'] = clean_name
env.filters['prettify_time_ago'] = prettify_time_ago
env.filters['max'] = max
env.filters['repr_str'] = lambda x: repr(unicode_str(x))[1:]
env.filters['tojson'] = json.dumps

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
    from sagenb.notebook.notebook import MATHJAX, JEDITABLE_TINYMCE
    from misc import notebook
    #A dictionary containing the default context
    default_context = {'sitename': gettext('Sage Notebook'),
                       'sage_version': SAGE_VERSION,
                       'MATHJAX': MATHJAX,
                       'gettext': gettext,
                       'JEDITABLE_TINYMCE': JEDITABLE_TINYMCE,
                       'conf': notebook.conf() if notebook else None}
    try:
        tmpl = env.get_template(filename)
    except jinja2.exceptions.TemplateNotFound:
        return "Notebook Bug -- missing template %s"%filename

    context = dict(default_context)
    context.update(user_context)
    r = tmpl.render(**context)
    return r
