#!/usr/bin/env python
import os, time
from functools import partial
from flask import Flask, Module, url_for, render_template, request, session, redirect, g, make_response, current_app
from decorators import login_required, guest_or_login_required

from flaskext.openid import OpenID
oid = OpenID()

class SageNBFlask(Flask):
    static_path = ''

    def __init__(self, *args, **kwds):
        startup_token = kwds.pop('startup_token', None)
        Flask.__init__(self, *args, **kwds)

        from sagenb.misc.misc import DATA
        self.add_static_path('/css', os.path.join(DATA, "sage", "css"))        
        self.add_static_path('/images', os.path.join(DATA, "sage", "images"))
        self.add_static_path('/javascript/sage', os.path.join(DATA, "sage", "js"))
        self.add_static_path('/javascript', DATA)
        self.add_static_path('/java', DATA)
        
        #######
        # Doc #
        #######
        #These "should" be in doc.py
        from sagenb.misc.misc import SAGE_DOC 
        DOC = os.path.join(SAGE_DOC, 'output', 'html', 'en')
        self.add_static_path('/pdf', os.path.join(SAGE_DOC, 'output', 'pdf'))
        self.add_static_path('/doc/static', DOC) 
        self.add_static_path('/doc/static/reference', os.path.join(SAGE_DOC, 'en', 'reference'))

        if startup_token:
            from random import randint
            self.one_time_token = str(randint(0, 2**128))
        else:
            self.one_time_token = None

    def create_jinja_environment(self):
        from sagenb.notebook.template import env
        return env

    def static_view_func(self, root_path, filename):
        from flask.helpers import send_from_directory
        return send_from_directory(root_path, filename)

    def add_static_path(self, base_url, root_path):
        self.add_url_rule(base_url + '/<path:filename>',
                          endpoint='/static'+base_url,
                          view_func=partial(self.static_view_func, root_path))

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
    
    if current_app.one_time_token is not None and 'one_time_token' in request.args:
        if request.args['one_time_token'] == current_app.one_time_token:
            session['username'] = 'admin' 
            session.modified = True
            current_app.one_time_token = -1 
            return index()
            
    return login()

######################
# Dynamic Javascript #
######################
@base.route('/javascript/sage/main.js')
def main_js():
    from sagenb.notebook.js import javascript
    response = make_response(javascript())
    response.headers['Content-Type'] = 'text/javascript; charset=utf-8'
    return response

@base.route('/javascript/sage/jsmath.js')
def jsmath_js():
    from sagenb.misc.misc import jsmath_macros
    response = make_response(render_template('js/jsmath.js', jsmath_macros=jsmath_macros,
                                             jsmath_image_fonts=jsmath_image_fonts))
    response.headers['Content-Type'] = 'text/javascript; charset=utf-8'
    return response

@base.route('/javascript/sage/keyboard/<browser_os>')
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
    W = g.notebook.create_new_worksheet_from_history('Log', g.username, 100)
    from worksheet import url_for_worksheet
    return redirect(url_for_worksheet(W))

###########
# Favicon #
###########
@base.route('/favicon.ico')
def favicon():
    from flask.helpers import send_file
    from sagenb.misc.misc import DATA
    return send_file(os.path.join(DATA, 'sage', 'images', 'favicon.ico'))

@base.route('/loginoid', methods=['POST', 'GET'])
@guest_or_login_required
@oid.loginhandler
def loginoid():
    if g.username != 'guest':
        return redirect(oid.get_next_url())
    if request.method == 'POST':
        openid = request.form.get('openid')
        if openid:
            return oid.try_login(openid, ask_for=['email', 'fullname', 'nickname'])
    return render_template('html/loginoid.html', next=oid.get_next_url(),
                           error=oid.fetch_error())

@oid.after_login
def create_or_login(resp):
    session['username'] = username = 'openid' + resp.identity_url[-10:]
    if g.notebook.user_manager().user_exists(username):
        g.username = username
    else:
        from sagenb.notebook.user import User
        new_user = User(username, '', email = resp.email, account_type='user') 
        g.notebook.add_user_if_allowed(new_user)
    return redirect(oid.get_next_url())

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
        notebook.save()
        last_save_time = t

def notebook_idle_check():
    global last_idle_time
    from sagenb.misc.misc import walltime

    t = walltime()
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

    return app
