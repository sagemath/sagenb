import os
from flask import Module, url_for, render_template, request, session, redirect, g, current_app
from decorators import login_required, admin_required, with_lock
from flaskext.babel import Babel, gettext, ngettext, lazy_gettext
_ = gettext

admin = Module('flask_version.admin')

# '/users' does not work, because current template calls urls like '/users/?reset=...'
@admin.route('/users/')
@admin_required
@with_lock
def users():
    template_dict = {}

    if 'reset' in request.values:
        user = request.values['reset']
        from random import choice
        import string
        chara = string.letters + string.digits
        password = ''.join([choice(chara) for i in range(8)])
        try:
            U = g.notebook.user_manager().user(user)
            g.notebook.user_manager().set_password(user, password)
        except KeyError:
            pass
        template_dict['reset'] = [user, password]

    if 'suspension' in request.values:
        user = request.values['suspension']
        try:
            U = g.notebook.user_manager().user(user)
            U.set_suspension()
        except KeyError:
            pass

    template_dict['number_of_users'] = len(g.notebook.user_manager().valid_login_names()) if len(g.notebook.user_manager().valid_login_names()) > 1 else None
    users = sorted(g.notebook.user_manager().valid_login_names())
    del users[users.index('admin')]
    template_dict['users'] = [g.notebook.user_manager().user(username) for username in users]
    template_dict['admin'] = g.notebook.user_manager().user(g.username).is_admin()
    template_dict['username'] = g.username
    return render_template(os.path.join('html', 'settings', 'user_management.html'), **template_dict)

@admin.route('/adduser', methods = ['GET','POST'])
@admin_required
@with_lock
def add_user():
    from sagenb.notebook.twist import is_valid_username
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

        message = gettext('The temporary password for the new user <em>%(username)s</em> is <em>%(password)s</em>',
                          username=username, password=password)
        return current_app.message(message='/adduser', title=_('New User'))
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

