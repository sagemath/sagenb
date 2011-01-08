from functools import wraps
from flask import Flask, url_for, render_template, request, session, redirect, g
from decorators import login_required
from base import app

def worksheet_view(f):
    @login_required
    @wraps(f)
    def wrapper(username, id, **kwds):
        assert username == g.username
        worksheet_filename = g.username + "/" + id
        worksheet = kwds['worksheet'] = app.notebook.get_worksheet_with_filename(worksheet_filename)
        owner = worksheet.owner()

        if owner != g.username:
            #XXX: Make this a template
            return "You do not have permission to access this worksheet"

        ## if owner != '_sage_' and g.username != owner:
        ##     if not worksheet.is_published():
        ##         if not username in self.worksheet.collaborators() and user_type(username) != 'admin':
        ##             raise RuntimeError, "illegal worksheet access"

        if not worksheet.is_published():
            worksheet.set_active(g.username)

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


"""
Functions from twist.py to add:

    571:class Worksheet_savedatafile(WorksheetResource, resource.PostableResource):
    581:class Worksheet_link_datafile(WorksheetResource, resource.Resource):
    596:class Worksheet_upload_data(WorksheetResource, resource.Resource):
    600:class Worksheet_do_upload_data(WorksheetResource, resource.PostableResource):
    674:class Worksheet_datafile(WorksheetResource, resource.Resource):
    691:class Worksheet_data(WorksheetResource, resource.Resource):
    721:class Worksheet_cells(WorksheetResource, resource.Resource):

    768:class Worksheet_introspect(WorksheetResource, resource.PostableResource):
    793:class Worksheet_edit(WorksheetResource, resource.Resource):
    805:class Worksheet_text(WorksheetResource, resource.Resource):
    817:class Worksheet_copy(WorksheetResource, resource.PostableResource):
    828:class Worksheet_edit_published_page(WorksheetResource, resource.Resource):

    
    900:class Worksheet_share(WorksheetResource, resource.Resource):
    905:class Worksheet_invite_collab(WorksheetResource, resource.PostableResource):
    959:class Worksheet_revisions(WorksheetResource, resource.PostableResource):
   
   1326:class Worksheet_publish(WorksheetResource, resource.Resource):
   1379:class Worksheet_rating_info(WorksheetResource, resource.Resource):
   1384:class Worksheet_rate(WorksheetResource, resource.Resource):
   1410:class Worksheet_download(WorksheetResource, resource.Resource):
   1466:class Worksheet_rename(WorksheetResource, resource.PostableResource):
   1471:class Worksheet_restart_sage(WorksheetResource, resource.Resource):
   1477:class Worksheet_quit_sage(WorksheetResource, resource.Resource):
   1483:class Worksheet_interrupt(WorksheetResource, resource.Resource):
   1493:class Worksheet_hide_all(WorksheetResource, resource.Resource):
   1498:class Worksheet_show_all(WorksheetResource, resource.Resource):
   1505:class Worksheet_delete_all_output(WorksheetResource, resource.Resource):
   1513:class Worksheet_print(WorksheetResource, resource.Resource):
"""
