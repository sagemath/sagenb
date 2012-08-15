#!/usr/bin/env python
import os, time, re
from functools import partial
from flask import Flask, Module, url_for, render_template, request, session, redirect, g, make_response, current_app
from decorators import login_required, guest_or_login_required, with_lock
from decorators import global_lock

from flaskext.autoindex import AutoIndex
SRC = os.path.join(os.environ['SAGE_ROOT'], 'devel', 'sage', 'sage')
from flaskext.openid import OpenID
from flaskext.babel import Babel, gettext, ngettext, lazy_gettext, get_locale
from sagenb.misc.misc import SAGENB_ROOT, DATA, SAGE_DOC, translations_path

oid = OpenID()

class SageNBFlask(Flask):
    static_path = ''

    def __init__(self, *args, **kwds):
        self.startup_token = kwds.pop('startup_token', None)
        Flask.__init__(self, *args, **kwds)

        self.root_path = SAGENB_ROOT

        # I think it would make more sense just to have one /data/ path and not do one for every kind of file
        self.add_static_path('/data', os.path.join(DATA))
        
        # this one is special though since it points to SAGE_ROOT
        self.add_static_path('/java/jmol', os.path.join(os.environ["SAGE_ROOT"], "local", "share", "jmol"))
        
        
        import mimetypes
        mimetypes.add_type('text/plain', '.jmol')
        mimetypes.add_type('font/opentype', '.otf')
        mimetypes.add_type('application/font-woff', '.woff')

        #######
        # Doc #
        #######
        #These "should" be in doc.py
        DOC = os.path.join(SAGE_DOC, 'output', 'html', 'en')
        self.add_static_path('/pdf', os.path.join(SAGE_DOC, 'output', 'pdf'))
        self.add_static_path('/doc/static', DOC)
        #self.add_static_path('/doc/static/reference', os.path.join(SAGE_DOC, 'reference'))

    def create_jinja_environment(self):
        from sagenb.notebook.template import env
        env.globals.update(url_for=url_for)
        return env

    def static_view_func(self, root_path, filename):
        from flask.helpers import send_from_directory
        return send_from_directory(root_path, filename)

    def add_static_path(self, base_url, root_path):
        self.add_url_rule(base_url + '/<path:filename>',
                          endpoint='/static'+base_url,
                          view_func=partial(self.static_view_func, root_path))

    def save_session(self, session, response):
        """
        This method needs to stay in sync with the version in Flask.
        The only modification made to it is the ``httponly=False``
        passed to ``save_cookie``.

        Saves the session if it needs updates.  For the default
        implementation, check :meth:`open_session`.

        :param session: the session to be saved (a
                        :class:`~werkzeug.contrib.securecookie.SecureCookie`
                        object)
        :param response: an instance of :attr:`response_class`
        """
        expires = domain = None
        if session.permanent:
            expires = datetime.utcnow() + self.permanent_session_lifetime
        if self.config['SERVER_NAME'] is not None:
            domain = '.' + self.config['SERVER_NAME']
        session.save_cookie(response, self.session_cookie_name,
                            expires=expires, httponly=False, domain=domain)

    def message(self, msg, cont='/', username=None, **kwds):
        """Returns an error message to the user."""
        template_dict = {'msg': msg, 'cont': cont, 'username': username}
        template_dict.update(kwds)
        return render_template(os.path.join('html', 'error_message.html'),
                               **template_dict)

base = Module('flask_server.base')

#############
# Main Page #
#############
@base.route('/')
def index():
    if 'username' in session:
        # If there is a next request use that.  See issue #76
        if 'next' in request.args:
            response = redirect(request.values.get('next', ''))
            return response
        response = redirect(url_for('worksheet_listing.home', username=session['username']))
        if 'remember' in request.args:
            response.set_cookie('nb_session_%s'%g.notebook.port,
                                expires=(time.time() + 60 * 60 * 24 * 14))
        else:
            response.set_cookie('nb_session_%s'%g.notebook.port)
        response.set_cookie('cookie_test_%s'%g.notebook.port, expires=1)
        return response

    from authentication import login

    if current_app.startup_token is not None and 'startup_token' in request.args:
        if request.args['startup_token'] == current_app.startup_token:
            g.username = session['username'] = 'admin'
            session.modified = True
            current_app.startup_token = None
            return index()

    return login()

######################
# Dynamic Javascript #
######################
from hashlib import sha1

@base.route('/javascript/dynamic/username.js')
@guest_or_login_required
def username_js():
    r = make_response(render_template(os.path.join('js', 'username.js'), username = g.username))
    r.mimetype = "application/javascript"
    return r

