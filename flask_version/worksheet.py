from functools import wraps
from flask import Flask, url_for, render_template, request, session, redirect, g
from base import app

def worksheet_view(f):
    @login_required
    @wraps(f)
    def wrapper(*args, **kwds):
        worksheet = kwds['worksheet'] = app.get_worksheet_with_filename(kwds['name'])
        owner = worksheet.owner()
        ## if owner != '_sage_' and session['username'] != owner:
        ##     if not worksheet.is_published():
        ##         if not username in self.worksheet.collaborators() and user_type(username) != 'admin':
        ##             raise RuntimeError, "illegal worksheet access"

        if not worksheet.is_published():
            worksheet.set_active(session['username'])

        return f(*args, **kwds)

    return wrapper

@app.route('/new_worksheet')
@login_required
def new_worksheet(self):
    W = notebook.create_new_worksheet("Untitled", self.username)
    return redirect(url_for('worksheet', name=W.filename()))

@app.route('/home/<username>/<name>/')
@worksheet_view
def worksheet(username, name, worksheet=None):
    pass

