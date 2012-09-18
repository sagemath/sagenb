# -*- coding: utf-8 -*
#!/usr/bin/env python
r"""
Process docstrings with Sphinx

Processes docstrings with Sphinx. Can also be used as a commandline script:

``python sphinxify.py <text>``

AUTHORS:

- Tim Joseph Dumol (2009-09-29): initial version
"""
#**************************************************
# Copyright (C) 2009 Tim Dumol <tim@timdumol.com>
#
# Distributed under the terms of the BSD License
#**************************************************
import os
import re
import shutil
from tempfile import mkdtemp

# We import Sphinx on demand, to reduce Sage startup time.
Sphinx = None

try:
    from sage.misc.misc import SAGE_DOC
except ImportError:
    SAGE_DOC = ''  # used to be None


def sphinxify(docstring, format='html'):
    r"""
    Runs Sphinx on a ``docstring``, and outputs the processed
    documentation.

    INPUT:

    - ``docstring`` -- string -- a ReST-formatted docstring

    - ``format`` -- string (optional, default 'html') -- either 'html' or
      'text'

    OUTPUT:

    - string -- Sphinx-processed documentation, in either HTML or
      plain text format, depending on the value of ``format``

    EXAMPLES::

        sage: from sagenb.misc.sphinxify import sphinxify
        sage: sphinxify('A test')
        '\n<div class="docstring">\n    \n  <p>A test</p>\n\n\n</div>'
        sage: sphinxify('**Testing**\n`monospace`')
        '\n<div class="docstring"...<strong>Testing</strong>\n<span class="math"...</p>\n\n\n</div>'
        sage: sphinxify('`x=y`')
        '\n<div class="docstring">\n    \n  <p><span class="math">\\(x=y\\)</span></p>\n\n\n</div>'
        sage: sphinxify('`x=y`', format='text')
        'x=y\n'
        sage: sphinxify(':math:`x=y`', format='text')
        'x=y\n'
    """
    global Sphinx
    if not Sphinx:
        from sphinx.application import Sphinx

    srcdir = mkdtemp()
    base_name = os.path.join(srcdir, 'docstring')
    rst_name = base_name + '.rst'

    if format == 'html':
        suffix = '.html'
    else:
        suffix = '.txt'
    output_name = base_name + suffix

    filed = open(rst_name, 'w')
    filed.write(docstring)
    filed.close()

    # Sphinx constructor: Sphinx(srcdir, confdir, outdir, doctreedir,
    # buildername, confoverrides, status, warning, freshenv).
    temp_confdir = False
    confdir = os.path.join(SAGE_DOC, 'en', 'introspect')
    if not SAGE_DOC and not os.path.exists(confdir):
        # If we don't have Sage, we need to do our own configuration
        # This may be inefficient or broken.  TODO: Find a faster way to do this.
        temp_confdir = True
        confdir = mkdtemp()
        generate_configuration(confdir)

    doctreedir = os.path.join(srcdir, 'doctrees')
    confoverrides = {'html_context': {}, 'master_doc': 'docstring'}

    sphinx_app = Sphinx(srcdir, confdir, srcdir, doctreedir, format,
                        confoverrides, None, None, True)
    sphinx_app.build(None, [rst_name])

    #We need to remove "_" from __builtin__ that the gettext module installs
    import __builtin__
    __builtin__.__dict__.pop('_', None)

    if os.path.exists(output_name):
        output = open(output_name, 'r').read()
        output = output.replace('<pre>', '<pre class="literal-block">')

        # Translate URLs for media from something like
        #    "../../media/...path.../blah.png"
        # or
        #    "/media/...path.../blah.png"
        # to
        #    "/doc/static/reference/media/...path.../blah.png"
        output = re.sub("""src=['"](/?\.\.)*/?media/([^"']*)['"]""",
                          'src="/doc/static/reference/media/\\2"',
                          output)
        # Remove spurious \(, \), \[, \].
        output = output.replace('\\(', '').replace('\\)', '').replace('\\[', '').replace('\\]', '')
    else:
        print "BUG -- Sphinx error"
        if format == 'html':
            output = '<pre class="introspection">%s</pre>' % docstring
        else:
            output = docstring

    if temp_confdir:
        shutil.rmtree(confdir, ignore_errors=True)
    shutil.rmtree(srcdir, ignore_errors=True)

    return output


