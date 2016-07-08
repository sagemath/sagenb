from __future__ import absolute_import
import re
import os
import threading
import collections
from functools import wraps
from flask import Module, make_response, url_for, render_template, request, session, redirect, g, current_app
from .decorators import login_required, with_lock
from collections import defaultdict
from werkzeug.utils import secure_filename
from flask.ext.babel import Babel, gettext, ngettext, lazy_gettext
_ = gettext

from sagenb.notebook.interact import INTERACT_UPDATE_PREFIX
from sagenb.notebook.misc import encode_response

ws = Module('sagenb.flask_version.worksheet')
worksheet_locks = defaultdict(threading.Lock)

def worksheet_view(f):
    """
    The `username` in the wrapper function is the username in the URL to the worksheet, which normally
    is the owner of the worksheet.  Don't confuse this with `g.username`, the actual username of the
    user looking at the worksheet.
    """
    @login_required
    @wraps(f)
    def wrapper(username, id, **kwds):
        worksheet_filename = username + "/" + id
        try:
            worksheet = kwds['worksheet'] = g.notebook.get_worksheet_with_filename(worksheet_filename)
        except KeyError:
            return current_app.message(_("You do not have permission to access this worksheet"), username=g.username)

        with worksheet_locks[worksheet]:
            owner = worksheet.owner()

            if owner != '_sage_' and g.username != owner:
                if not worksheet.is_published():
                    if (not g.username in worksheet.collaborators() and
                        not g.notebook.user_manager().user_is_admin(g.username)):
                        return current_app.message(_("You do not have permission to access this worksheet"), username=g.username)

            if not worksheet.is_published():
                worksheet.set_active(g.username)

            #This was in twist.Worksheet.childFactory
            from .base import notebook_updates
            notebook_updates()

            return f(username, id, **kwds)

    return wrapper

def url_for_worksheet(worksheet):
    """
    Returns the url for a given worksheet.
    """
    return url_for('worksheet.worksheet', username=worksheet.owner(),
                   id=worksheet.filename_without_owner())


def get_cell_id():
    """
    Returns the cell ID from the request.

    We cast the incoming cell ID to an integer, if it's possible.
    Otherwise, we treat it as a string.
    """
    try:
        return int(request.values['id'])
    except ValueError:
        return request.values['id']

##############################
# Views
##############################
@ws.route('/new_worksheet')
@login_required
def new_worksheet():
    if g.notebook.readonly_user(g.username):
        return current_app.message(_("Account is in read-only mode"), cont=url_for('worksheet_listing.home', username=g.username))

    W = g.notebook.create_new_worksheet(gettext("Untitled"), g.username)
    return redirect(url_for_worksheet(W))

@ws.route('/home/<username>/<id>/')
@worksheet_view
def worksheet(username, id, worksheet=None):
    """
    username is the owner of the worksheet
    id is the id of the worksheet
    """
    # /home/pub/* is handled in worksheet_listing.py
    assert worksheet is not None
    worksheet.sage()
    s = g.notebook.html(worksheet_filename=worksheet.filename(),
                        username=g.username)
    return s

published_commands_allowed = set(['alive', 'cells', 'cell_update',
                          'data', 'download', 'edit_published_page', 'eval',
                          'quit_sage', 'rate', 'rating_info', 'new_cell_before',
                          'new_cell_after', 'introspect', 'delete_all_output',
                          'copy', 'restart_sage', 'jsmol'])

readonly_commands_allowed = set(['alive', 'cells', 'data', 'datafile', 'download', 'quit_sage', 'rating_info', 'delete_all_output', 'jsmol'])

def worksheet_command(target, **route_kwds):
    if 'methods' not in route_kwds:
        route_kwds['methods'] = ['GET', 'POST']

    def decorator(f):
        @ws.route('/home/<username>/<id>/' + target, **route_kwds)
        @worksheet_view
        @wraps(f)
        def wrapper(*args, **kwds):
            #We remove the first two arguments corresponding to the
            #username and the worksheet id
            username_id = args[:2]
            args = args[2:]

            #####################
            # Public worksheets #
            #####################
            #_sage_ is used by live docs and published interacts
            if username_id and username_id[0] in ['_sage_']:
                if target.split('/')[0] not in published_commands_allowed:
                    raise NotImplementedError("User _sage_ can not access URL %s"%target)
            if g.notebook.readonly_user(g.username):
                if target.split('/')[0] not in readonly_commands_allowed:
                    return current_app.message(_("Account is in read-only mode"), cont=url_for('worksheet_listing.home', username=g.username))

            #Make worksheet a non-keyword argument appearing before the
            #other non-keyword arguments.
            worksheet = kwds.pop('worksheet', None)
            if worksheet is not None:
                args = (worksheet,) + args

            return f(*args, **kwds)

        #This function shares some functionality with url_for_worksheet.
        #Maybe we can refactor this some?
        def wc_url_for(worksheet, *args, **kwds):
            kwds['username'] = g.username
            kwds['id'] = worksheet.filename_without_owner()
            return url_for(f.__name__, *args, **kwds)

        wrapper.url_for = wc_url_for

        return wrapper
    return decorator


