"""
"""
import os
import urllib, urlparse
from flask import Module, url_for, render_template, request, session, redirect, g, current_app
from decorators import login_required, guest_or_login_required, with_lock
from flaskext.babel import Babel, gettext, ngettext, lazy_gettext
_ = gettext

worksheet_listing = Module('flask_version.worksheet_listing')

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
    from sagenb.misc.misc import unicode_str, SAGE_VERSION
    from sagenb.notebook.pagination import Paginator

    typ = args['typ'] if 'typ' in args else 'active'
    search = unicode_str(args['search']) if 'search' in args else None
    sort = args['sort'] if 'sort' in args else 'last_edited'
    reverse = (args['reverse'] == 'True') if 'reverse' in args else False
    page = 1
    if 'page' in args:
        try:
            page = int(args['page'])
        except ValueError as E:
            print "Error improper page input", E

    try:
        if not pub:
            worksheets = g.notebook.worksheet_list_for_user(username, typ=typ, sort=sort,
                                                              search=search, reverse=reverse)
        else:
            worksheets = g.notebook.worksheet_list_for_public(username, sort=sort,
                                                                search=search, reverse=reverse)
    except ValueError as E:
        # for example, the sort key was not valid
        print "Error displaying worksheet listing: ", E
        return current_app.message(_("Error displaying worksheet listing."))

    paginator = Paginator(worksheets, 25) #25 is number of items per page, change this value to change the number of objects per page.

    try:
        pages = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        pages = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        pages = paginator.page(paginator.num_pages)

    worksheets = pages.object_list

    worksheet_filenames = [x.filename() for x in worksheets]

    if pub and (not username or username == tuple([])):
        username = 'pub'

    accounts = g.notebook.user_manager().get_accounts()
    sage_version = SAGE_VERSION
    return render_template('html/worksheet_listing.html', **locals())

@worksheet_listing.route('/home/<username>/')
@login_required
def home(username):
    if not g.notebook.user_manager().user_is_admin(g.username) and username != g.username:
        #XXX: i18n
        return current_app.message("User '%s' does not have permission to view the home page of '%s'."%(g.username, username))
    else:
        return render_worksheet_list(request.args, pub=False, username=username)

@worksheet_listing.route('/home/')
@login_required
def bare_home():
    return redirect(url_for('home', username=g.username))

###########
# Folders #
###########

def get_worksheets_from_request():
    U = g.notebook.user_manager().user(g.username)
    
    if 'filename' in request.form:
        filenames = [request.form['filename']]
    elif 'filenames' in request.form:
        import json
        filenames = json.loads(request.form['filenames'])
    else:
        filenames = []
    worksheets = []
    for filename in filenames:
        W = g.notebook.get_worksheet_with_filename(filename)
        if W.owner() != g.username:
            # TODO BUG: if trying to stop a shared worksheet, this check means that 
            # only the owner can stop from the worksheet listing (using /send_to_stop), but any 
            # shared person can stop the worksheet by quitting it.
            continue
        worksheets.append(W)

    return worksheets

@worksheet_listing.route('/send_to_trash', methods=['POST'])
@login_required
def send_worksheet_to_trash():
    for W in get_worksheets_from_request():
        W.move_to_trash(g.username)
    return ''

@worksheet_listing.route('/send_to_archive', methods=['POST'])
@login_required
def send_worksheet_to_archive():
    for W in get_worksheets_from_request():
        W.move_to_archive(g.username)
    return ''

@worksheet_listing.route('/send_to_active', methods=['POST'])
@login_required
def send_worksheet_to_active():
    for W in get_worksheets_from_request():
        W.set_active(g.username)
    return ''

@worksheet_listing.route('/send_to_stop', methods=['POST'])
@login_required
def send_worksheet_to_stop():
    for W in get_worksheets_from_request():
        W.quit()
    return ''

@worksheet_listing.route('/emptytrash', methods=['POST'])
@login_required
def empty_trash():
    g.notebook.empty_trash(g.username)
    if 'referer' in request.headers:
        return redirect(request.headers['referer'])
    else:
        return redirect(url_for('home', typ='trash'))
                       

#####################
# Public Worksheets #
#####################
@worksheet_listing.route('/pub/')
@guest_or_login_required
def pub():
    return render_worksheet_list(request.args, pub=True, username=g.username)

@worksheet_listing.route('/home/pub/<id>/')
@guest_or_login_required
def public_worksheet(id):
    from worksheet import pub_worksheet
    filename = 'pub/%s'%id
    if g.notebook.conf()['pub_interact']:
        try:
            original_worksheet = g.notebook.get_worksheet_with_filename(filename)
        except KeyError:
            return _("Requested public worksheet does not exist"), 404
        worksheet = pub_worksheet(original_worksheet)
        
        owner = worksheet.owner()
        worksheet.set_owner('pub')
        s = g.notebook.html(worksheet_filename=worksheet.filename(),
                            username=g.username)
        worksheet.set_owner(owner)
    else:
        s = g.notebook.html(worksheet_filename=filename, username = g.username)
    return s

