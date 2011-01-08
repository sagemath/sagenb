"""
"""
from flask import Flask, url_for, render_template, request, session, redirect, g
from decorators import login_required
from base import app

@app.route('/home/<username>/')
@login_required
def home(username):
    if not app.notebook.user_is_admin(username) and username != session['username']:
        #XXX: Put this into a template
        return "User '%s' does not have permission to view the home page of '%s'."%(session['username'],
                                                                                    username)
    else:
        from sagenb.notebook.twist import render_worksheet_list
        import sagenb.notebook.twist as twist
        twist.notebook = app.notebook
        return render_worksheet_list(request.args, pub=False, username=session['username'])

@app.route('/home/')
@login_required
def bare_home():
    return redirect(url_for('home', username=session['username']))
