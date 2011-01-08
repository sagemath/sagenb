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

from sagenb.misc.misc import SAGE_DOC 
app.add_static_path('/pdf/', os.path.join(SAGE_DOC, 'output', 'pdf'))
app.add_static_path('/doc/static/', os.path.join(SAGE_DOC, 'output', 'html', 'en'))
app.add_static_path('/doc/static/reference/', os.path.join(SAGE_DOC, 'en', 'reference'))