@worksheet_command('rename')
def worksheet_rename(worksheet):
    worksheet.set_name(request.values['name'])
    return 'done'

@worksheet_command('alive')
def worksheet_alive(worksheet):
    return str(worksheet.state_number())

@worksheet_command('system/<system>')
def worksheet_system(worksheet, system):
    worksheet.set_system(system)
    return 'success'

@worksheet_command('pretty_print/<enable>')
def worksheet_pretty_print(worksheet, enable):
    worksheet.set_pretty_print(enable)
    return 'success'

@worksheet_command('live_3D/<enable>')
def worksheet_live_3D(worksheet, enable):
    if enable == 'true':
        worksheet.set_live_3D(True)
    else:
        worksheet.set_live_3D(False)
    return 'success'


@worksheet_command('conf')
def worksheet_conf(worksheet):
    return str(worksheet.conf())


########################################################
# Save a worksheet
########################################################

@worksheet_command('save')
def worksheet_save(worksheet):
    """
    Save the contents of a worksheet after editing it in plain-text
    edit mode.
    """
    if 'button_save' in request.form:
        E = request.values['textfield']
        worksheet.edit_save(E)
        worksheet.record_edit(g.username)
    return redirect(url_for_worksheet(worksheet))

@worksheet_command('save_snapshot')
def worksheet_save_snapshot(worksheet):
    """Save a snapshot of a worksheet."""
    worksheet.save_snapshot(g.username)
    return 'saved'

@worksheet_command('save_and_quit')
def worksheet_save_and_quit(worksheet):
    """Save a snapshot of a worksheet then quit it. """
    worksheet.save_snapshot(g.username)
    worksheet.quit()
    return 'saved'

#XXX: Redundant due to the above?
@worksheet_command('save_and_close')
def worksheet_save_and_close(worksheet):
    """Save a snapshot of a worksheet then quit it. """
    worksheet.save_snapshot(g.username)
    worksheet.quit()
    return 'saved'

@worksheet_command('discard_and_quit')
def worksheet_discard_and_quit(worksheet):
    """Quit the worksheet, discarding any changes."""
    worksheet.revert_to_last_saved_state()
    worksheet.quit()
    return 'saved' #XXX: Should this really be saved?

@worksheet_command('revert_to_last_saved_state')
def worksheet_revert_to_last_saved_state(worksheet):
    worksheet.revert_to_last_saved_state()
    return 'reverted'

########################################################
# Used in refreshing the cell list
########################################################
@worksheet_command('cell_list')
def worksheet_cell_list(worksheet):
    """
    Return the state number and the HTML for the main body of the
    worksheet, which consists of a list of cells.
    """
    r = {}
    r['state_number'] = worksheet.state_number()
    # TODO: Send and actually use the body's HTML.
    r['html_cell_list'] = ''
    #r['html_cell_list'] = W.html_cell_list()

    return encode_response(r)

########################################################
# Set output type of a cell
########################################################
@worksheet_command('set_cell_output_type')
def worksheet_set_cell_output_type(worksheet):
    """
    Set the output type of the cell.

    This enables the type of output cell, such as to allowing wrapping
    for output that is very long.
    """
    id = get_cell_id()
    type = request.values['type']
    worksheet.get_cell_with_id(id).set_cell_output_type(type)
    return ''

########################################################
#Cell creation
########################################################
from sagenb.misc.misc import unicode_str


@worksheet_command('new_cell_before')
def worksheet_new_cell_before(worksheet):
    """Add a new cell before a given cell."""
    r = {}
    r['id'] =  id = get_cell_id()
    input = unicode_str(request.values.get('input', ''))
    cell = worksheet.new_cell_before(id, input=input)
    worksheet.increase_state_number()

    r['new_id'] = cell.id()
    r['new_html'] = cell.html(div_wrap=False)

    return encode_response(r)