_localization_cache = {}
@base.route('/data/sage/js/localization.js')
@base.route('/javascript/dynamic/localization.js')
def localization_js():
    global _localization_cache
    locale = repr(get_locale())
    if _localization_cache.get(locale,None) is None:
        data = render_template(os.path.join('js/localization.js'))
        _localization_cache[locale] = (data, sha1(repr(data)).hexdigest())
    data, datahash = _localization_cache[locale]

    if request.environ.get('HTTP_IF_NONE_MATCH', None) == datahash:
        response = make_response('', 304)
    else:
        response = make_response(data)
        response.headers['Content-Type'] = 'text/javascript; charset=utf-8'
        response.headers['Etag'] = datahash
    return response

# _mathjax_js_cache = None
# @base.route('/javascript/dynamic/mathjax_sage.js')
# def mathjax_js():
#     global _mathjax_js_cache
#     if _mathjax_js_cache is None:
#         from sagenb.misc.misc import mathjax_macros
#         data = render_template('js/mathjax_sage.js', theme_mathjax_macros=mathjax_macros)
#         _mathjax_js_cache = (data, sha1(repr(data)).hexdigest())
#     data, datahash = _mathjax_js_cache
#
#    if request.environ.get('HTTP_IF_NONE_MATCH', None) == datahash:
#        response = make_response('',304)
#    else:
#        response = make_response(data)
#        response.headers['Content-Type'] = 'text/javascript; charset=utf-8'
#        response.headers['Etag']=datahash
#    return response

########
# Help #
########
@base.route('/help')
@login_required
def help():
    return render_template(os.path.join('html', 'docs.html'))

###########
# History #
###########
@base.route('/history')
@login_required
def history():
    return render_template(os.path.join('html', 'history.html'), username = g.username, 
                           text = g.notebook.user_history_text(g.username), actions = False)

@base.route('/live_history')
@login_required
def live_history():
    W = g.notebook.create_new_worksheet_from_history(gettext('Log'), g.username, 100)
    from worksheet import url_for_worksheet
    return redirect(url_for_worksheet(W))

@base.route('/loginoid', methods=['POST', 'GET'])
@guest_or_login_required
@oid.loginhandler
def loginoid():
    if not g.notebook.conf()['openid']:
        return redirect(url_for('base.index'))
    if g.username != 'guest':
        return redirect(request.values.get('next', url_for('base.index')))
    if request.method == 'POST':
        openid = request.form.get('url')
        if openid:
            return oid.try_login(openid, ask_for=['email', 'fullname', 'nickname'])
    return redirect(url_for('authentication.login'))
    #render_template('html/login.html', next=oid.get_next_url(), error=oid.fetch_error())

@oid.after_login
@with_lock
def create_or_login(resp):
    if not g.notebook.conf()['openid']:
        return redirect(url_for('base.index'))
    try:
        username = g.notebook.user_manager().get_username_from_openid(resp.identity_url)
        session['username'] = g.username = username
        session.modified = True
    except KeyError:
        session['openid_response'] = resp
        session.modified = True
        return redirect(url_for('set_profiles'))
    return redirect(request.values.get('next', url_for('base.index')))

@base.route('/openid_profiles', methods=['POST','GET'])
def set_profiles():
    if not g.notebook.conf()['openid']:
        return redirect(url_for('base.index'))

    from sagenb.notebook.challenge import challenge


    show_challenge=g.notebook.conf()['challenge']
    if show_challenge:
        chal = challenge(g.notebook.conf(),
                         is_secure = g.notebook.secure,
                         remote_ip = request.environ['REMOTE_ADDR'])

    if request.method == 'GET':
        if 'openid_response' in session:
            from sagenb.notebook.misc import valid_username_chars
            re_invalid_username_chars = re.compile('[^(%s)]' % valid_username_chars)
            openid_resp = session['openid_response']
            if openid_resp.fullname is not None:
                openid_resp.fullname = re.sub(re_invalid_username_chars, '_', openid_resp.fullname)
            template_dict={}
            if show_challenge:
                template_dict['challenge_html'] = chal.html()

            return render_template('html/accounts/openid_profile.html', resp=openid_resp, 
                                   challenge=show_challenge, **template_dict)
        else:
            return redirect(url_for('base.index'))


    if request.method == 'POST':
        if 'openid_response' in session:
            parse_dict = {'resp':session['openid_response']}
        else:
            return redirect(url_for('base.index'))

        try:
            resp = session['openid_response']
            username = request.form.get('username')
            from sagenb.notebook.user import User
            from sagenb.notebook.misc import is_valid_username, is_valid_email

            if show_challenge:
                parse_dict['challenge'] = True
                status = chal.is_valid_response(req_args = request.values)
                if status.is_valid is True:
                    pass
                elif status.is_valid is False:
                    err_code = status.error_code
                    if err_code:
                        parse_dict['challenge_html'] = chal.html(error_code = err_code)
                    else:
                        parse_dict['challenge_invalid'] = True
                    raise ValueError
                else:
                    parse_dict['challenge_missing'] = True
                    raise ValueError

            if not is_valid_username(username):
                parse_dict['username_invalid'] = True
                raise ValueError
            if g.notebook.user_manager().user_exists(username):
                parse_dict['username_taken'] = True
                raise ValueError
            if not is_valid_email(request.form.get('email')):
                parse_dict['email_invalid'] = True
                raise ValueError
            try:
                new_user = User(username, '', email = resp.email, account_type='user') 
                g.notebook.user_manager().add_user_object(new_user)
            except ValueError:
                parse_dict['creation_error'] = True
                raise ValueError
            g.notebook.user_manager().create_new_openid(resp.identity_url, username)
            session['username'] = g.username = username
            session.modified = True
        except ValueError:
            return render_template('html/accounts/openid_profile.html', **parse_dict) 
        return redirect(url_for('base.index'))


