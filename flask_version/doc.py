"""
Documentation functions

URLS to do:

/pdf/       <-FILE->  DOC_PDF
/doc/        - Doc
/doc/live/   - WorksheetFile(os.path.join(DOC, name)
/doc/static/ - DOC/index.html
/doc/static/reference/ <-FILE-> DOC/reference/
/doc/reference/media/  <-FILE-> DOC_REF_MEDIA

/src/             - SourceBrowser
/src/<name>       - Source(os.path.join(SRC,name), self.username)

"""
from flask import Flask, url_for, render_template, request, session, redirect, g
from base import app
