from functools import wraps
from flask import Flask, url_for, render_template, request, session, redirect, g, current_app
from flaskext.babel import Babel, gettext, ngettext, lazy_gettext
_ = gettext

from threading import Lock
global_lock = Lock()

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwds):
        if 'username' not in session:
            #XXX: Do we have to specify this for the publised
            #worksheets here?
            if request.path.startswith('/home/_sage_/'):
                g.username = 'guest'
                return f(*args, **kwds)
            else:
                return redirect(url_for('base.index', next=request.url))
        else:
            g.username = session['username']
        return f(*args, **kwds)
    return wrapper

def admin_required(f):
    @login_required
    @wraps(f)
    def wrapper(*args, **kwds):
        if not g.notebook.user_manager().user_is_admin(g.username):
            return current_app.message(_("You do not have permission to access this location"), cont=url_for('base.index'))
        return f(*args, **kwds)

    return wrapper

def guest_or_login_required(f):
    @wraps(f)
    def wrapper(*args, **kwds):
        if 'username' not in session:
            g.username = 'guest'
        else:
            g.username = session['username']
        return f(*args, **kwds)
    return wrapper

def with_lock(f):
    @wraps(f)
    def wrapper(*args, **kwds):
        with global_lock:
            return f(*args, **kwds)
    return wrapper
