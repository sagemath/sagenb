import os
from flask import Module, url_for, render_template, request, session, redirect, g, current_app
from decorators import login_required, admin_required, with_lock
from flaskext.babel import Babel, gettext, ngettext, lazy_gettext
_ = gettext
from sagenb.notebook.misc import encode_response

admin = Module('flask_server.admin')

def random_password(length=8):
    from random import choice
    import string
    chara = string.letters + string.digits
    return ''.join([choice(chara) for i in range(length)])

@admin.route('/manage_users')
@admin_required
@with_lock
def manage_users():
    template_dict = {}
    template_dict['number_of_users'] = len(g.notebook.user_manager().valid_login_names()) if len(g.notebook.user_manager().valid_login_names()) > 1 else None
    users = sorted(g.notebook.user_manager().valid_login_names())
    del users[users.index('admin')]
    template_dict['users'] = [g.notebook.user_manager().user(username) for username in users]
    return render_template(os.path.join('html', 'settings', 'manage_users.html'), **template_dict)

@admin.route('/reset_user_password', methods = ['POST'])
@admin_required
@with_lock
def reset_user_password():
    user = request.values['username']
    password = random_password()
    try:
        # U = g.notebook.user_manager().user(user)
        g.notebook.user_manager().set_password(user, password)
    except KeyError:
        pass

    return encode_response({
        'message': _('The temporary password for the new user <strong>%(username)s</strong> is <strong>%(password)s</strong>',
                          username=user, password=password)
    })

@admin.route('/suspend_user', methods = ['POST'])
@admin_required
@with_lock
def suspend_user():
    user = request.values['username']
    try:
        U = g.notebook.user_manager().user(user)
        U.set_suspension()
    except KeyError:
        pass

    return encode_response({
        'message': _('User <strong>%(username)s</strong> has been suspended/unsuspended.', username=user)
    })

@admin.route('/add_user', methods = ['POST'])
@admin_required
@with_lock
def add_user():
    from sagenb.notebook.misc import is_valid_username

    username = request.values['username']
    password = random_password()

    if not is_valid_username(username):
        return encode_response({
            'error': _('<strong>Invalid username!</strong>')
        })

    if username in g.notebook.user_manager().usernames():
        return encode_response({
            'error': _('The username <strong>%(username)s</strong> is already taken!', username=username)
        })

    g.notebook.user_manager().add_user(username, password, '', force=True)
    return encode_response({
        'message': _('The temporary password for the new user <strong>%(username)s</strong> is <strong>%(password)s</strong>',
                      username=username, password=password)
    })

@admin.route('/notebook_settings', methods=['GET', 'POST'])
@admin_required
@with_lock
def notebook_settings():
    updated = {}
    if 'form' in request.values:
        updated = g.notebook.conf().update_from_form(request.values)
        
    # Make changes to the default language used
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