@worksheet_command('new_text_cell_before')
def worksheet_new_text_cell_before(worksheet):
    """Add a new text cell before a given cell."""
    r = {}
    r['id'] = id = get_cell_id()
    input = unicode_str(request.values.get('input', ''))
    cell = worksheet.new_text_cell_before(id, input=input)
    worksheet.increase_state_number()

    r['new_id'] = cell.id()
    r['new_html'] = cell.html(editing=True)

    # XXX: Does editing correspond to TinyMCE?  If so, we should try
    # to centralize that code.
    return encode_response(r)


@worksheet_command('new_cell_after')
def worksheet_new_cell_after(worksheet):
    """Add a new cell after a given cell."""
    r = {}
    r['id'] = id = get_cell_id()
    input = unicode_str(request.values.get('input', ''))
    cell = worksheet.new_cell_after(id, input=input)
    worksheet.increase_state_number()

    r['new_id'] = cell.id()
    r['new_html'] = cell.html(div_wrap=True)

    return encode_response(r)

@worksheet_command('new_text_cell_after')
def worksheet_new_text_cell_after(worksheet):
    """Add a new text cell after a given cell."""
    r = {}
    r['id'] = id = get_cell_id()
    input = unicode_str(request.values.get('input', ''))
    cell = worksheet.new_text_cell_after(id, input=input)
    worksheet.increase_state_number()

    r['new_id'] = cell.id()
    r['new_html'] = cell.html(editing=True)

    # XXX: Does editing correspond to TinyMCE?  If so, we should try
    # to centralize that code.
    return encode_response(r)

########################################################
# Cell deletion
########################################################

@worksheet_command('delete_cell')
def worksheet_delete_cell(worksheet):
    """
    Deletes a worksheet cell, unless there's only one compute cell
    left.  This allows functions which evaluate relative to existing
    cells, e.g., inserting a new cell, to continue to work.
    """
    r = {}
    r['id'] = id = get_cell_id()
    if len(worksheet.compute_cell_id_list()) <= 1:
        r['command'] = 'ignore'
    else:
        prev_id = worksheet.delete_cell_with_id(id)
        r['command'] = 'delete'
        r['prev_id'] = worksheet.delete_cell_with_id(id)
        r['cell_id_list'] = worksheet.cell_id_list()

    return encode_response(r)

@worksheet_command('delete_cell_output')
def worksheet_delete_cell_output(worksheet):
    """Delete's a cell's output."""
    r = {}
    r['id'] = id = get_cell_id()
    worksheet.get_cell_with_id(id).delete_output()
    r['command'] = 'delete_output'

    return encode_response(r)

########################################################
# Evaluation and cell update
########################################################
@worksheet_command('eval')
def worksheet_eval(worksheet):
    """
    Evaluate a worksheet cell.

    If the request is not authorized (the requester did not enter the
    correct password for the given worksheet), then the request to
    evaluate or introspect the cell is ignored.

    If the cell contains either 1 or 2 question marks at the end (not
    on a comment line), then this is interpreted as a request for
    either introspection to the documentation of the function, or the
    documentation of the function and the source code of the function
    respectively.
    """
    from .base import notebook_updates

    r = {}

    r['id'] = id = get_cell_id()
    cell = worksheet.get_cell_with_id(id)
    public = worksheet.tags().get('_pub_', [False])[0] #this is set in pub_worksheet

    if public and not cell.is_interactive_cell():
        r['command'] = 'error'
        r['message'] = 'Cannot evaluate non-interactive public cell with ID %r.' % id
        return encode_response(r)

    worksheet.increase_state_number()

    if public:
        # Make public input cells read-only.
        input_text = cell.input_text()
    else:
        input_text = unicode_str(request.values.get('input', '')).replace('\r\n', '\n') #DOS

    # Handle an updated / recomputed interact.  TODO: JSON encode
    # the update data.
    if 'interact' in request.values:
        r['interact'] = 1
        input_text = INTERACT_UPDATE_PREFIX
        variable = request.values.get('variable', '')
        if variable!='':
            adapt_number = int(request.values.get('adapt_number', -1))
            value = request.values.get('value', '')
            input_text += "\n_interact_.update('%s', '%s', %s, _interact_.standard_b64decode('%s'), globals())" % (id, variable, adapt_number, value)

        if int(request.values.get('recompute', 0)):
            input_text += "\n_interact_.recompute('%s')" % id

    cell.set_input_text(input_text)

    if int(request.values.get('save_only', '0')):
        notebook_updates()
        return encode_response(r)
    elif int(request.values.get('text_only', '0')):
        notebook_updates()
        r['cell_html'] = cell.html()
        return encode_response(r)

    cell.evaluate(username=g.username)

    new_cell = int(request.values.get('newcell', 0)) #whether to insert a new cell or not
    if new_cell:
        new_cell = worksheet.new_cell_after(id)
        r['command'] = 'insert_cell'
        r['new_cell_id'] = new_cell.id()
        r['new_cell_html'] = new_cell.html(div_wrap=False)
    else:
        r['next_id'] = cell.next_compute_id()

    notebook_updates()

    return encode_response(r)


