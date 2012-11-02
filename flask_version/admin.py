import os
from flask import Module, url_for, render_template, request, session, redirect, g, current_app
from decorators import login_required, admin_required, with_lock
from flaskext.babel import Babel, gettext, ngettext, lazy_gettext
_ = gettext

admin = Module('flask_version.admin')

@admin.route('/users')
@admin.route('/users/reset/<reset>')
@admin_required
@with_lock
def users(reset=None):
    template_dict = {}
    if reset:
        from random import choice
        import string
        chara = string.letters + string.digits
        password = ''.join([choice(chara) for i in range(8)])
        try:
            U = g.notebook.user_manager().user(reset)
            g.notebook.user_manager().set_password(reset, password)
        except KeyError:
            pass
        template_dict['reset'] = [reset, password]

    template_dict['number_of_users'] = len(g.notebook.user_manager().valid_login_names()) if len(g.notebook.user_manager().valid_login_names()) > 1 else None
    users = sorted(g.notebook.user_manager().valid_login_names())
    del users[users.index('admin')]
    template_dict['users'] = [g.notebook.user_manager().user(username) for username in users]
    template_dict['admin'] = g.notebook.user_manager().user(g.username).is_admin()
    template_dict['username'] = g.username
    return render_template(os.path.join('html', 'settings', 'user_management.html'), **template_dict)

@admin.route('/users/suspend/<user>')
@admin_required
@with_lock
def suspend_user(user):
    try:
        U = g.notebook.user_manager().user(user)
        U.set_suspension()
    except KeyError:
        pass
    return redirect(url_for("users"))

@admin.route('/users/delete/<user>')
@admin_required
@with_lock
def del_user(user):
    if user != 'admin':
        try:
            g.notebook.user_manager().delete_user(user)
        except KeyError:
            pass
    return redirect(url_for("users"))

@admin.route('/users/toggleadmin/<user>')
@admin_required
@with_lock
def toggle_admin(user):
    try:
        U = g.notebook.user_manager().user(user)
        if U.is_admin():
            U.revoke_admin()
        else:
            U.grant_admin()
    except KeyError:
        pass
    return redirect(url_for("users"))

@admin.route('/adduser', methods = ['GET','POST'])
@admin_required
@with_lock
def add_user():
    from sagenb.notebook.misc import is_valid_username
    template_dict = {'admin': g.notebook.user_manager().user(g.username).is_admin(),
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
        if username in g.notebook.user_manager().usernames():
            return render_template(os.path.join('html', 'settings', 'admin_add_user.html'),
                                   error='username_taken', username_input=username, **template_dict)
        g.notebook.user_manager().add_user(username, password, '', force=True)

        message = _('The temporary password for the new user <em>%(username)s</em> is <em>%(password)s</em>',
                          username=username, password=password)
        return current_app.message(message, cont='/adduser', title=_('New User'))
    else:
        return render_template(os.path.join('html', 'settings', 'admin_add_user.html'),
                               **template_dict)

@admin.route('/notebooksettings', methods=['GET', 'POST'])
@admin_required
@with_lock
def notebook_settings():
    updated = {}
    if 'form' in request.values:
        updated = g.notebook.conf().update_from_form(request.values)
        
    #Make changes to the default language used
    if 'default_language' in request.values:
        from flaskext.babel import refresh
        refresh()
        current_app.config['BABEL_DEFAULT_LOCALE'] = request.values['default_language']
        
    template_dict = {}
    template_dict['auto_table'] = g.notebook.conf().html_table(updated)
    template_dict['admin'] = g.notebook.user_manager().user(g.username).is_admin()
    template_dict['username'] = g.username
        
    return render_template(os.path.join('html', 'settings', 'notebook_settings.html'),
                           **template_dict)

