"""
"""
from flask import Flask, url_for, render_template, request, session, redirect, g
from decorators import login_required
from base import app

def render_worksheet_list(args, pub, username):
    """
    Returns a rendered worksheet listing.

    INPUT:

    -  ``args`` - ctx.args where ctx is the dict passed
       into a resource's render method

    -  ``pub`` - boolean, True if this is a listing of
       public worksheets

    -  ``username`` - the user whose worksheets we are
       listing

    OUTPUT:

    a string
    """
    from sagenb.notebook.notebook import sort_worksheet_list
    typ = args['typ'] if 'typ' in args else 'active'
    search = unicode_str(args['search']) if 'search' in args else None
    sort = args['sort'] if 'sort' in args else 'last_edited'
    reverse = (args['reverse'] == 'True') if 'reverse' in args else False

    if not pub:
        worksheets = app.notebook.worksheet_list_for_user(username, typ=typ, sort=sort,
                                                          search=search, reverse=reverse)

    else:
        worksheets = app.notebook.worksheet_list_for_public(username, sort=sort,
                                                            search=search, reverse=reverse)

    worksheet_filenames = [x.filename() for x in worksheets]

    if pub and (not username or username == tuple([])):
        username = 'pub'

    accounts = app.notebook.get_accounts()

    return render_template('html/worksheet_listing.html', **locals())


@app.route('/home/<username>/')
@login_required
def home(username):
    if not app.notebook.user_is_admin(username) and username != g.username:
        #XXX: Put this into a template
        return "User '%s' does not have permission to view the home page of '%s'."%(g.username,
                                                                                    username)
    else:
        return render_worksheet_list(request.args, pub=False, username=g.username)

@app.route('/home/')
@login_required
def bare_home():
    return redirect(url_for('home', username=g.username))

###########
# Folders #
###########

def get_worksheets_from_request():
    U = app.notebook.user(g.username)
    
    if 'filename' in request.form:
        filenames = [request.form['filename']]
    elif 'filenames' in request.form:
        sep = request.form['sep']
        filenames = [x for x in request.form['filenames'].split(sep) if x.strip()]
    else:
        filenames = []

    worksheets = []
    for filename in filenames:
        W = app.notebook.get_worksheet_with_filename(filename)
        if W.owner() != g.username:
            continue
        worksheets.append(W)

    return worksheets

@app.route('/send_to_trash', methods=['POST'])
@login_required
def send_worksheet_to_trash():
    for W in get_worksheets_from_request():
        W.move_to_trash(g.username)
    return ''

@app.route('/send_to_archive', methods=['POST'])
@login_required
def send_worksheet_to_archive():
    for W in get_worksheets_from_request():
        W.move_to_archive(g.username)
    return ''

@app.route('/send_to_active', methods=['POST'])
@login_required
def send_worksheet_to_active():
    for W in get_worksheets_from_request():
        W.set_active(g.username)
    return ''

@app.route('/send_to_stop', methods=['POST'])
@login_required
def send_worksheet_to_stop():
    for W in get_worksheets_from_request():
        W.quit()
    return ''

@app.route('/emptytrash', methods=['POST'])
def empty_trash():
    app.notebook.empty_trash(g.username)
    if 'referer' in request.headers:
        return redirect(request.headers['referer'])
    else:
        return redirect(url_for('home', typ='trash'))
                       

#####################
# Public Worksheets #
#####################
@app.route('/pub/')
def pub():
    return render_worksheet_list(request.args, pub=True, username='')

@app.route('/home/pub/<id>/')
def public_worksheet(id):
    filename = 'pub' + '/' + id
    return app.notebook.html(worksheet_filename=filename)
