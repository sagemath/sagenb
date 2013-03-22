import os
import random
from flask import Module, url_for, render_template, request, session, redirect, g, current_app
from decorators import with_lock
from flaskext.babel import gettext, ngettext, lazy_gettext
_ = gettext

authentication = Module('flask_version.authentication')

##################
# Authentication #
##################
@authentication.before_request
def lookup_current_user():
    g.username = None
    if 'username' in session:
        g.username = session['username']


@authentication.route('/login', methods=['POST', 'GET'])
def login(template_dict={}):
    from sagenb.misc.misc import SAGE_VERSION
    template_dict.update({'accounts': g.notebook.user_manager().get_accounts(),
                          'recovery': g.notebook.conf()['email'],
                          'next': request.values.get('next', ''), 
                          'sage_version': SAGE_VERSION,
                          'openid': g.notebook.conf()['openid'],
                          'username_error': False,
                          'password_error': False})
    
    if request.method == 'POST':
        username = request.form['email']
        password = request.form['password']

        if username == 'COOKIESDISABLED':
            return "Please enable cookies or delete all Sage cookies and localhost cookies in your browser and try again."

        # we only handle ascii usernames.
        from sagenb.notebook.misc import is_valid_username, is_valid_password
        if is_valid_username(username):
            try:
                U = g.notebook.user_manager().user(username)
            except KeyError:
                U = None
                template_dict['username_error'] = True
        else:
            U = None
            template_dict['username_error'] = True

        # It is critically important that it be impossible to login as the
        # pub, _sage_, or guest users.  This _sage_ user is a fake user that is used
        # internally by the notebook for the doc browser and other tasks.
        if username in ['_sage_', 'guest', 'pub']:
            U = None
            template_dict['username_error'] = True

        if U is None:
            pass
        elif (is_valid_password(password, username) and 
              g.notebook.user_manager().check_password(username, password)):
            if U.is_suspended():
                #suspended
                return "Your account is currently suspended"
            else:
                #Valid user, everything is okay
                session['username'] = username
                session.modified = True
                return redirect(request.values.get('next', url_for('base.index')))
        else:
            template_dict['password_error'] = True

    response = current_app.make_response(render_template(os.path.join('html', 'login.html'), **template_dict))
    response.set_cookie('cookie_test_%s'%g.notebook.port, 'cookie_test')
    return response

@authentication.route('/logout/')
def logout():
    username = session.pop('username', None)
    g.notebook.logout(username)
    return redirect(url_for('base.index'))




################
# Registration #
################

#XXX: Yuck!  This global variable should not be here.
#This is data should be stored somewhere more persistant.
waiting = {}