@worksheet_command('cell_update')
def worksheet_cell_update(worksheet):
    import time

    r = {}
    r['id'] = id = get_cell_id()

    # update the computation one "step".
    worksheet.check_comp()

    # now get latest status on our cell
    r['status'], cell = worksheet.check_cell(id)

    if r['status'] == 'd':
        r['new_input'] = cell.changed_input_text()
        r['output_html'] = cell.output_html()

        # Update the log.
        t = time.strftime('%Y-%m-%d at %H:%M',
                          time.localtime(time.time()))
        H = "Worksheet '%s' (%s)\n" % (worksheet.name(), t)
        H += cell.edit_text(ncols=g.notebook.HISTORY_NCOLS, prompts=False,
                            max_out=g.notebook.HISTORY_MAX_OUTPUT)
        g.notebook.add_to_user_history(H, g.username)
    else:
        r['new_input'] = ''
        r['output_html'] = ''

    if cell.interrupted():
        r['interrupted'] = 'true'
    else:
        r['interrupted'] = 'false'

    if 'Unhandled SIGSEGV' in cell.output_text(raw=True).split('\n'):
        r['interrupted'] = 'restart'
        print('Segmentation fault detected in output!')


    r['output'] = cell.output_text(html=True) + ' '
    r['output_wrapped'] = cell.output_text(g.notebook.conf()['word_wrap_cols'],
                                           html=True) + ' '
    r['introspect_html'] = cell.introspect_html()

    # Compute 'em, if we got 'em.
    worksheet.start_next_comp()

    return encode_response(r)


########################################################
# Cell introspection
########################################################
@worksheet_command('introspect')
def worksheet_introspect(worksheet):
    """
    Cell introspection. This is called when the user presses the tab
    key in the browser in order to introspect.
    """
    r = {}
    r['id'] = id = get_cell_id()

    if worksheet.tags().get('_pub_', [False])[0]: #tags set in pub_worksheet
        r['command'] = 'error'
        r['message'] = 'Cannot evaluate public cell introspection.'
        return encode_response(r)

    before_cursor = request.values.get('before_cursor', '')
    after_cursor = request.values.get('after_cursor', '')
    cell = worksheet.get_cell_with_id(id)
    cell.evaluate(introspect=[before_cursor, after_cursor])

    r['command'] = 'introspect'
    return encode_response(r)

########################################################
# Edit the entire worksheet
########################################################
@worksheet_command('edit')
def worksheet_edit(worksheet):
    """
    Return a window that allows the user to edit the text of the
    worksheet with the given filename.
    """
    return g.notebook.html_edit_window(worksheet, g.username)


########################################################
# Plain text log view of worksheet
########################################################
@worksheet_command('text')
def worksheet_text(worksheet):
    """
    Return a window that allows the user to edit the text of the
    worksheet with the given filename.
    """
    return g.notebook.html_plain_text_window(worksheet, g.username)

########################################################
# Copy a worksheet
########################################################
@worksheet_command('copy')
def worksheet_copy(worksheet):
    copy = g.notebook.copy_worksheet(worksheet, g.username)
    if 'no_load' in request.values:
        return ''
    else:
        return redirect(url_for_worksheet(copy))

########################################################
# Get a copy of a published worksheet and start editing it
########################################################
@worksheet_command('edit_published_page')
def worksheet_edit_published_page(worksheet):
    ## if user_type(self.username) == 'guest':
    ##     return current_app.message('You must <a href="/">login first</a> in order to edit this worksheet.')

    ws = worksheet.worksheet_that_was_published()
    if ws.owner() == g.username:
        W = ws
    else:
        W = g.notebook.copy_worksheet(worksheet, g.username)
        W.set_name(worksheet.name())

    return redirect(url_for_worksheet(W))


########################################################
# Collaborate with others
########################################################
@worksheet_command('share')
def worksheet_share(worksheet):
    return g.notebook.html_share(worksheet, g.username)

