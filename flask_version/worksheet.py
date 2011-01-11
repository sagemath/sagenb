import os
from functools import wraps
from flask import Flask, url_for, render_template, request, session, redirect, g
from decorators import login_required
from base import app

def worksheet_view(f):
    @login_required
    @wraps(f)
    def wrapper(username, id, **kwds):
        worksheet_filename = username + "/" + id
        try:
            worksheet = kwds['worksheet'] = app.notebook.get_worksheet_with_filename(worksheet_filename)
        except KeyError:
            return app.message("You do not have permission to access this worksheet") #XXX: i18n
        
        owner = worksheet.owner()

        if owner != '_sage_' and g.username != owner:
            if not worksheet.is_published():
                if (not username in worksheet.collaborators() and
                    not app.notebook.user_manager().user_is_admin(g.username)):
                    return app.message("You do not have permission to access this worksheet") #XXX: i18n

        if not worksheet.is_published():
            worksheet.set_active(g.username)

        #This was in twist.Worksheet.childFactory
        from base import notebook_updates
        notebook_updates()

        return f(username, id, **kwds)

    return wrapper

def url_for_worksheet(worksheet):
    """
    Returns the url for a given worksheet.
    """
    return url_for('worksheet', username=g.username,
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
@app.route('/new_worksheet')
@login_required
def new_worksheet():
    W = app.notebook.create_new_worksheet("Untitled", g.username)
    return redirect(url_for_worksheet(W))

@app.route('/home/<username>/<id>/')
@worksheet_view
def worksheet(username, id, worksheet=None):
    worksheet.sage()
    s = app.notebook.html(worksheet_filename=worksheet.filename(),
                          username=username)
    return s


def worksheet_command(target, **route_kwds):
    if 'methods' not in route_kwds:
        route_kwds['methods'] = ['GET', 'POST']
        
    def decorator(f):
        @app.route('/home/<username>/<id>/' + target, **route_kwds)
        @worksheet_view
        @wraps(f)
        def wrapper(*args, **kwds):
            #We remove the first two arguments corresponding to the
            #username and the worksheet id
            args = args[2:]
            
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
    # TODO: Send and actually use the body's HTML.
    from sagenb.notebook.twist import encode_list
    return encode_list([worksheet.state_number(), ''])

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
    id = get_cell_id()
    input = unicode_str(request.values.get('input', ''))
    cell = worksheet.new_cell_before(id, input=input)
    worksheet.increase_state_number()
    
    from sagenb.notebook.twist import encode_list
    return encode_list([cell.id(), cell.html(div_wrap=False), id])

@worksheet_command('new_text_cell_before')
def worksheet_new_text_cell_before(worksheet):
    """Add a new text cell before a given cell."""
    id = get_cell_id()
    input = unicode_str(request.values.get('input', ''))
    cell = worksheet.new_text_cell_before(id, input=input)
    worksheet.increase_state_number()
    
    from sagenb.notebook.twist import encode_list
    # XXX: Does editing correspond to TinyMCE?  If so, we should try
    # to centralize that code.
    return encode_list([cell.id(), cell.html(editing=True), id])


@worksheet_command('new_cell_after')
def worksheet_new_cell_after(worksheet):
    """Add a new cell after a given cell."""
    id = get_cell_id()
    input = unicode_str(request.values.get('input', ''))
    cell = worksheet.new_cell_after(id, input=input)
    worksheet.increase_state_number()
    
    from sagenb.notebook.twist import encode_list
    return encode_list([cell.id(), cell.html(div_wrap=False), id])

@worksheet_command('new_text_cell_after')
def worksheet_new_text_cell_after(worksheet):
    """Add a new text cell after a given cell."""    
    id = get_cell_id()
    input = unicode_str(request.values.get('input', ''))
    cell = worksheet.new_text_cell_after(id, input=input)
    worksheet.increase_state_number()
    
    from sagenb.notebook.twist import encode_list
    # XXX: Does editing correspond to TinyMCE?  If so, we should try
    # to centralize that code.
    return encode_list([cell.id(), cell.html(editing=True), id])

########################################################
# Cell deletion
########################################################

@worksheet_command('delete_cell')
def worksheet_delete_cell(worksheet):
    """
    Deletes a notebook cell.

    If there is only one cell left in a given worksheet, the request to
    delete that cell is ignored because there must be a least one cell
    at all times in a worksheet. (This requirement exists so other
    functions that evaluate relative to existing cells will still work,
    and so one can add new cells.)
    """
    id = get_cell_id()
    if len(worksheet.compute_cell_id_list()) <= 1:
        return 'ignore'
    else:
        prev_id = worksheet.delete_cell_with_id(id)
        from sagenb.notebook.twist import encode_list
        return encode_list(['delete', id, prev_id, worksheet.cell_id_list()])

@worksheet_command('delete_cell_output')
def worksheet_delete_cell_output(worksheet):
    """Delete's a cell's output."""
    id = get_cell_id()
    worksheet.get_cell_with_id(id).delete_output()

    from sagenb.notebook.twist import encode_list
    return encode_list(['delete_output', id])

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
    from sagenb.notebook.twist import encode_list
    from base import notebook_updates
    
    id = get_cell_id()
    input_text = unicode_str(request.values.get('input', '')).replace('\r\n', '\n') #DOS

    worksheet.increase_state_number()

    cell = worksheet.get_cell_with_id(id)
    cell.set_input_text(input_text)

    if request.values.get('save_only', '0') == '1':
        notebook_updates()
        return ''
    elif request.values.get('text_only', '0') == '1':
        notebook_updates()
        return encode_list([str(id), cell.html()])
    else:
        new_cell = int(request.values.get('newcell', 0)) #wheter to insert a new cell or not

    cell.evaluate(username=g.username)

    if cell.is_last():
        new_cell = worksheet.append_new_cell()
        s = encode_list([new_cell.id(), 'append_new_cell', new_cell.html(div_wrap=False)])
    elif new_cell:
        new_cell = worksheet.new_cell_after(id)
        s = encode_list([new_cell.id(), 'insert_cell', new_cell.html(div_wrap=False), str(id)])
    else:
        s = encode_list([cell.next_id(), 'no_new_cell', str(id)])

    notebook_updates()
    return s
        

@worksheet_command('cell_update')
def worksheet_cell_update(worksheet):
    import time
    from sagenb.notebook.twist import encode_list, HISTORY_MAX_OUTPUT, HISTORY_NCOLS, word_wrap_cols
    
    id = get_cell_id()

    # update the computation one "step".
    worksheet.check_comp()

    # now get latest status on our cell
    status, cell = worksheet.check_cell(id)

    if status == 'd':
        new_input = cell.changed_input_text()
        out_html = cell.output_html()
        H = "Worksheet '%s' (%s)\n"%(worksheet.name(), time.strftime("%Y-%m-%d at %H:%M",time.localtime(time.time())))
        H += cell.edit_text(ncols=HISTORY_NCOLS, prompts=False,
                            max_out=HISTORY_MAX_OUTPUT)
        app.notebook.add_to_user_history(H, g.username)
    else:
        new_input = ''
        out_html = ''

    if cell.interrupted():
        inter = 'true'
    else:
        inter = 'false'

    raw = cell.output_text(raw=True).split("\n")
    if "Unhandled SIGSEGV" in raw:
        inter = 'restart'
        print "Segmentation fault detected in output!"
        
    msg = '%s%s %s'%(status, cell.id(),
                   encode_list([cell.output_text(html=True),
                                cell.output_text(word_wrap_cols(), html=True),
                                out_html,
                                new_input,
                                inter,
                                cell.introspect_html()]))

    # There may be more computations left to do, so start one if there is one.
    worksheet.start_next_comp()
    return msg

########################################################
# Cell introspection
########################################################
@worksheet_command('introspect')
def worksheet_introspect(worksheet):
    """
    Cell introspection. This is called when the user presses the tab
    key in the browser in order to introspect.
    """
    id = get_cell_id()
    before_cursor = request.values.get('before_cursor', '')
    after_cursor = request.values.get('after_cursor', '')
    cell = worksheet.get_cell_with_id(id)
    cell.evaluate(introspect=[before_cursor, after_cursor])

    from sagenb.notebook.twist import encode_list
    return encode_list([cell.next_id(), 'introspect', id])

########################################################
# Edit the entire worksheet
########################################################
@worksheet_command('edit')
def worksheet_edit(worksheet):
    """
    Return a window that allows the user to edit the text of the
    worksheet with the given filename.
    """    
    return app.notebook.html_edit_window(worksheet, g.username)


########################################################
# Plain text log view of worksheet
########################################################
@worksheet_command('text')
def worksheet_text(worksheet):
    """
    Return a window that allows the user to edit the text of the
    worksheet with the given filename.
    """
    return app.notebook.html_plain_text_window(worksheet, g.username)

########################################################
# Copy a worksheet
########################################################
@worksheet_command('copy')
def worksheet_copy(request):
    copy = app.notebook.copy_worksheet(worksheet, g.username)
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
    ##     return app.message('You must <a href="/">login first</a> in order to edit this worksheet.')

    ws = worksheet.worksheet_that_was_published()
    if ws.owner() == g.username:
        W = ws
    else:
        W = app.notebook.copy_worksheet(worksheet, g.username)
        W.set_name(worksheet.name())

    return redirect(url_for_worksheet(W))


########################################################
# Collaborate with others
########################################################
@worksheet_command('share')
def worksheet_share(worksheet):
    return app.notebook.html_share(worksheet, g.session)

@worksheet_command('invite_collab')
def worksheet_invite_collab(worksheet):
    collaborators = [u.strip() for u in request.values.get('collaborators', '').split(',')]
    worksheet.set_collaborators(collaborators)
    return redirect('.') #XXX: What should this really be?
    
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
            return app.notebook.html_specific_revision(g.username, worksheet,
                                                       request.values['rev'])
        else:
            return app.notebook.html_worksheet_revision_list(g.username, worksheet)
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
            W = app.notebook.publish_worksheet(worksheet, g.username)
            txt = bz2.decompress(open(worksheet.get_snapshot_text_filename(rev)).read())
            W.delete_cells_directory()
            W.edit_save(txt)
            return redirect(url_for_worksheet(W))
        else:
            return app.message('Error')


        
########################################################
# Cell directories 
########################################################
@worksheet_command('cells/<path:filename>')
def worksheet_cells(worksheet, filename):
    #XXX: This requires that the worker filesystem be accessible from
    #the server.
    from flask.helpers import send_from_directory
    return send_from_directory(worksheet.cells_directory(), filename)

##############################################
# Data
##############################################
@worksheet_command('data/<path:filename>')
def worksheet_data(worksheet, filename):
    dir = os.path.abspath(worksheet.data_directory())
    if not os.path.exists(dir):
        return app.message('No data files')
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
        return app.message("Successfully deleted '%s'"%filename) #XXX: i18n
    else:
        return app.notebook.html_download_or_delete_datafile(worksheet, g.username, filename)

@worksheet_command('savedatafile')
def worksheet_savedatafile(worksheet):
    if 'button_save' in request.values:
        text_field = request.values['textfield'] #XXX: Should this be text_field
        filename = request.values['filename']
        dest = os.path.join(worksheet.data_directory(), filename) #XXX: Requires access to filesystem
        if os.path.exists(dest):
            os.unlink(dest)
        open(dest, 'w').write(text_field)

@worksheet_command('link_datafile')
def worksheet_link_datafile(worksheet):
    target_worksheet_filename = request.values['target']
    data_filename = request.values['filename']
    src = os.path.abspath(os.path.join(
        worksheet.data_directory(), data_filename))
    target_ws =  app.notebook.get_worksheet_with_filename(target_worksheet_filename)
    target = os.path.abspath(os.path.join(
        target_ws.data_directory(), data_filename))
    if target_ws.owner() != g.username and not target_ws.is_collaborator(g.username):
        return app.message("illegal link attempt!") #XXX: i18n
    os.system('ln "%s" "%s"'%(src, target))
    return redirect(worksheet_link_datafile.url_for(worksheet, name=data_filename))
    #return redirect(url_for_worksheet(target_ws) + '/datafile?name=%s'%data_filename) #XXX: Can we not hardcode this?
    
@worksheet_command('upload_data')
def worksheet_upload_data(worksheet):
    return app.notebook.html_upload_data_window(worksheet, g.username)        

@worksheet_command('do_upload_data')
def worksheet_do_upload_data(worksheet):
    from werkzeug import secure_filename

    worksheet_url = url_for_worksheet(worksheet)
    upload_url = worksheet_upload_data.url_for(worksheet)

    #XXX: i18n
    backlinks = """ Return to <a href="%s" title="Upload or create a data file in a wide range of formats"><strong>Upload or Create Data File</strong></a> or <a href="%s" title="Interactively use the worksheet"><strong>%s</strong></a>.""" % (upload_url, worksheet_url, worksheet.name())


    if 'file' not in request.files:
        #XXX: i18n
        return app.message('Error uploading file (missing field "file").%s' % backlinks, worksheet_url)
    else:
        file = request.files['file']
        
    text_fields = ['url', 'new', 'name']
    for field in text_fields:
        if field not in request.values:
            #XXX: i18n
            return app.message('Error uploading file (missing %s arg).%s' % (field, backlinks), worksheet_url)


    name = request.values.get('name', '').strip()
    new_field = request.values.get('new', '').strip()
    url = request.values.get('url', '').strip()

    name = name or file.filename or new_field
    if url and not name:
        name = url.split('/')[-1]
    name = secure_filename(name)

    if not name:
        #XXX: i18n
        return app.message('Error uploading file (missing filename).%s' % backlinks, worksheet_url)

    #XXX: disk access
    dest = os.path.join(worksheet.data_directory(), name)
    if os.path.exists(dest):
        if not os.path.isfile(dest):
            #XXX: i18n
            return app.message('Suspicious filename "%s" encountered uploading file.%s' % (name, backlinks), worksheet_url)
        os.unlink(dest)


    response = redirect(worksheet_datafile.url_for(worksheet, name=name))

    if url != '':
        #XXX: Finish me!
        pass
    elif new_field:
        open(dest, 'w').close()
        return response
    else:
        file.save(dest)
        return response        
    
################################
#Publishing
################################
@worksheet_command('publish/')
def worksheet_publish(worksheet):
    """
    This provides a frontend to the management of worksheet
    publication. This management functionality includes
    initializational of publication, re-publication, automated
    publication when a worksheet saved, and ending of publication.
    """
    # Publishes worksheet and also sets worksheet to be published automatically when saved
    if 'yes' in request.values and 'auto' in request.values:
        app.notebook.publish_worksheet(worksheet, g.username)
        worksheet.set_auto_publish(True)
        return redirect(worksheet_publish.url_for(worksheet))
    # Just publishes worksheet
    elif 'yes' in request.values:
        app.notebook.publish_worksheet(worksheet, g.username)
        return redirect(worksheet_publish.url_for(worksheet))
    # Stops publication of worksheet
    elif 'stop' in request.values:
        app.notebook.delete_worksheet(worksheet.published_version().filename())
        return redirect(worksheet_publish.url_for(worksheet))
    # Re-publishes worksheet
    elif 're' in request.values:
        W = app.notebook.publish_worksheet(worksheet, g.username)
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
            hostname = request.headers.get('host', app.notebook.interface + ':' + str(app.notebook.port))

            #XXX: We shouldn't hardcode this.
            addr = 'http%s://%s/home/%s' % ('' if not app.notebook.secure else 's',
                                            hostname,
                                            worksheet.published_version().filename())
            dtime = worksheet.published_version().date_edited()
            return app.notebook.html_afterpublish_window(worksheet, g.username, addr, dtime)
        # Page for when worksheet is not already published
        else:
            return app.notebook.html_beforepublish_window(worksheet, g.username)

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
        return app.messge("Gees -- You can't fool the rating system that easily!",
                          url_for_worksheet(worksheet))

    comment = request.values['comment']
    worksheet.rate(rating, comment, g.username)
    s = """
    Thank you for rating the worksheet <b><i>%s</i></b>!
    You can <a href="rating_info">see all ratings of this worksheet.</a>
    """%(worksheet.name())
    #XXX: Hardcoded url
    return app.message(s.strip(), '/pub/', title=u'Rating Accepted')


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
        app.notebook.export_worksheet(worksheet.filename(), filename, title)
    except KeyError:
        return app.message('No such worksheet.')

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
    return app.notebook.html(worksheet.filename(), do_print=True)


#######################
# Live documentation #
######################
doc_worksheet_number = 0
def doc_worksheet():
    global doc_worksheet_number
    wnames = app.notebook.worksheet_names()
    name = 'doc_browser_%s'%doc_worksheet_number
    doc_worksheet_number = doc_worksheet_number % app.notebook.conf()['doc_pool_size']
    if name in wnames:
        W = app.notebook.get_worksheet_with_name(name)
        W.clear()
    else:
        W = app.notebook.create_new_worksheet(name, '_sage_', docbrowser=True)
    W.set_is_doc_worksheet(True)
    return W

def extract_title(html_page):
    #XXX: This might be better as a regex
    h = html_page.lower()
    i = h.find('<title>')
    if i == -1:
        return "Untitled"
    j = h.find('</title>')
    return html_page[i + len('<title>') : j]

@login_required
def worksheet_file(path):
    # Create a live Sage worksheet out of path and render it.
    if not os.path.exists(path):
        return app.message('Document does not exist.')

    doc_page_html = open(path).read()
    from sagenb.notebook.docHTMLProcessor import SphinxHTMLProcessor
    doc_page = SphinxHTMLProcessor().process_doc_html(doc_page_html)

    title = extract_title(doc_page_html).replace('&mdash;','--')
    doc_page = title + '\nsystem:sage\n\n' + doc_page

    W = doc_worksheet()
    W.edit_save(doc_page)

    #FIXME: For some reason, an extra cell gets added
    #so we remove it here.
    cells = W.cell_list()
    cells.pop()

    return app.notebook.html(worksheet_filename=W.filename(),
                         username=g.username)