def generate_configuration(directory):
    r"""
    Generates a Sphinx configuration in ``directory``.

    INPUT:

    - ``directory`` - string, base directory to use

    EXAMPLES::

        sage: from sagenb.misc.sphinxify import generate_configuration
        sage: import tempfile, os
        sage: tmpdir = tempfile.mkdtemp()
        sage: generate_configuration(tmpdir)
        sage: open(os.path.join(tmpdir, 'conf.py')).read()
        '\n...extensions =...'
    """
    conf = r'''
###########################################################
# Taken from  `$SAGE_ROOT$/devel/sage/doc/common/conf.py` #
###########################################################
import sys, os, re

# If your extensions are in another directory, add it here. If the directory
# is relative to the documentation root, use os.path.abspath to make it
# absolute, like shown here.
#sys.path.append(os.path.abspath('.'))

# General configuration
# ---------------------

# Add any Sphinx extension module names here, as strings. They can be extensions
# coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = ['sage_autodoc',  'sphinx.ext.graphviz',
              'sphinx.ext.inheritance_diagram', 'sphinx.ext.todo']
#, 'sphinx.ext.intersphinx', 'sphinx.ext.extlinks']

# The suffix of source filenames.
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = u""
copyright = u'2005--2011, The Sage Development Team'

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.

#version = '3.1.2'
# The full version, including alpha/beta/rc tags.
#release = '3.1.2'

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#language = None

# There are two options for replacing |today|: either, you set today to some
# non-false value, then it is used:
#today = ''
# Else, today_fmt is used as the format for a strftime call.
#today_fmt = '%B %d, %Y'

# List of documents that shouldn't be included in the build.
#unused_docs = []

# List of directories, relative to source directory, that shouldn't be searched
# for source files.
exclude_trees = ['.build']

# The reST default role (used for this markup: `text`) to use for all documents.
default_role = 'math'

# If true, '()' will be appended to :func: etc. cross-reference text.
#add_function_parentheses = True

# If true, the current module name will be prepended to all description
# unit titles (such as .. function::).
#add_module_names = True

# If true, sectionauthor and moduleauthor directives will be shown in the
# output. They are ignored by default.
#show_authors = False

# The name of the Pygments (syntax highlighting) style to use.  NOTE:
# This overrides a HTML theme's corresponding setting (see below).
pygments_style = 'sphinx'

# GraphViz includes dot, neato, twopi, circo, fdp.
graphviz_dot = 'dot'
inheritance_graph_attrs = { 'rankdir' : 'BT' }
inheritance_node_attrs = { 'height' : 0.5, 'fontsize' : 12, 'shape' : 'oval' }
inheritance_edge_attrs = {}

# Extension configuration
# -----------------------

# include the todos
todo_include_todos = True



# Options for HTML output
# -----------------------

# HTML style sheet NOTE: This overrides a HTML theme's corresponding
# setting.
#html_style = 'default.css'

# The name for this set of Sphinx documents.  If None, it defaults to
# "<project> v<release> documentation".
#html_title = None

# A shorter title for the navigation bar.  Default is the same as html_title.
#html_short_title = None

# The name of an image file (within the static path) to place at the top of
# the sidebar.
#html_logo = 'sagelogo-word.ico'

# The name of an image file (within the static path) to use as favicon of the
# docs.  This file should be a Windows icon file (.ico) being 16x16 or 32x32
# pixels large.
html_favicon = 'favicon.ico'


# If we're using MathJax, we prepend its location to the static path
# array.  We can override / overwrite selected files by putting them
# in the remaining paths.  We also write the local config file,
# containing Sage-specific macros and allowing the use of dollar signs
# to delimit math.  We write the file to the directory
#    sagenb/data/mathjax/config/local/mathjax_sage.js,
# in the sagenb-... subdirectory of
#    SAGE_ROOT/local/lib/python/site-libraries.
# This is in the static path, so the file gets copied to the
# appropriate place, allowing us to use the above setting for
# mathjax_path.

# The environment variable SAGE_DOC_MATHJAX may be set by the user or
# by the file "builder.py".  If it's set, or if SAGE_DOC_JSMATH is set
# (for backwards compatibility), use MathJax.
if (os.environ.get('SAGE_DOC_MATHJAX', False)
    or os.environ.get('SAGE_DOC_JSMATH', False)):

    extensions.append('sphinx.ext.mathjax')
    mathjax_path = 'MathJax.js?config=TeX-AMS_HTML-full,../mathjax_sage.js'

    from sage.misc.latex_macros import sage_mathjax_macros
    html_theme_options['mathjax_macros'] = sage_mathjax_macros

    from pkg_resources import Requirement, working_set
    sagenb_path = working_set.find(Requirement.parse('sagenb')).location
    mathjax_relative = os.path.join('sagenb','data','mathjax')

    # It would be really nice if sphinx would copy the entire mathjax directory, 
    # (so we could have a _static/mathjax directory), rather than the contents of the directory

    mathjax_static = os.path.join(sagenb_path, mathjax_relative)
    html_static_path.append(mathjax_static)
    exclude_patterns=['**/'+os.path.join(mathjax_relative, i) for i in ('docs', 'README*', 'test', 
                                                                        'unpacked', 'LICENSE')]
else:
     extensions.append('sphinx.ext.pngmath')


# If not '', a 'Last updated on:' timestamp is inserted at every page bottom,
# using the given strftime format.
#html_last_updated_fmt = '%b %d, %Y'

# If true, SmartyPants will be used to convert quotes and dashes to
# typographically correct entities.
#html_use_smartypants = True

# Custom sidebar templates, maps document names to template names.
#html_sidebars = {}

# Additional templates that should be rendered to pages, maps page names to
# template names.
#html_additional_pages = {}

# If false, no module index is generated.
#html_use_modindex = True

# If false, no index is generated.
#html_use_index = True

# If true, the reST sources are included in the HTML build as _sources/<name>.
#html_copy_source = True

# If true, an OpenSearch description file will be output, and all pages will
# contain a <link> tag referring to it.  The value of this option must be the
# base URL from which the finished HTML is served.
#html_use_opensearch = ''

# If nonempty, this is the file name suffix for HTML files (e.g. ".xhtml").
#html_file_suffix = ''

# Output file base name for HTML help builder.
#htmlhelp_basename = ''


# Options for LaTeX output
# ------------------------
# See http://sphinx.pocoo.org/config.html#confval-latex_elements
latex_elements = {}

# Extended UTF-8 scheme
latex_elements['inputenc'] = '\\usepackage[utf8x]{inputenc}'

# Prevent Sphinx from by default inserting the following LaTeX
# declaration into the preamble of a .tex file:
#
# \DeclareUnicodeCharacter{00A0}{\nobreakspace}
#
# This happens in the file src/sphinx/writers/latex.py in the sphinx
# spkg.  This declaration is known to result in a failure to build the
# PDF version of a document in the Sage standard documentation. See
# ticket #8183 for further information on this issue.
latex_elements['utf8extra'] = ''

# The paper size ('letterpaper' or 'a4paper').
#latex_elements['papersize'] = 'letterpaper'

# The font size ('10pt', '11pt' or '12pt').
#latex_elements['pointsize'] = '10pt'

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author, document class [howto/manual]).
latex_documents = []

# The name of an image file (relative to this directory) to place at the top of
# the title page.
#latex_logo = 'sagelogo-word.png'

# For "manual" documents, if this is true, then toplevel headings are parts,
# not chapters.
#latex_use_parts = False

# Additional stuff for the LaTeX preamble.
latex_elements['preamble'] = '\usepackage{amsmath}\n\usepackage{amssymb}\n'

# Documents to append as an appendix to all manuals.
#latex_appendices = []

# If false, no module index is generated.
#latex_use_modindex = True

#####################################################
# add LaTeX macros for Sage
try:
    from sage.misc.latex_macros import sage_latex_macros
except ImportError:
    sage_latex_macros = []

try:
    pngmath_latex_preamble  # check whether this is already defined
except NameError:
    pngmath_latex_preamble = ""

for macro in sage_latex_macros:
    # used when building latex and pdf versions
    latex_elements['preamble'] += macro + '\n'
    # used when building html version
    pngmath_latex_preamble += macro + '\n'

#####################################################
def process_docstring_aliases(app, what, name, obj, options, docstringlines):
    """
    Change the docstrings for aliases to point to the original object.
    """
    basename = name.rpartition('.')[2]
    if hasattr(obj, '__name__') and obj.__name__ != basename:
        docstringlines[:] = ['See :obj:`%s`.' % name]

def process_directives(app, what, name, obj, options, docstringlines):
    """
    Remove 'nodetex' and other directives from the first line of any
    docstring where they appear.
    """
    if len(docstringlines) == 0:
        return
    first_line = docstringlines[0]
    directives = [ d.lower() for d in first_line.split(',') ]
    if 'nodetex' in directives:
        docstringlines.pop(0)

def process_docstring_cython(app, what, name, obj, options, docstringlines):
    """
    Remove Cython's filename and location embedding.
    """
    if len(docstringlines) <= 1:
        return

    first_line = docstringlines[0]
    if first_line.startswith('File:') and '(starting at' in first_line:
        #Remove the first two lines
        docstringlines.pop(0)
        docstringlines.pop(0)

def process_docstring_module_title(app, what, name, obj, options, docstringlines):
    """
    Removes the first line from the beginning of the module's docstring.  This
    corresponds to the title of the module's documentation page.
    """
    if what != "module":
        return

    #Remove any additional blank lines at the beginning
    title_removed = False
    while len(docstringlines) > 1 and not title_removed:
        if docstringlines[0].strip() != "":
            title_removed = True
        docstringlines.pop(0)

    #Remove any additional blank lines at the beginning
    while len(docstringlines) > 1:
        if docstringlines[0].strip() == "":
            docstringlines.pop(0)
        else:
            break

skip_picklability_check_modules = [
    #'sage.misc.nested_class_test', # for test only
    'sage.misc.latex',
    'sage.misc.explain_pickle',
    '__builtin__',
]

def check_nested_class_picklability(app, what, name, obj, skip, options):
    """
    Print a warning if pickling is broken for nested classes.
    """
    import types
    if hasattr(obj, '__dict__') and hasattr(obj, '__module__'):
        # Check picklability of nested classes.  Adapted from
        # sage.misc.nested_class.modify_for_nested_pickle.
        module = sys.modules[obj.__module__]
        for (nm, v) in obj.__dict__.iteritems():
            if (isinstance(v, (type, types.ClassType)) and
                v.__name__ == nm and
                v.__module__ == module.__name__ and
                getattr(module, nm, None) is not v and
                v.__module__ not in skip_picklability_check_modules):
                # OK, probably this is an *unpicklable* nested class.
                app.warn('Pickling of nested class %r is probably broken. '
                         'Please set __metaclass__ of the parent class to '
                         'sage.misc.nested_class.NestedClassMetaclass.' % (
                        v.__module__ + '.' + name + '.' + nm))

def skip_member(app, what, name, obj, skip, options):
    """
    To suppress Sphinx warnings / errors, we

    - Don't include [aliases of] builtins.

    - Don't include the docstring for any nested class which has been
      inserted into its module by
      :class:`sage.misc.NestedClassMetaclass` only for pickling.  The
      class will be properly documented inside its surrounding class.

    - Don't include
      sagenb.notebook.twist.userchild_download_worksheets.zip.

    - Optionally, check whether pickling is broken for nested classes.

    - Optionally, include objects whose name begins with an underscore
      ('_'), i.e., "private" or "hidden" attributes, methods, etc.

    Otherwise, we abide by Sphinx's decision.  Note: The object
    ``obj`` is excluded (included) if this handler returns True
    (False).
    """
    if 'SAGE_CHECK_NESTED' in os.environ:
        check_nested_class_picklability(app, what, name, obj, skip, options)

    if getattr(obj, '__module__', None) == '__builtin__':
        return True

    if (hasattr(obj, '__name__') and obj.__name__.find('.') != -1 and
        obj.__name__.split('.')[-1] != name):
        return True

    if name.find("userchild_download_worksheets.zip") != -1:
        return True

    if 'SAGE_DOC_UNDERSCORE' in os.environ:
        if name.split('.')[-1].startswith('_'):
            return False

    return skip

def process_dollars(app, what, name, obj, options, docstringlines):
    r"""
    Replace dollar signs with backticks.
    See sage.misc.sagedoc.process_dollars for more information
    """
    if len(docstringlines) > 0 and name.find("process_dollars") == -1:
        from sage.misc.sagedoc import process_dollars as sagedoc_dollars
        s = sagedoc_dollars("\n".join(docstringlines))
        lines = s.split("\n")
        for i in range(len(lines)):
            docstringlines[i] = lines[i]

def process_inherited(app, what, name, obj, options, docstringlines):
    """
    If we're including inherited members, omit their docstrings.
    """
    if not options.get('inherited-members'):
        return

    if what in ['class', 'data', 'exception', 'function', 'module']:
        return

    name = name.split('.')[-1]

    if what == 'method' and hasattr(obj, 'im_class'):
        if name in obj.im_class.__dict__.keys():
            return

    if what == 'attribute' and hasattr(obj, '__objclass__'):
        if name in obj.__objclass__.__dict__.keys():
            return

    for i in xrange(len(docstringlines)):
        docstringlines.pop()

from sage.misc.sageinspect import sage_getargspec
autodoc_builtin_argspec = sage_getargspec

def setup(app):
    app.connect('autodoc-process-docstring', process_docstring_cython)
    app.connect('autodoc-process-docstring', process_directives)
    app.connect('autodoc-process-docstring', process_docstring_module_title)
    app.connect('autodoc-process-docstring', process_dollars)
    app.connect('autodoc-process-docstring', process_inherited)
    app.connect('autodoc-skip-member', skip_member)
    '''


    # From SAGE_DOC/en/introspect/templates/layout.html:
    layout = r"""
<div class="docstring">
    {% block body %}{% endblock %}
</div>
"""
    os.makedirs(os.path.join(directory, 'templates'))
    os.makedirs(os.path.join(directory, 'static'))
    open(os.path.join(directory, 'conf.py'), 'w').write(conf)
    open(os.path.join(directory, '__init__.py'), 'w').write('')
    open(os.path.join(directory, 'templates', 'layout.html'),
         'w').write(layout)
    open(os.path.join(directory, 'static', 'empty'), 'w').write('')

if __name__ == '__main__':
    import sys
    if len(sys.argv) == 2:
        print sphinxify(sys.argv[1])
    else:
        print """Usage:
%s 'docstring'

docstring -- docstring to be processed
"""