@worksheet_command('invite_collab')
def worksheet_invite_collab(worksheet):
    owner = worksheet.owner()
    id_number = worksheet.id_number()
    old_collaborators = set(worksheet.collaborators())
    collaborators = set([u.strip() for u in request.values.get('collaborators', '').split(',') if u!=owner])
    if len(collaborators-old_collaborators)>500:
        # to prevent abuse, you can't add more than 500 collaborators at a time
        return current_app.message(_("Error: can't add more than 500 collaborators at a time"), cont=url_for_worksheet(worksheet), username=g.username)
    worksheet.set_collaborators(collaborators)
    user_manager = g.notebook.user_manager()
    # add worksheet to new collaborators
    for u in collaborators-old_collaborators:
        try:
            user_manager.user(u).viewable_worksheets().add((owner, id_number))
        except (ValueError, LookupError):
            # user doesn't exist
            pass
    # remove worksheet from ex-collaborators
    for u in old_collaborators-collaborators:
        try:
            user_manager.user(u).viewable_worksheets().discard((owner, id_number))
        except (ValueError, LookupError):
            # user doesn't exist
            pass

    return redirect(url_for_worksheet(worksheet))

########################################################
# Revisions
########################################################
@worksheet_command('revisions')
def worksheet_revisions(worksheet):
    """
    Show a list of revisions of this worksheet.
    """
    if 'action' not in request.values:
        if 'rev' in request.values:
            return g.notebook.html_specific_revision(g.username, worksheet,
                                                       request.values['rev'])
        else:
            return g.notebook.html_worksheet_revision_list(g.username, worksheet)
    else:
        rev = request.values['rev']
        action = request.values['action']
        if action == 'revert':
            import bz2
            worksheet.save_snapshot(g.username)
            #XXX: Requires access to filesystem
            txt = bz2.decompress(open(worksheet.get_snapshot_text_filename(rev)).read())
            worksheet.delete_cells_directory()
            worksheet.edit_save(txt)
            return redirect(url_for_worksheet(worksheet))
        elif action == 'publish':
            import bz2
            W = g.notebook.publish_worksheet(worksheet, g.username)
            txt = bz2.decompress(open(worksheet.get_snapshot_text_filename(rev)).read())
            W.delete_cells_directory()
            W.edit_save(txt)
            return redirect(url_for_worksheet(W))
        else:
            return current_app.message(_('Error'), username=g.username)



########################################################
# Cell directories
########################################################
@worksheet_command('cells/<path:filename>')
def worksheet_cells(worksheet, filename):
    #XXX: This requires that the worker filesystem be accessible from
    #the server.
    from flask.helpers import send_from_directory
    return send_from_directory(worksheet.cells_directory(), filename)


########################################################
# Jmol/JSmol callback to read data files
########################################################
@worksheet_command('jsmol')
def worksheet_jsmol_data(worksheet):
    """
    Jmol/JSmol callback

    The jmol applet does not take the data inline, but calls back at
    this URI to get one or more base64-encoded data files.
    """
    # Defaults taken from upstream jsmol.php
    query = request.values.get('query', 
        "http://cactus.nci.nih.gov/chemical/structure/ethanol/file?format=sdf&get3d=True")
    call = request.values.get('call', u'getRawDataFromDatabase')
    database = request.values.get('database', '_')
    encoding = request.values.get('encoding', None)

    current_app.logger.debug('JSmol call:  %s', call)
    current_app.logger.debug('JSmol query: %s', query)
    if encoding == None:
        def encoder(x): 
            return x
    elif encoding == u'base64':
        import base64
        def encoder(x): 
            # JSmol expects the magic ';base64,' in front of output
            return ';base64,' + base64.encodestring(x)
    else:
        current_app.logger.error('Invalid JSmol encoding %s', encoding)
        return current_app.message(_('Invalid JSmol encoding: ' + str(encoding)), username=g.username)

    if call == u'getRawDataFromDatabase':
        # Annoyingly, JMol prepends the worksheet url (not: the
        # request url) to the query. Strip off:
        worksheet_url = request.base_url[:-len('/jsmol')]
        pattern = worksheet_url + '/cells/(?P<cell_id>[0-9]*)/(?P<filename>.*)'
        match = re.match(pattern, query)
        if match is None:
            current_app.logger.error('Invalid JSmol query %s, does not match %s', query, pattern)
            return current_app.message(_('Invalid JSmol query: ' + query), username=g.username)
        cell_id = match.group('cell_id')
        filename = match.group('filename')
        filename = filename.rsplit('?',1)[0] # appended query is only for cache busting
        filename = secure_filename(filename)   # never trust input
        filename = os.path.join(worksheet.cells_directory(), cell_id, filename)
        with open(filename, 'r') as f:
            data = f.read()
            response = make_response(encoder(data))
    else:
        current_app.logger.error('Invalid JSmol request %s', call)
        return current_app.message(_('Invalid JSmol request: ' + str(call)), username=g.username)

    # Taken from upstream jsmol.php
    is_binary = '.gz' in query
    # Non-standard Content-Type taken from upstream jsmol.php
    if is_binary:
        response.headers['Content-Type'] = 'Content-Type: text/plain; charset=x-user-defined';
    else:
        response.headers['Content-Type'] = 'Content-Type: application/json';
    return response


