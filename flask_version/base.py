#!/usr/bin/env python
import os, time
from functools import wraps, partial
from flask import Flask, url_for, render_template, request, session, redirect, g, make_response
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
        

app = SageNBFlask(__name__)
app.secret_key = os.urandom(24)

#XXX: This should probably be made able to put in a "central" place
#with all of the jsmath stuff rather than just a global variable here.
from sagenb.misc.misc import is_package_installed
jsmath_image_fonts = is_package_installed("jsmath-image-fonts")

#############
# Main Page #
#############
@app.route('/')
def index():
    if 'username' in session:
        response = redirect(url_for('home', username=session['username']))
        if 'remember' in request.args:
            response.set_cookie('nb_session_%s'%app.notebook.port,
                                expires=(time.time() + 60 * 60 * 24 * 14))
        else:
            response.set_cookie('nb_session_%s'%app.notebook.port)
        response.set_cookie('cookie_test_%s'%app.notebook.port, expires=1)
        return response
        
    from authentication import login
    
    if app.one_time_token != -1 and 'one_time_token' in request.args:
        if request.args['one_time_token'] == app.one_time_token:
            session['username'] = 'admin' 
            session.modified = True
            app.one_time_token = -1 
            return index()
            
    return login()

######################
# Dynamic Javascript #
######################
@app.route('/javascript/sage/main.js')
def main_js():
    from sagenb.notebook.js import javascript
    response = make_response(javascript())
    response.headers['Content-Type'] = 'text/javascript; charset=utf-8'
    return response

@app.route('/javascript/sage/jsmath.js')
def jsmath_js():
    from sagenb.misc.misc import jsmath_macros
    response = make_response(render_template('js/jsmath.js', jsmath_macros=jsmath_macros,
                                             jsmath_image_fonts=jsmath_image_fonts))
    response.headers['Content-Type'] = 'text/javascript; charset=utf-8'
    return response

@app.route('/javascript/sage/keyboard/<browser_os>')
def keyboard_js(browser_os):
    from sagenb.notebook.keyboards import get_keyboard
    response = make_response(get_keyboard(browser_os))
    response.headers['Content-Type'] = 'text/javascript; charset=utf-8'
    return response


################
# View imports #
################
import authentication
import doc
import worksheet_listing
import worksheet

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
    
    save_interval = app.notebook.conf()['save_interval']
    idle_interval = app.notebook.conf()['idle_check_interval']
    last_save_time = walltime()
    last_idle_time = walltime()

def notebook_save_check():
    global last_save_time
    from sagenb.misc.misc import walltime

    t = walltime()
    if t > last_save_time + save_interval:
        app.notebook.save()
        last_save_time = t

def notebook_idle_check():
    global last_idle_time
    from sagenb.misc.misc import walltime

    t = walltime()
    if t > last_idle_time + idle_interval:
        app.notebook.update_worksheet_processes()
        app.notebook.quit_idle_worksheet_processes()
        last_idle_time = t

def notebook_updates():
    notebook_save_check()
    notebook_idle_check()



#CLEAN THIS UP!
def start():
    import sys
    path_to_notebook = sys.argv[1].rstrip('/')
    port = 5000
    
    #############
    # OLD STUFF #
    #############
    import sagenb.notebook.notebook
    sagenb.notebook.notebook.JSMATH = True
    import sagenb.notebook.notebook as notebook

    app.notebook = notebook.load_notebook(path_to_notebook,interface="localhost",port=port,secure=False)
    SAGETEX_PATH = ""
    OPEN_MODE = False
    SID_COOKIE = str(hash(path_to_notebook))
    DIR = path_to_notebook
    init_updates()

    app.run(debug=True, port=port)

    app.notebook.save()
    print "Notebook saved!"