@worksheet_listing.route('/home/pub/<id>/download/<path:title>')
def public_worksheet_download(id, title):
    from worksheet import unconditional_download
    worksheet_filename =  "pub" + "/" + id
    try:
        worksheet = g.notebook.get_worksheet_with_filename(worksheet_filename)
    except KeyError:
        return current_app.message(_("You do not have permission to access this worksheet"))
    return unconditional_download(worksheet, title)

@worksheet_listing.route('/home/pub/<id>/cells/<path:filename>')
def public_worksheet_cells(id, filename):
    worksheet_filename =  "pub" + "/" + id
    try:
        worksheet = g.notebook.get_worksheet_with_filename(worksheet_filename)
    except KeyError:
        return current_app.message("You do not have permission to access this worksheet") #XXX: i18n
    from flask.helpers import send_from_directory
    return send_from_directory(worksheet.cells_directory(), filename)

#######################
# Download Worksheets #
#######################
@worksheet_listing.route('/download_worksheets.zip')
@login_required
def download_worksheets():
    from sagenb.misc.misc import walltime, tmp_filename
    
    t = walltime()
    print "Starting zipping a group of worksheets in a separate thread..."
    zip_filename = tmp_filename() + ".zip"

    # child
    worksheet_names = set()
    if 'filenames' in request.values:
        import json
        filenames = json.loads(request.values['filenames'])
        worksheets = [g.notebook.get_worksheet_with_filename(x.strip())
                      for x in filenames if len(x.strip()) > 0]
    else:
        worksheets = g.notebook.worksheet_list_for_user(g.username)

    import zipfile
    zip = zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_STORED)
    for worksheet in worksheets:
        sws_filename = tmp_filename() + '.sws'
        g.notebook.export_worksheet(worksheet.filename(), sws_filename)
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

    response = current_app.make_response(r)
    response.headers['Content-Type'] = 'application/zip'
    return response


#############
# Uploading #
#############
@worksheet_listing.route('/upload')
@login_required
def upload():
    return render_template(os.path.join('html', 'upload.html'),
                           username=g.username)

class RetrieveError(Exception):
    """
    Use this in my_urlretrieve below, and when calling that function, do:

    try:
        my_urlretrive(...)
    except RetrieveError as err:
        return current_app.message(str(err))

    This allows us to factor out all the error message handling into
    my_urlretrieve.
    """
    pass

def my_urlretrieve(url, *args, **kwargs):
    """
    Call urllib.urlretrieve and give friendly error messages depending
    on the result. If successful, return exactly what urllib.urlretrieve
    would. Arguments are exactly the same as urlretrieve, except that
    you can also specify a ``backlinks`` keyword used in the error
    message.

    Raises RetrieveError when an error occurs for which we can figure
    out a sensible error message.
    """
    try:
        backlinks = kwargs.pop('backlinks')
    except KeyError:
        backlinks = ''
    try:
        return urllib.urlretrieve(url, *args, **kwargs)
    except IOError as err:
        if err.strerror == 'unknown url type' and err.filename == 'https':
            raise RetrieveError(_("This Sage notebook is not configured to load worksheets from 'https' URLs. Try a different URL or download the worksheet and upload it directly from your computer.\n%(backlinks)s",backlinks=backlinks))
        else:
            raise

def parse_link_rel(url, fn):
    """
    Read through html file ``fn`` downloaded from ``url``, looking for a
    link tag of the form:

    <link rel="alternate"
          type="application/sage"
          title="currently ignored"
          href=".../example.sws" />

    This function reads ``fn`` looking for such tags and returns a list
    of dictionaries of the form

    {'title': from title field in link, 'url': absolute URL to .sws file}

    for the corresponding ``.sws`` files. Naturally if there are no
    appropriate link tags found, the returned list is empty. If the HTML
    parser raises an HTMLParseError, we simply return an empty list.
    """
    from HTMLParser import HTMLParser
    class GetLinkRelWorksheets(HTMLParser):
        def __init__(self):
            HTMLParser.__init__(self)
            self.worksheets = []

        def handle_starttag(self, tag, attrs):
            if (tag == 'link' and
                ('rel', 'alternate') in attrs and
                ('type', 'application/sage') in attrs):
                self.worksheets.append({'title': [_ for _ in attrs if _[0] == 'title'][0][1],
                                          'url': [_ for _ in attrs if _[0] == 'href'][0][1]})

    parser = GetLinkRelWorksheets()
    with open(fn) as f:
        try:
            parser.feed(f.read())
        except HTMLParseError:
            return []

    ret = []
    for d in parser.worksheets:
        sws = d['url']
        # is that link a relative URL?
        if not urlparse.urlparse(sws).netloc:
            # unquote-then-quote to avoid turning %20 into %2520, etc
            ret.append({'url': urlparse.urljoin(url, urllib.quote(urllib.unquote(sws))),
                        'title': d['title']})
        else:
            ret.append({'url': sws, 'title': d['title']})
    return ret