##############################################
# Data
##############################################
@worksheet_command('<path:filename>')
def worksheet_data_legacy(worksheet, filename):
    # adhering to old behavior, should be removed eventually
    return worksheet_data(worksheet, filename)

@worksheet_command('data/<path:filename>')
def worksheed_data_folder(worksheet,filename):
    # preferred way of accessing data
    return worksheet_data(worksheet, filename)

def worksheet_data(worksheet, filename):
    dir = os.path.abspath(worksheet.data_directory())
    if not os.path.exists(dir):
        return current_app.message(_('No data files'), username=g.username)
    else:
        from flask.helpers import send_from_directory
        return send_from_directory(worksheet.data_directory(), filename)

@worksheet_command('datafile')
def worksheet_datafile(worksheet):
    #XXX: This requires that the worker filesystem be accessible from
    #the server.
    dir = os.path.abspath(worksheet.data_directory())
    filename = request.values['name']
    if request.values.get('action', '') == 'delete':
        path = os.path.join(dir, filename)
        os.unlink(path)
        return current_app.message(_("Successfully deleted '%(filename)s'", filename=filename),
                                   cont=url_for_worksheet(worksheet), username=g.username)
    else:
        return g.notebook.html_download_or_delete_datafile(worksheet, g.username, filename)

@worksheet_command('savedatafile')
def worksheet_savedatafile(worksheet):
    filename = request.values['filename']
    if 'button_save' in request.values:
        text_field = request.values['textfield'] #XXX: Should this be text_field
        dest = os.path.join(worksheet.data_directory(), filename) #XXX: Requires access to filesystem
        if os.path.exists(dest):
            os.unlink(dest)
        open(dest, 'w').write(text_field)
    return g.notebook.html_download_or_delete_datafile(worksheet, g.username, filename)


@worksheet_command('link_datafile')
def worksheet_link_datafile(worksheet):
    target_worksheet_filename = request.values['target']
    data_filename = request.values['filename']
    src = os.path.abspath(os.path.join(
        worksheet.data_directory(), data_filename))
    target_ws =  g.notebook.get_worksheet_with_filename(target_worksheet_filename)
    target = os.path.abspath(os.path.join(
        target_ws.data_directory(), data_filename))
    if target_ws.owner() != g.username and not target_ws.is_collaborator(g.username):
        return current_app.message(_("illegal link attempt!"), worksheet_datafile.url_for(worksheet, name=data_filename), username=g.username)
    if os.path.exists(target):
        return current_app.message(_("The data filename already exists in other worksheet\nDelete the file in the other worksheet before creating a link."), worksheet_datafile.url_for(worksheet, name=data_filename), username=g.username)
    os.link(src,target)
    return redirect(worksheet_datafile.url_for(worksheet, name=data_filename))
    #return redirect(url_for_worksheet(target_ws) + '/datafile?name=%s'%data_filename) #XXX: Can we not hardcode this?

@worksheet_command('upload_data')
def worksheet_upload_data(worksheet):
    return g.notebook.html_upload_data_window(worksheet, g.username)

