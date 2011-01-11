#!/usr/bin/env python
import os, time
from functools import partial
from flask import Flask, Module, url_for, render_template, request, session, redirect, g, make_response, current_app
from decorators import login_required

class SageNBFlask(Flask):
    static_path = ''

    def __init__(self, *args, **kwds):
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

        from random import randint
        self.one_time_token = str(randint(0, 2**128))

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
    
    if current_app.one_time_token != -1 and 'one_time_token' in request.args:
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
def init_app(path_to_notebook, port=5000):
    global notebook

    print "Starting notebook..."
    port = 5000
    
    #############
    # OLD STUFF #
    #############
    import sagenb.notebook.notebook
    sagenb.notebook.notebook.JSMATH = True
    import sagenb.notebook.notebook as notebook

    notebook = notebook.load_notebook(path_to_notebook,interface="localhost",port=port,secure=False)
    SAGETEX_PATH = ""
    OPEN_MODE = False
    SID_COOKIE = str(hash(path_to_notebook))
    DIR = path_to_notebook
    init_updates()

    ##############
    # Create app #
    ##############
    app = SageNBFlask('flask_version')
    app.secret_key = os.urandom(24)

    @app.before_request
    def set_notebook_object():
        g.notebook = notebook

    ########################
    # Register the modules #
    ########################
        
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

def start(port=5000):
    import sys
    path_to_notebook = sys.argv[1].rstrip('/')

    app = init_app(path_to_notebook)
    app.run(debug=True, port=port)

    notebook.save()
    print "Notebook saved!"
