from functools import wraps
from flask import Flask, url_for, render_template, request, session, redirect, g

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwds):
        if 'username' not in session:
            return redirect(url_for('base.index', next=request.url))
        else:
            g.username = session['username']
        return f(*args, **kwds)
    return wrapper

def admin_required(f):
    @login_required
    @wraps(f)
    def wrapper(*args, **kwds):
        from base import app
        if not app.notebook.user_is_admin(g.username):
            #XXX: i18n
            app.message("You do not have permission to access this location")
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