@worksheet_command('do_upload_data')
def worksheet_do_upload_data(worksheet):
    worksheet_url = url_for_worksheet(worksheet)
    upload_url = worksheet_upload_data.url_for(worksheet)

    backlinks = _(""" Return to <a href="%(upload_url)s" title="Upload or create a data file in a wide range of formats"><strong>Upload or Create Data File</strong></a> or <a href="%(worksheet_url)s" title="Interactively use the worksheet"><strong>%(worksheet_name)s</strong></a>.""", upload_url=upload_url, worksheet_url=worksheet_url, worksheet_name=worksheet.name())


    if 'file' not in request.files:
        return current_app.message(_('Error uploading file (missing field "file"). %(backlinks)s', backlinks=backlinks), worksheet_url, username=g.username)
    else:
        file = request.files['file']

    text_fields = ['url', 'new', 'name']
    for field in text_fields:
        if field not in request.values:
            return current_app.message(_('Error uploading file (missing %(field)s arg).%(backlinks)s', field=field, backlinks=backlinks), worksheet_url, username=g.username)


    name = request.values.get('name', '').strip()
    new_field = request.values.get('new', '').strip()
    url = request.values.get('url', '').strip()

    name = name or file.filename or new_field
    if url and not name:
        name = url.split('/')[-1]
    name = secure_filename(name)

    if not name:
        return current_app.message(_('Error uploading file (missing filename).%(backlinks)s', backlinks=backlinks), worksheet_url)

    if url != '':
        import urllib2
        from urlparse import urlparse
        # we normalize the url by parsing it first
        parsedurl=urlparse(url)
        if not parsedurl[0] in ('http','https','ftp'):
            return current_app.message(_('URL must start with http, https, or ftp.%(backlinks)s', backlinks=backlinks), worksheet_url, username=g.username)
        download = urllib2.urlopen(parsedurl.geturl())

    #XXX: disk access
    dest = os.path.join(worksheet.data_directory(), name)
    if os.path.exists(dest):
        if not os.path.isfile(dest):
            return current_app.message(_('Suspicious filename "%(filename)s" encountered uploading file.%(backlinks)s', filename=filename, backlinks=backlinks), worksheet_url, username=g.username)
        os.unlink(dest)

    response = redirect(worksheet_datafile.url_for(worksheet, name=name))

    import re
    matches = re.match("file://(?:localhost)?(/.+)", url)
    if matches:
        f = file(dest, 'wb')
        f.write(open(matches.group(1)).read())
        f.close()
        return response

    elif url != '':
        with open(dest, 'w') as f:
            f.write(download.read())
        return response
    elif new_field:
        open(dest, 'w').close()
        return response
    else:
        file.save(dest)
        return response

################################
#Publishing
################################
@worksheet_command('publish')
def worksheet_publish(worksheet):
    """
    This provides a frontend to the management of worksheet
    publication. This management functionality includes
    initializational of publication, re-publication, automated
    publication when a worksheet saved, and ending of publication.
    """
    # Publishes worksheet and also sets worksheet to be published automatically when saved
    if 'yes' in request.values and 'auto' in request.values:
        g.notebook.publish_worksheet(worksheet, g.username)
        worksheet.set_auto_publish(True)
        return redirect(worksheet_publish.url_for(worksheet))
    # Just publishes worksheet
    elif 'yes' in request.values:
        g.notebook.publish_worksheet(worksheet, g.username)
        return redirect(worksheet_publish.url_for(worksheet))
    # Stops publication of worksheet
    elif 'stop' in request.values:
        g.notebook.delete_worksheet(worksheet.published_version().filename())
        return redirect(worksheet_publish.url_for(worksheet))
    # Re-publishes worksheet
    elif 're' in request.values:
        W = g.notebook.publish_worksheet(worksheet, g.username)
        return redirect(worksheet_publish.url_for(worksheet))
    # Sets worksheet to be published automatically when saved
    elif 'auto' in request.values:
        worksheet.set_auto_publish(not worksheet.is_auto_publish())
        return redirect(worksheet_publish.url_for(worksheet))
    # Returns boolean of "Is this worksheet set to be published automatically when saved?"
    elif 'is_auto' in request.values:
        return str(worksheet.is_auto_publish())
    # Returns the publication page
    else:
        # Page for when worksheet already published
        if worksheet.has_published_version():
            hostname = request.headers.get('host', g.notebook.interface + ':' + str(g.notebook.port))

            #XXX: We shouldn't hardcode this.
            addr = 'http%s://%s/home/%s' % ('' if not g.notebook.secure else 's',
                                            hostname,
                                            worksheet.published_version().filename())
            dtime = worksheet.published_version().date_edited()
            return g.notebook.html_afterpublish_window(worksheet, g.username, addr, dtime)
        # Page for when worksheet is not already published
        else:
            return g.notebook.html_beforepublish_window(worksheet, g.username)

############################################
# Ratings
############################################
@worksheet_command('rating_info')
def worksheet_rating_info(worksheet):
    return worksheet.html_ratings_info()

@worksheet_command('rate')
def worksheet_rate(worksheet):
    ## if user_type(self.username) == "guest":
    ##     return HTMLResponse(stream = message(
    ##         'You must <a href="/">login first</a> in order to rate this worksheet.', ret))

    rating = int(request.values['rating'])
    if rating < 0 or rating >= 5:
        return current_app.message(_("Gees -- You can't fool the rating system that easily!"),
                          url_for_worksheet(worksheet), username=g.username)

    comment = request.values['comment']
    worksheet.rate(rating, comment, g.username)
    s = _("""
    Thank you for rating the worksheet <b><i>%(worksheet_name)s</i></b>!
    You can <a href="rating_info">see all ratings of this worksheet.</a>
    """, worksheet_name=worksheet.name())
    #XXX: Hardcoded url
    return current_app.message(s.strip(), '/pub/', title=_('Rating Accepted'), username=g.username)


