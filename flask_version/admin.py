import os
from flask import Flask, url_for, render_template, request, session, redirect, g
from base import app
from decorators import login_required, admin_required

# '/users' does not work, because current template calls urls like '/users/?reset=...'
@app.route('/users/')
@admin_required
def users():
    template_dict = {}

    if 'reset' in request.values:
        user = request.values['reset']
        from random import choice
        import string
        chara = string.letters + string.digits
        password = ''.join([choice(chara) for i in range(8)])
        try:
            U = app.notebook.user_manager().user(user)
            app.notebook.user_manager().set_password(user, password)
        except KeyError:
            pass
        template_dict['reset'] = [user, password]

    if 'suspension' in request.values:
        user = request.values['suspension']
        try:
            U = app.notebook.user_manager().user(user)
            U.set_suspension()
        except KeyError:
            pass

    template_dict['number_of_users'] = len(app.notebook.user_manager().valid_login_names()) if len(app.notebook.user_manager().valid_login_names()) > 1 else None
    users = sorted(app.notebook.user_manager().valid_login_names())
    del users[users.index('admin')]
    template_dict['users'] = [app.notebook.user_manager().user(username) for username in users]
    template_dict['admin'] = app.notebook.user_manager().user(g.username).is_admin()
    template_dict['username'] = g.username
    return render_template(os.path.join('html', 'settings', 'user_management.html'), **template_dict)

@app.route('/adduser', methods = ['GET','POST'])
@admin_required
def add_user():
    from sagenb.notebook.twist import is_valid_username
    template_dict = {'admin': app.notebook.user_manager().user(g.username).is_admin(),
                     'username': g.username}
    if 'username' in request.values:
        username = request.values['username']
        if not is_valid_username(username):
            return render_template(os.path.join('html', 'settings', 'admin_add_user.html'),
                                   error='username_invalid', username=username, **template_dict)

        from random import choice
        import string
        chara = string.letters + string.digits
        password = ''.join([choice(chara) for i in range(8)])
        if username in app.notebook.user_manager().usernames():
            return render_template(os.path.join('html', 'settings', 'admin_add_user.html'),
                                   error='username_taken', username_input=username, **template_dict)
        app.notebook.user_manager().add_user(username, password, '', force=True)

        #XXX: i18n
        return app.message('The temporary password for the new user <em>%s</em> is <em>%s</em>' %
                                           (username, password), '/adduser',
                                           title=u'New User')
    else:
        return render_template(os.path.join('html', 'settings', 'admin_add_user.html'),
                               **template_dict)

@app.route('/notebooksettings')
@admin_required
def notebook_settings():
    updated = {}
    if 'form' in request.values:
        updated = app.notebook.conf().update_from_form(request.values)
    template_dict = {}
    template_dict['auto_table'] = app.notebook.conf().html_table(updated)
    template_dict['admin'] = app.notebook.user_manager().user(g.username).is_admin()
    template_dict['username'] = g.username
    return render_template(os.path.join('html', 'settings', 'notebook_settings.html'),
                           **template_dict)

