from functools import wraps
from flask import Flask, url_for, render_template, request, session, redirect, g

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwds):
        if 'username' not in session:
            return redirect(url_for('index'))
        return f(*args, **kwds)
    return wrapper