########################################################
# Downloading, moving around, renaming, etc.
########################################################
@worksheet_command('download/<path:title>')
def worksheet_download(worksheet, title):
    return unconditional_download(worksheet, title)

def unconditional_download(worksheet, title):
    from sagenb.misc.misc import tmp_filename
    from flask.helpers import send_file
    filename = tmp_filename() + '.sws'

    if title.endswith('.sws'):
        title = title[:-4]

    try:
        #XXX: Accessing the hard disk.
        g.notebook.export_worksheet(worksheet.filename(), filename, title)
    except KeyError:
        return current_app.message(_('No such worksheet.'))

    from flask.helpers import send_file
    return send_file(filename, mimetype='application/sage')


@worksheet_command('restart_sage')
def worksheet_restart_sage(worksheet):
    #XXX: TODO -- this must not block long (!)
    worksheet.restart_sage()
    return 'done'

@worksheet_command('quit_sage')
def worksheet_quit_sage(worksheet):
    #XXX: TODO -- this must not block long (!)
    worksheet.quit()
    return 'done'

@worksheet_command('interrupt')
def worksheet_interrupt(worksheet):
    #XXX: TODO -- this must not block long (!)
    worksheet.sage().interrupt()
    return 'failed' if worksheet.sage().is_computing() else 'success'

@worksheet_command('hide_all')
def worksheet_hide_all(worksheet):
    worksheet.hide_all()
    return 'success'

@worksheet_command('show_all')
def worksheet_show_all(worksheet):
    worksheet.show_all()
    return 'success'

@worksheet_command('delete_all_output')
def worksheet_delete_all_output(worksheet):
    try:
        worksheet.delete_all_output(g.username)
    except ValueError:
        return 'fail'
    else:
        return 'success'

@worksheet_command('print')
def worksheet_print(worksheet):
    #XXX: We might want to separate the printing template from the
    #regular html template.
    return g.notebook.html(worksheet.filename(), do_print=True)


#######################################################
# Live "docbrowser" worksheets from HTML documentation
#######################################################
doc_worksheet_number = -1
def doc_worksheet():
    global doc_worksheet_number
    doc_worksheet_number = doc_worksheet_number % g.notebook.conf()['doc_pool_size']
    W = None
    for X in g.notebook.users_worksheets('_sage_'):
        if X.compute_process_has_been_started():
            continue
        if X.id_number() == doc_worksheet_number:
            W = X
            W.clear()
            break

    if W is None:
        # The first argument here is the worksheet's title, which the
        # caller should set with W.set_name.
        W = g.notebook.create_new_worksheet('', '_sage_')
    return W

def extract_title(html_page):
    #XXX: This might be better as a regex
    h = html_page.lower()
    i = h.find('<title>')
    if i == -1:
        return gettext("Untitled")
    j = h.find('</title>')
    return html_page[i + len('<title>') : j]

@login_required
def worksheet_file(path):
    # Create a live Sage worksheet from the given path.
    if not os.path.exists(path):
        return current_app.message(_('Document does not exist.'), username=g.username)

    doc_page_html = open(path).read()
    from sagenb.notebook.docHTMLProcessor import SphinxHTMLProcessor
    doc_page = SphinxHTMLProcessor().process_doc_html(doc_page_html)

    title = (extract_title(doc_page_html).replace('&mdash;', '--') or
             'Live Sage Documentation')

    W = doc_worksheet()
    W.edit_save(doc_page)
    W.set_system('sage')
    W.set_name(title)
    W.save()
    W.quit()

    # FIXME: For some reason, an extra cell gets added so we
    # remove it here.
    W.cell_list().pop()

    return g.notebook.html(worksheet_filename=W.filename(),
                           username=g.username)


####################
# Public Worksheets
####################
def pub_worksheet(source):
    # TODO: Independent pub pool and server settings.
    proxy = doc_worksheet()
    proxy.set_name(source.name())
    proxy.set_last_change(*source.last_change())
    proxy.set_worksheet_that_was_published(source.worksheet_that_was_published())
    g.notebook._initialize_worksheet(source, proxy)
    proxy.set_tags({'_pub_': [True]})
    proxy.save()
    return proxy
