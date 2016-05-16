# -*- coding: utf-8 -*
"""nodoctest
Notebook Stylesheets (CSS)
"""


#############################################################################
#       Copyright (C) 2007 William Stein <wstein@gmail.com>
#  Distributed under the terms of the GNU General Public License (GPL)
#  The full text of the GPL is available at:
#                  http://www.gnu.org/licenses/
#############################################################################

import os

from sagenb.misc.misc import DOT_SAGENB
from sagenb.notebook.template import template
from hashlib import sha1

_css_cache = None
def css(color='default'):
    r"""
    Return the CSS header used by the Sage Notebook.
    
    INPUT:
    
    
    -  ``color`` - string or pair of html colors, e.g.,
       'gmail' 'grey' ``('#ff0000', '#0000ff')``
    
    
    EXAMPLES::
    
        sage: import sagenb.notebook.css as c
        sage: type(c.css()[0])
        <type 'str'>
    """
    # TODO: the color argument does nothing right now, since 
    # the main.css file does not use it at all
    global _css_cache
    if _css_cache is None:
        # TODO: Implement a theming system, with a register.
        if color in ('default', 'grey', 'gmail', None):
            color1 = None
            color2 = None
        elif isinstance(color, (tuple,list)):
            color1, color2 = color
        else:
            raise ValueError("unknown color scheme %s" % color)

        main_css = template(os.path.join('css', 'main.css'),
                            color1 = color1, color2 = color2,
                            color_theme = color)

        user_css_path = os.path.join(DOT_SAGENB, 'notebook.css')
        user_css = ''
        if os.path.exists(user_css_path):
            user_css = '\n' + open(user_css_path).read()

        data = main_css + user_css
        _css_cache = (data, sha1(data).hexdigest())
    return _css_cache
