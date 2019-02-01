# -*- coding: utf-8 -*
#!/usr/bin/env python
r"""
Process docstrings with Sphinx

Processes docstrings with Sphinx. Can also be used as a commandline script:

``python sphinxify.py <text>``

AUTHORS:

- Tim Joseph Dumol (2009-09-29): initial version
"""
# **************************************************
# Copyright (C) 2009 Tim Dumol <tim@timdumol.com>
#
# Distributed under the terms of the BSD License
# **************************************************

from sage.misc.sphinxify import sphinxify

def is_sphinx_markup(docstring):
    """
    Returns whether a string that contains Sphinx-style ReST markup.

    INPUT:

    - ``docstring`` - string to test for markup

    OUTPUT:

    - boolean
    """
    # this could be made much more clever
    return ("`" in docstring or "::" in docstring)


if __name__ == '__main__':
    import sys
    if len(sys.argv) == 2:
        print(sphinxify(sys.argv[1]))
    else:
        print("""Usage:
%s 'docstring'

docstring -- docstring to be processed
""")