@authentication.route('/register', methods = ['GET','POST'])
@with_lock
def register():
    if not g.notebook.user_manager().get_accounts():
        return redirect(url_for('base.index'))
    from sagenb.notebook.misc import is_valid_username, is_valid_password, \
    is_valid_email, do_passwords_match
    from sagenb.notebook.challenge import challenge

    # VALIDATORS: is_valid_username, is_valid_password,
    # do_passwords_match, is_valid_email,
    # challenge.is_valid_response
    # INPUT NAMES: username, password, retype_password, email +
    # challenge fields

    # TEMPLATE VARIABLES: error, username, username_missing,
    # username_taken, username_invalid, password_missing,
    # password_invalid, passwords_dont_match,
    # retype_password_missing, email, email_missing,
    # email_invalid, email_address, challenge, challenge_html,
    # challenge_missing, challenge_invalid

    # PRE-VALIDATION setup and hooks.
    required = set(['username', 'password'])
    empty = set()
    validated = set()

    # Template variables.  We use empty_form_dict for empty forms.
    empty_form_dict = {}
    template_dict = {}

    if g.notebook.conf()['email']:
        required.add('email')
        empty_form_dict['email'] = True

    if g.notebook.conf()['challenge']:
        required.add('challenge')
        empty_form_dict['challenge'] = True
        chal = challenge(g.notebook.conf(),
                         is_secure = g.notebook.secure,
                         remote_ip = request.environ['REMOTE_ADDR'])
        empty_form_dict['challenge_html'] = chal.html()

    template_dict.update(empty_form_dict)

    # VALIDATE FIELDS.

    # Username.  Later, we check if a user with this username
    # already exists.
    username = request.values.get('username', None)
    if username:
        if not is_valid_username(username):
            template_dict['username_invalid'] = True
        elif g.notebook.user_manager().user_exists(username):
            template_dict['username_taken'] = True
        else:
            template_dict['username'] = username
            validated.add('username')
    else:
        template_dict['username_missing'] = True
        empty.add('username')

    # Password.
    password = request.values.get('password', None)
    retype_password = request.values.get('retype_password', None)
    if password:
        if not is_valid_password(password, username):
            template_dict['password_invalid'] = True
        elif not do_passwords_match(password, retype_password):
            template_dict['passwords_dont_match'] = True
        else:
            validated.add('password')
    else:
        template_dict['password_missing'] = True
        empty.add('password')

    # Email address.
    email_address = ''
    if g.notebook.conf()['email']:
        email_address = request.values.get('email', None)
        if email_address:
            if not is_valid_email(email_address):
                template_dict['email_invalid'] = True
            else:
                template_dict['email_address'] = email_address
                validated.add('email')
        else:
            template_dict['email_missing'] = True
            empty.add('email')

    # Challenge (e.g., reCAPTCHA).
    if g.notebook.conf()['challenge']:
        status = chal.is_valid_response(req_args = request.values)
        if status.is_valid is True:
            validated.add('challenge')
        elif status.is_valid is False:
            err_code = status.error_code
            if err_code:
                template_dict['challenge_html'] = chal.html(error_code = err_code)
            else:
                template_dict['challenge_invalid'] = True
        else:
            template_dict['challenge_missing'] = True
            empty.add('challenge')

    # VALIDATE OVERALL.
    if empty == required:
        # All required fields are empty.  Not really an error.
        return render_template(os.path.join('html', 'accounts', 'registration.html'),
                               **empty_form_dict)
    elif validated != required:
        # Error(s)!
        errors = len(required) - len(validated)
        template_dict['error'] = 'E ' if errors == 1 else 'Es '
        return render_template(os.path.join('html', 'accounts', 'registration.html'),
                        **template_dict)

    # Create an account, if username is unique.
    try:
        g.notebook.user_manager().add_user(username, password, email_address)
    except ValueError:
        template_dict['username_taken'] = True
        template_dict['error'] = 'E '

        form = render_template(os.path.join('html', 'accounts', 'registration.html'),
                        **template_dict)
        return HTMLResponse(stream = form)

    #XXX: Add logging support
    #log.msg("Created new user '%s'"%username)

    # POST-VALIDATION hooks.  All required fields should be valid.
    if g.notebook.conf()['email']:
        from sagenb.notebook.smtpsend import send_mail
        from sagenb.notebook.register import make_key, build_msg

        # TODO: make this come from the server settings
        key = make_key()
        listenaddr = g.notebook.interface
        port = g.notebook.port
        fromaddr = 'no-reply@%s' % listenaddr
        body = build_msg(key, username, listenaddr, port, g.notebook.secure)

        # Send a confirmation message to the user.
        try:
            send_mail(fromaddr, email_address,
                      "Sage Notebook Registration", body)
            waiting[key] = username
        except ValueError:
            pass

    # Go to the login page.
    from sagenb.misc.misc import SAGE_VERSION
    template_dict = {'accounts': g.notebook.user_manager().get_accounts(),
                     'welcome_user': username,
                     'recovery': g.notebook.conf()['email'],
                     'sage_version': SAGE_VERSION}

    return render_template(os.path.join('html', 'login.html'), **template_dict)


@authentication.route('/confirm')
@with_lock
def confirm():
    if not g.notebook.conf()['email']:
        return current_app.message(_('The confirmation system is not active.'))
    key = int(request.values.get('key', '-1'))
    
    invalid_confirm_key = _("""\
    <h1>Invalid confirmation key</h1>
    <p>You are reporting a confirmation key that has not been assigned by this
    server. Please <a href="/register">register</a> with the server.</p>
    """)
    try:
        username = waiting[key]
        user = g.notebook.user(username)
        user.set_email_confirmation(True)
    except KeyError:
        return current_app.message(invalid_confirm_key, '/register')
    success = _("""<h1>Email address confirmed for user %(username)s</h1>""", username=username)
    del waiting[key]
    return current_app.message(success, title=_('Email Confirmed'))

@authentication.route('/forgotpass')
@with_lock
def forgot_pass():
    if not g.notebook.conf()['email']:
        return current_app.message('The account recovery system is not active.')

    username = request.values.get('username', '').strip()
    if not username:
        return render_template(os.path.join('html', 'accounts', 'account_recovery.html'))

    def error(msg):
        return current_app.message(msg, url_for('forgot_pass'))

    try:
        user = g.notebook.user(username)
    except KeyError:
        return error('Username is invalid.')

    if not user.is_email_confirmed():
        return error("The e-mail address hasn't been confirmed.")

    #XXX: some of this could be factored out into a random passowrd
    #function.  There are a few places in admin.py that also use it.
    from random import choice
    import string
    chara = string.letters + string.digits
    old_pass = user.password()
    password = ''.join([choice(chara) for i in range(8)])
    user.set_password(password)

    from sagenb.notebook.smtpsend import send_mail
    from sagenb.notebook.register import build_password_msg
    # TODO: make this come from the server settings

    listenaddr = g.notebook.interface
    port = g.notebook.port
    fromaddr = 'no-reply@%s' % listenaddr
    body = build_password_msg(password, username, listenaddr, port, g.notebook.secure)
    destaddr = user.get_email()
    try:
        send_mail(fromaddr, destaddr, "Sage Notebook Account Recovery", body)
    except ValueError:
        # the email address is invalid
        user.set_password(old_pass)
        return error("The new password couldn't be sent."%destaddr)

    return current_app.message("A new password has been sent to your e-mail address.", url_for('base.index'))

