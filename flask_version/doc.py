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
from flask import Flask, url_for, render_template, request, session, redirect, g
from base import app, SRC, idx
from decorators import login_required, guest_or_login_required

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
    return app.message('nothing to see.', username=g.username)

@app.route('/doc/live/<path:filename>')
@login_required
def doc_live(filename):
    filename = os.path.join(DOC, filename)
    if filename.endswith('.html'):
        from worksheet import worksheet_file
        return worksheet_file(filename)
    else:
        from flask.helpers import send_file
        return send_file(filename)

@app.route('/src/')
@app.route('/src/<path:path>')
@guest_or_login_required
def autoindex(path='.'):
    filename = os.path.join(SRC, path)
    if os.path.isfile(filename):
        from cgi import escape
        src = escape(open(filename).read())
        return render_template(os.path.join('html', 'source_code.html'), src_filename=path, src=src, username = g.username)
    return idx.render_autoindex(path)
