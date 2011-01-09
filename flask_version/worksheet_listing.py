"""
"""
import os
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
    from sagenb.misc.misc import unicode_str
    
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
        #XXX: i18n
        return app.message("User '%s' does not have permission to view the home page of '%s'."%(g.username, username))
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
@login_required
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

#######################
# Download Worksheets #
#######################
@app.route('/download_worksheets.zip')
@login_required
def download_worksheets():
    from sagenb.misc.misc import walltime, tmp_filename
    
    t = walltime()
    print "Starting zipping a group of worksheets in a separate thread..."
    zip_filename = tmp_filename() + ".zip"

    # child
    worksheet_names = set()
    if 'filenames' in request.values:
        sep = request.values['sep']
        worksheets = [app.notebook.get_worksheet_with_filename(x.strip())
                      for x in request.values['filenames'].split(sep)
                      if len(x.strip()) > 0]
    else:
        worksheets = app.notebook.worksheet_list_for_user(g.username)

    import zipfile
    zip = zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_STORED)
    for worksheet in worksheets:
        sws_filename = tmp_filename() + '.sws'
        app.notebook.export_worksheet(worksheet.filename(), sws_filename)
        entry_name = worksheet.name()
        if entry_name in worksheet_names:
            i = 2
            while ("%s_%s" % (entry_name, i)) in worksheet_names:
                i += 1
            entry_name = "%s_%s" % (entry_name, i)
        zip.write(sws_filename, entry_name + ".sws")
        os.unlink(sws_filename)
    zip.close()
    r = open(zip_filename, 'rb').read()
    os.unlink(zip_filename)
    print "Finished zipping %s worksheets (%s seconds)"%(len(worksheets), walltime(t))

    response = app.make_response(r)
    response.headers['Content-Type'] = 'application/zip'
    return response


#############
# Uploading #
#############
@app.route('/upload')
@login_required
def upload():
    return render_template(os.path.join('html', 'upload.html'),
                           username=g.username)

@app.route('/upload_worksheet', methods=['GET', 'POST'])
@login_required
def upload_worksheet():
    from sage.misc.misc import tmp_filename, tmp_dir
    from werkzeug import secure_filename
    import zipfile
    
    #XXX: i18n
    backlinks = """ Return to <a href="/upload" title="Upload a worksheet"><strong>Upload File</strong></a>."""

    url = request.values['url'].strip()
    dir = ''
    if url:
        #Downloading a file from the internet
        import urllib
        filename = tmp_filename() + ('.zip' if url.endswith('.zip') else '.sws')
        urllib.urlretrieve(url, filename)
    else:
        #Uploading a file from the user's computer
        dir = tmp_dir()
        file = request.files['file']
        if file.filename == '':
            return app.message("Please specify a worksheet to load.%s" % backlinks)

        filename = secure_filename(file.filename)
        filename = os.path.join(dir, filename)
        file.save(filename)

    new_name = request.values.get('name', None)

    try:
        try:
            if filename.endswith('.zip'):
                # Extract all the .sws files from a zip file.
                zip_file = zipfile.ZipFile(filename)
                sws_file = os.path.join(dir, "tmp.sws")
                for sws in zip_file.namelist():
                    if sws.endswith('.sws'):
                        open(sws_file, 'w').write(zip_file.read(sws)) # 2.6 zip_file.extract(sws, sws_file)
                        W = app.notebook.import_worksheet(sws_file, g.username)
                        if new_name:
                            W.set_name("%s - %s" % (new_name, W.name()))
                return redirect(url_for('home', username=g.username))

            else:
                W = app.notebook.import_worksheet(filename, g.username)

        except Exception, msg:
            s = 'There was an error uploading the worksheet.  It could be an old unsupported format or worse.  If you desperately need its contents contact the <a href="http://groups.google.com/group/sage-support">sage-support group</a> and post a link to your worksheet.  Alternatively, an sws file is just a bzip2 tarball; take a look inside!%s' % backlinks
            return app.message(s, url_for('home', username=g.username))
        finally:
            # Clean up the temporarily uploaded filename.
            os.unlink(filename)
            # if a temp directory was created, we delete it now.
            if dir:
                import shutil
                shutil.rmtree(dir)

    except ValueError, msg:
        s = "Error uploading worksheet '%s'.%s" % (msg, backlinks)
        return app.message(s, url_for('home', username=g.username))

    if new_name:
        W.set_name(new_name)

    from worksheet import url_for_worksheet
    return redirect(url_for_worksheet(W))
        
