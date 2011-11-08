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

        self.add_static_path('/css', os.path.join(DATA, "sage", "css"))        
        self.add_static_path('/images', os.path.join(DATA, "sage", "images"))
        self.add_static_path('/javascript', DATA)
        self.add_static_path('/static', DATA)
        self.add_static_path('/java', DATA)
        import mimetypes
        mimetypes.add_type('text/plain','.jmol')

        
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


#XXX: This should probably be made able to put in a "central" place
#with all of the jsmath stuff rather than just a global variable here.
from sagenb.misc.misc import is_package_installed
jsmath_image_fonts = is_package_installed("jsmath-image-fonts")

base = Module('flask_version.base')



#############
# Main Page #
#############
@base.route('/')
def index():
    if 'username' in session:
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
            current_app.startup_token = -1 
            return index()

    return login()

######################
# Dynamic Javascript #
######################
@base.route('/javascript/dynamic/notebook_dynamic.js')
def dynamic_js():
    from sagenb.notebook.js import javascript
    # the javascript() function is cached, so there shouldn't be a big slowdown calling it
    response = make_response(javascript())
    response.headers['Content-Type'] = 'text/javascript; charset=utf-8'
    return response

_localization_cache = None
@base.route('/javascript/dynamic/localization.js')
def localization_js():
    global _localization_cache
    if _localization_cache is None:
        _localization_cache = render_template(os.path.join('js/localization.js'))
    response = make_response(_localization_cache)
    response.headers['Content-Type'] = 'text/javascript; charset=utf-8'
    return response


_jsmath_js_cache = None
@base.route('/javascript/dynamic/jsmath.js')
def jsmath_js():
    global _jsmath_js_cache
    if _jsmath_js_cache is None:
        from sagenb.misc.misc import jsmath_macros
        _jsmath_js_cache = render_template('js/jsmath.js', jsmath_macros=jsmath_macros,
                                           jsmath_image_fonts=jsmath_image_fonts)
    response = make_response(_jsmath_js_cache)
    response.headers['Content-Type'] = 'text/javascript; charset=utf-8'
    return response

@base.route('/javascript/dynamic/keyboard/<browser_os>')
def keyboard_js(browser_os):
    from sagenb.notebook.keyboards import get_keyboard
    response = make_response(get_keyboard(browser_os))
    response.headers['Content-Type'] = 'text/javascript; charset=utf-8'
    return response

###############
# Dynamic CSS #
###############
@base.route('/css/main.css')
def main_css():
    from sagenb.notebook.css import css 
    # the css() function is cached, so there shouldn't be a big slowdown calling it
    response = make_response(css())
    response.headers['Content-Type'] = 'text/css; charset=utf-8'
    return response

########
# Help #
########
@base.route('/help')
@login_required
def help():
    from sagenb.notebook.tutorial import notebook_help
    return render_template(os.path.join('html', 'docs.html'), username = g.username, notebook_help = notebook_help)

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

###########
# Favicon #
###########
@base.route('/favicon.ico')
def favicon():
    from flask.helpers import send_file
    return send_file(os.path.join(DATA, 'sage', 'images', 'favicon.ico'))

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
    if request.method == 'GET' and 'openid_response' in session:
        from sagenb.notebook.misc import valid_username_chars
        re_invalid_username_chars = re.compile('[^(%s)]' % valid_username_chars)
        openid_resp = session['openid_response']
        if openid_resp.fullname is not None:
            openid_resp.fullname = re.sub(re_invalid_username_chars, '_', openid_resp.fullname)
        return render_template('html/accounts/openid_profile.html', resp=openid_resp)

    if request.method == 'POST':
        parse_dict = {'resp':session['openid_response']}
        try:
            resp = session['openid_response']
            username = request.form.get('username')
            from sagenb.notebook.user import User
            from sagenb.notebook.misc import is_valid_username, is_valid_email
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
    notebook.JSMATH = True
    notebook = notebook.load_notebook(path_to_notebook, *args, **kwds)
    init_updates()

    ##############
    # Create app #
    ##############
    app = SageNBFlask('flask_version', startup_token=startup_token)
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
    app.register_module(base)

    from worksheet_listing import worksheet_listing
    app.register_module(worksheet_listing)  

    from admin import admin
    app.register_module(admin)

    from authentication import authentication
    app.register_module(authentication)

    from doc import doc
    app.register_module(doc)

    from worksheet import ws as worksheet
    app.register_module(worksheet)

    from settings import settings
    app.register_module(settings)

    #autoindex v0.3 doesnt seem to work with modules
    #routing with app directly does the trick
    #TODO: Check to see if autoindex 0.4 works with modules
    idx = AutoIndex(app, browse_root=SRC)
    @app.route('/src/')
    @app.route('/src/<path:path>')
    @guest_or_login_required
    def autoindex(path='.'):
        filename = os.path.join(SRC, path)
        if os.path.isfile(filename):
            from cgi import escape
            src = escape(open(filename).read().decode('utf-8','ignore'))
            if (os.path.splitext(filename)[1] in 
                ['.py','.c','.cc','.h','.hh','.pyx','.pyd']):
                return render_template(os.path.join('html', 'source_code.html'),
                                       src_filename=path, 
                                       src=src, username = g.username)
            return src
        return idx.render_autoindex(path)

    return app
