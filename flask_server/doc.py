"""
Documentation functions

URLS to do:

###/pdf/       <-FILE->  DOC_PDF
###/doc/live/   - WorksheetFile(os.path.join(DOC, name)
###/doc/static/ - DOC/index.html
###/doc/static/reference/ <-FILE-> DOC/reference/
###/doc/reference/media/  <-FILE-> DOC_REF_MEDIA

/src/             - SourceBrowser
/src/<name>       - Source(os.path.join(SRC,name), self.username)

"""
import os
from flask import Module, url_for, render_template, request, session, redirect, g, current_app
from decorators import login_required, guest_or_login_required

doc = Module('flask_server.doc')

from sagenb.misc.misc import SAGE_DOC 
DOC = os.path.join(SAGE_DOC, 'output', 'html', 'en')

################
# Static paths #
################

#The static documentation paths are currently set in base.SageNBFlask.__init__

@doc.route('/doc/static/')
def docs_static_index():
    return redirect('/doc/static/index.html')

@doc.route('/doc/live/')
@login_required
def doc_live_base():
    return current_app.message('nothing to see.', username=g.username)

@doc.route('/doc/live/<manual>/<path:path_static>/_static/<path:filename>')
@login_required
def doc_static_file(manual, path_static, filename):
    """
    The docs reference a _static URL in the current directory, even if
    the real _static directory only lives in the root of the manual.
    This function strips out the subdirectory part and returns the
    file from the _static directory in the root of the manual.

    This seems like a Sphinx bug: the generated html file should not
    reference a _static in the current directory unless there actually
    is a _static directory there.

    TODO: Determine if the reference to a _static in the current
    directory is a bug in Sphinx, and file a report or see if it has
    already been fixed upstream.
    """
    from flask.helpers import send_file
    filename = os.path.join(DOC, manual, '_static', filename)
    return send_file(filename)

@doc.route('/doc/live/<path:filename>')
@login_required
def doc_live(filename):
    filename = os.path.join(DOC, filename)
    from flask.helpers import send_file
    return send_file(filename)
