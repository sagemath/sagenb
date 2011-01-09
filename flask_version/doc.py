"""
Documentation functions

URLS to do:

###/pdf/       <-FILE->  DOC_PDF
/doc/        - Doc
/doc/live/   - WorksheetFile(os.path.join(DOC, name)
/doc/static/ - DOC/index.html
###doc/static/reference/ <-FILE-> DOC/reference/
###/doc/reference/media/  <-FILE-> DOC_REF_MEDIA

/src/             - SourceBrowser
/src/<name>       - Source(os.path.join(SRC,name), self.username)

"""
import os
from flask import Flask, url_for, render_template, request, session, redirect, g
from base import app
from decorators import login_required

from sagenb.misc.misc import SAGE_DOC 
DOC = os.path.join(SAGE_DOC, 'output', 'html', 'en')

app.add_static_path('/pdf', os.path.join(SAGE_DOC, 'output', 'pdf'))
app.add_static_path('/doc/static', DOC) 
app.add_static_path('/doc/static/reference', os.path.join(SAGE_DOC, 'en', 'reference'))

@app.route('/doc/static/')
def docs_static_index():
    return redirect(url_for('/static/doc/static', filename='index.html'))

@app.route('/doc/live/')
@login_required
def doc_live_base():
    return app.message('nothing to see.', username = session['username'])

@app.route('/doc/live/<path:filename>')
@login_required
def doc_live(filename):
    from worksheet import worksheet_file
    return worksheet_file(os.path.join(DOC, filename))