#############
# OLD STUFF #
#############
############################
# Notebook autosave.
############################
# save if make a change to notebook and at least some seconds have elapsed since last save.
def init_updates():
    global save_interval, idle_interval, last_save_time, last_idle_time
    from sagenb.misc.misc import walltime

    save_interval = notebook.conf()['save_interval']
    idle_interval = notebook.conf()['idle_check_interval']
    last_save_time = walltime()
    last_idle_time = walltime()

def notebook_save_check():
    global last_save_time
    from sagenb.misc.misc import walltime

    t = walltime()
    if t > last_save_time + save_interval:
        with global_lock:
            # if someone got the lock before we did, they might have saved,
            # so we check against the last_save_time again
            # we don't put the global_lock around the outer loop since we don't need
            # it unless we are actually thinking about saving.
            if t > last_save_time + save_interval:
                notebook.save()
                last_save_time = t

def notebook_idle_check():
    global last_idle_time
    from sagenb.misc.misc import walltime

    t = walltime()

    if t > last_idle_time + idle_interval:
        with global_lock:
            # if someone got the lock before we did, they might have already idled,
            # so we check against the last_idle_time again
            # we don't put the global_lock around the outer loop since we don't need
            # it unless we are actually thinking about quitting worksheets
            if t > last_idle_time + idle_interval:
                notebook.update_worksheet_processes()
                notebook.quit_idle_worksheet_processes()
                last_idle_time = t

def notebook_updates():
    notebook_save_check()
    notebook_idle_check()


notebook = None

#CLEAN THIS UP!
def create_app(path_to_notebook, *args, **kwds):
    """
    This is the main method to create a running notebook. This is
    called from the process spawned in run_notebook.py
    """
    global notebook
    startup_token = kwds.pop('startup_token', None)

    #############
    # OLD STUFF #
    #############
    import sagenb.notebook.notebook as notebook
    notebook.MATHJAX = True
    notebook = notebook.load_notebook(path_to_notebook, *args, **kwds)
    init_updates()

    ##############
    # Create app #
    ##############
    app = SageNBFlask('flask_server', startup_token=startup_token)
    app.secret_key = os.urandom(24)
    oid.init_app(app)
    app.debug = True

    @app.before_request
    def set_notebook_object():
        g.notebook = notebook

    ####################################
    # create Babel translation manager #
    ####################################
    babel = Babel(app, default_locale=notebook.conf()['default_language'],
                  default_timezone='UTC',
                  date_formats=None, configure_jinja=True)

    ########################
    # Register the modules #
    ########################
    app.register_blueprint(base)

    from worksheet_listing import worksheet_listing
    app.register_blueprint(worksheet_listing)

    from admin import admin
    app.register_blueprint(admin)

    from authentication import authentication
    app.register_blueprint(authentication)

    from doc import doc
    app.register_blueprint(doc)

    from worksheet import ws as worksheet
    app.register_blueprint(worksheet)

    from settings import settings
    app.register_blueprint(settings)

    #autoindex v0.3 doesnt seem to work with modules
    #routing with app directly does the trick
    #TODO: Check to see if autoindex 0.4 works with modules
    idx = AutoIndex(app, browse_root=SRC, add_url_rules=False)
    @app.route('/src/')
    @app.route('/src/<path:path>')
    @guest_or_login_required
    def autoindex(path='.'):
        filename = os.path.join(SRC, path)
        if os.path.isfile(filename):
            from cgi import escape
            src = escape(open(filename).read().decode('utf-8','ignore'))
            if (os.path.splitext(filename)[1] in
                ['.py','.c','.cc','.h','.hh','.pyx','.pxd']):
                return render_template(os.path.join('html', 'source_code.html'),
                                       src_filename=path,
                                       src=src, username = g.username)
            return src
        return idx.render_autoindex(path)

    return app