@worksheet_listing.route('/upload_worksheet', methods=['GET', 'POST'])
@login_required
def upload_worksheet():
    from sage.misc.misc import tmp_filename, tmp_dir
    from werkzeug.utils import secure_filename
    import zipfile

    backlinks = _("""Return to <a href="/upload" title="Upload a worksheet"><strong>Upload File</strong></a>.""")

    url = request.values['url'].strip()
    dir = ''
    if url != '':
        #Downloading a file from the internet
        # The file will be downloaded from the internet and saved
        # to a temporary file with the same extension
        path = urlparse.urlparse(url).path
        extension = os.path.splitext(path)[1].lower()
        if extension not in ["", ".txt", ".sws", ".zip", ".html", ".rst"]:
            # Or shall we try to import the document as an sws when in doubt?
            return current_app.message("Unknown worksheet extension: %s. %s" % (extension, backlinks))
        filename = tmp_filename()+extension
        try:
            import re
            matches = re.match("file://(?:localhost)?(/.+)", url)
            if matches:
                if g.notebook.interface != 'localhost':
                    return current_app.message(_("Unable to load file URL's when not running on localhost.\n%(backlinks)s",backlinks=backlinks))

                import shutil
                shutil.copy(matches.group(1),filename)
            else:
                my_urlretrieve(url, filename, backlinks=backlinks)

        except RetrieveError as err:
            return current_app.message(str(err))

    else:
        #Uploading a file from the user's computer
        dir = tmp_dir()
        file = request.files['file']
        if file.filename is None:
            return current_app.message(_("Please specify a worksheet to load.\n%(backlinks)s",backlinks=backlinks))

        filename = secure_filename(file.filename)
        if len(filename)==0:
            return current_app.message(_("Invalid filename.\n%(backlinks)s",backlinks=backlinks))

        filename = os.path.join(dir, filename)
        file.save(filename)

    new_name = request.values.get('name', None)

    try:
        try:
            if filename.endswith('.zip'):
                # Extract all the .sws files from a zip file.
                zip_file = zipfile.ZipFile(filename)
                for subfilename in zip_file.namelist():
                    prefix, extension = os.path.splitext(subfilename)
                    if extension in ['.sws', '.html', '.txt', '.rst'] :
                        tmpfilename = os.path.join(dir, "tmp" + extension)
                        try:
                            tmpfilename = zip_file.extract(subfilename, tmpfilename)
                        except AttributeError:
                            open(tmpfilename, 'w').write(zip_file.read(subfilename))
                        W = g.notebook.import_worksheet(tmpfilename, g.username)
                        if new_name:
                            W.set_name("%s - %s" % (new_name, W.name()))
                    else:
                        print "Unknown extension, file %s is ignored" % subfilename
                return redirect(url_for('home', username=g.username))

            else:
                if url and extension in ['', '.html']:
                    linked_sws = parse_link_rel(url, filename)
                    if linked_sws:
                        # just grab 1st URL; perhaps later add interface for
                        # downloading multiple linked .sws
                        try:
                            filename = my_urlretrieve(linked_sws[0]['url'], backlinks=backlinks)[0]
                            print 'Importing {0}, linked to from {1}'.format(linked_sws[0]['url'], url)
                        except RetrieveError as err:
                            return current_app.message(str(err))
                W = g.notebook.import_worksheet(filename, g.username)
        except Exception, msg:
            print 'error uploading worksheet', msg
            s = _('There was an error uploading the worksheet.  It could be an old unsupported format or worse.  If you desperately need its contents contact the <a href="http://groups.google.com/group/sage-support">sage-support group</a> and post a link to your worksheet.  Alternatively, an sws file is just a bzip2 tarball; take a look inside!\n%(backlinks)s', backlinks=backlinks)
            return current_app.message(s, url_for('home', username=g.username))
        finally:
            # Clean up the temporarily uploaded filename.
            os.unlink(filename)
            # if a temp directory was created, we delete it now.
            if dir:
                import shutil
                shutil.rmtree(dir)

    except ValueError, msg:
        s = _("Error uploading worksheet '%(msg)s'.%(backlinks)s", msg=msg, backlinks=backlinks)
        return current_app.message(s, url_for('home', username=g.username))

    if new_name:
        W.set_name(new_name)

    from worksheet import url_for_worksheet
    return redirect(url_for_worksheet(W))
