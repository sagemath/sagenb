/*global $, alert, async_request, clearTimeout, confirm, document, escape, location, navigator, open, prompt, setTimeout, window, worksheet_filenames */
/*jslint maxerr: 10000, white: true, onevar: true, undef: true, nomen: true, eqeqeq: true, plusplus: true, bitwise: true, regexp: true, strict: true, newcap: true, immed: true */
//"use strict";

// Code and docstring conventions.  Please use 4-space indentation
// throughout.  JSLint (http://www.jslint.com/) on the "The Good
// Parts" setting can uncover potential problems.

//function foo(arg1, arg2) {
    /*
    Description.

    INPUT:
        arg1 -- description of arg1
        arg2 -- description of arg2
    GLOBAL INPUT / OUTPUT:
        glob1 -- how we use and/or change this
        glob2 -- how we use and/or change this
    OUTPUT:
        Returned variable(s).
    */
    /*
    // Declare variables at the top, since JS vars don't have block scope.
    var a, b, X;
    for (a = 0; a < arg1.length; a++) {
        // This is a comment.
        arg1[a] *= glob1;
    }
    // Here's another comment.
    return [arg2, arg1];
    */
//}


///////////////////////////////////////////////////////////////////
//
// GLOBAL VARIABLES
//
// PLEASE define all global variables up here, and if you want to set
// them with anything but simple assignment, 'var' them first, and set
// them later.  Your code might work in your browser, but it might
// break initial setup for other critical pieces in other browsers.
// Thanks. (and for the record, I'm guilty of this more than anybody
// else here -- I figure a big block comment might help keep me in
// check)
//
// Exception: keyboard globals are defined at the end.
//
///////////////////////////////////////////////////////////////////

// Cell lists, maps, and cache.
var cell_id_list = [];
var queue_id_list = [];
var onload_id_list = [];
var cell_element_cache = {};

// Worksheet information from worksheet.py
var worksheet_locked;
var original_title = document.title;
var state_number = -1;
// Current worksheet info, set in notebook.py.
var worksheet_filename = '';
var worksheet_name = '';
var user_name = '';

// Ping the server periodically for worksheet updates.
var server_ping_time = 10000;

// Interact constants.  See interact.py and related files.
// Present in wrapped output, forces re-evaluation of ambient cell.
var INTERACT_RESTART = '__SAGE_INTERACT_RESTART__';
// Delimit updated markup.
var INTERACT_START = '<?__SAGE__START>';
var INTERACT_END = '<?__SAGE__END>';

// Browser & OS identification.
var browser_op, browser_saf, browser_konq, browser_moz, browser_ie, browser_iphone;
var os_mac, os_lin, os_win;

// Functions assigned during keyboard setup.
var input_keypress;
var input_keydown;
// Bug workaround.
var skip_keyup = false;

// Interrupts.
var interrupt_state = {count: 0};

// Focus / blur.
var current_cell = -1;
var cell_has_changed = false;

// Resizing too often significantly affects performance.
var keypress_resize_delay = 250;
var last_keypress_resize = 0;
var will_resize_soon = false;
var previous = {};

// Are we're splitting a cell and evaluating it?
var doing_split_eval = false;
// Whether the the next call to jump_to_cell is ignored.  Used to
// avoid changing focus.
var ignore_next_jump = false;
// Set to true for pages with public interacts.
var ignore_all_jumps = false;
var control_key_pressed = 0;
var evaluating_all = false;

// Cell update check variables.  Times are in milliseconds.
var update_timeout = -1;
var updating = false;
var update_time = -1;
var update_count = 0;
var update_falloff_threshold = 20;
var update_falloff_level = 0;
var update_falloff_deltas = [250, 500, 1000, 5000];
var update_error_count = 0;
var update_error_threshold = 30;
var update_error_delta = 1024;
var update_normal_delta = update_falloff_deltas[0];
var cell_output_delta = update_normal_delta;

// Introspection data.
var introspect = {};

// Regular expressions to parse cell input for introspection.
// Characters that don't belong in a variable name.
var non_word = "[^a-zA-Z0-9_]";
// The command at the end of a string.
var command_pat = "([a-zA-Z_][a-zA-Z._0-9]*)$";
var function_pat = "([a-zA-Z_][a-zA-Z._0-9]*)\\([^()]*$";
var one_word_pat = "([a-zA-Z_][a-zA-Z._0-9]*)";
var unindent_pat = "^\\s{0,4}(.*)$";
// The # doesn't need a slash for now, but let's give it one anyway...
var uncomment_pat = "^([^\\#]*)\\#{0,1}(.*)$";
var whitespace_pat = "(\\s*)";

try {
    non_word = new RegExp(non_word);
    command_pat = new RegExp(command_pat);
    function_pat = new RegExp(function_pat);
    one_word_pat = new RegExp(one_word_pat);
    whitespace_pat = new RegExp(whitespace_pat);
    unindent_pat = new RegExp(unindent_pat);
    uncomment_pat = new RegExp(uncomment_pat);
} catch (e) {}

// The global cell_writer target.
var cell_writer = document;

// Slideshow mode?
var in_slide_mode = false;
// Does the current slide have the hidden input class?
var slide_hidden = false;

var title_spinner_i = 0;
var title_spinner = ['/ ', '\\ '];
//var title_spinner = ['    ', '.   ', '..  ', '... '];
//var title_spinner = ['[ ] ', '[.] ', '[:] ', '[.] '];
//var title_spinner = ['S ', 'SA ', 'SAG ', 'SAGE '];
//var title_spinner = ['[   ] ', '[.  ] ', '[.. ] ', '[...] '];
//var title_spinner = ['[-] ','[/] ','[|] ','[\\] '];

var modal_prompt_element =
    '<div class="modal-prompt" style="display: none;">' +
    '    <form>' +
    '        <div class="message"></div>' +
    '        <div class="field">' +
    '            <input type="text" />' +
    '        </div>' +
    '        <div class="button-div">' +
    '            <button type="submit">OK</submit>' +
    '        </div>' +
    '    </form>' +
    '</div>';


///////////////////////////////////////////////////////////////////
// Cross-Browser Stuff
///////////////////////////////////////////////////////////////////
function toint(x) {
    /*
    Convert a object to an integer, if it's possible.  We use this to
    convert a cell id to an integer if it's just a string
    representation of that integer.  Otherwise, we return the original
    id.  This allows us to use alphanumeric ids for special cells.

    INPUT:
        x -- any object, e.g., a string, integer, float, etc.
    OUTPUT:
        an integer or the object
     */
    if (x === '0') {
        return 0;
    } else {
        return parseInt(x, 10) || x;
    }
}


function decode_response(text) {
    /*
    Reconstructs a JSON-encoded object from a string.  We use this to
    parse server responses into cell IDs, data, etc.  In particular,
    any key in the reconstructed object that ends in 'id' is filtered
    through toint.

    INPUT:
        text -- string
    OUTPUT:
        object
    */
    return JSON.parse(text, function (key, value) {
        if (typeof(key) === 'string' && key.slice(-2) === 'id') {
            return toint(value);
        }
        return value;
    });
}


function encode_response(obj) {
    /*
    JSON-encodes a object to a string.

    INPUT:
        obj -- object
    OUTPUT:
        string
    */
    return JSON.stringify(obj);
}



function initialize_the_notebook() {
    /*
    Do the following:
        1. Determine the browser OS, type e.g., opera, safari, etc.;
           we set global variables for each type.
        2. Figure out which keyboard the user has.
    */
    var i, n, nav, nap, nua;

    // TODO: Use js-hotkeys (http://code.google.com/p/js-hotkeys/)?
    // Determine the browser, OS and set global variables.
    try {
        n = navigator;
        nav = n.appVersion;
        nap = n.appName;
        nua = n.userAgent;
        browser_op = (nua.indexOf('Opera') !== -1);
        browser_saf = (nua.indexOf('Safari') !== -1);
        browser_iphone = (nua.indexOf('iPhone') !== -1);
        browser_konq = (!browser_saf &&
                        (nua.indexOf('Konqueror') !== -1)) ? true : false;
        browser_moz = ((!browser_saf && !browser_konq) &&
                       (nua.indexOf('Gecko') !== -1)) ? true : false;
        browser_ie = ((nap.indexOf('Internet Explorer') !== -1) && !browser_op);
        os_mac = (nav.indexOf('Mac') !== -1);
        os_win = (((nav.indexOf('Win') !== -1) ||
                   (nav.indexOf('NT') !== -1)) && !os_mac) ? true : false;
        os_lin = (nua.indexOf('Linux') !== -1);
    } catch (e) {
        alert(e);
    }

    // Get the keyboard codes for our browser/os combination.
    get_keyboard();

    // Parse the cell IDs.
    cell_id_list = $.map(cell_id_list, function (id) {
        // Reset each cell's introspection variables.
        if (is_compute_cell(id)) {
            halt_introspection(id);
        }
        return toint(id);
    });

    // Parse active cell IDs and mark these cells as running.  We
    // don't use $.map here, to avoid the possibility of overwriting a
    // debug version of the list.  See debug.js for details.
    for (i = 0; i < queue_id_list.length; i += 1) {
       queue_id_list[i] = toint(queue_id_list[i]);
       cell_set_running(queue_id_list[i]);
    }
    if (queue_id_list.length) {
        start_update_check();
    }

    // Parse active cell IDs and mark these cells as running.  We
    // don't use $.map here, to avoid the possibility of overwriting a
    // debug version of the list.  See debug.js for details.
    for (i = 0; i < queue_id_list.length; i += 1) {
       queue_id_list[i] = toint(queue_id_list[i]);
       cell_set_running(queue_id_list[i]);
    }
    if (queue_id_list.length) {
        start_update_check();
    }

    // Parse "onload" cell IDs and evaluate these cells.  Note: The
    // server fires "%auto" cells, whereas the client fires "onload"
    // cells.
    onload_id_list = $.map(onload_id_list, function (id) {
        id = toint(id);
        evaluate_cell(id, 0);
        return id;
    });

    // Resize all cells on window resize.
    previous.height = $(document.documentElement).height();
    previous.width = $(document.documentElement).width();
    $(window).resize(function () {
        var h, w;
        h = $(document.documentElement).height();
        w = $(document.documentElement).width();

        // IE fires global resize *far* too often (e.g., on every cell
        // focus/blur).
        if ((h !== previous.height) || (w !== previous.width)) {
            resize_all_cells();
            previous.height = h;
            previous.width = w;
        }
    });

    // Resize and save on paste.
    $('textarea').live('paste', function () {
        var id = $(this).attr('id').slice(11);
        setTimeout(function () {
            send_cell_input(id);
            cell_input_resize(id);
        }, keypress_resize_delay);
    });

    // Quit the sage process on close for doc/pub-browser worksheets.
    i = worksheet_filename.indexOf('/');
    if (i !== -1 && worksheet_filename.slice(0, i) === '_sage_') {
	    $(window).unload(function () {
	        quit_sage();
	    });
    }

    //bind events to our DOM elements
    bind_events();
}


function bind_events() {
    /*
     * Attaches events to DOM elements.
     */
    $('body').on('focus', 'textarea.cell_input', function () {
        var id = $(this).attr("id");
        var cell_id = get_cell_id_from_id(id);
        cell_focused(this, cell_id);
        return true;
    });
    $('body').on('focus', 'textarea.cell_input_hide', function () {
        var id = $(this).attr("id");
        var cell_id = get_cell_id_from_id(id);
        cell_focused(this, cell_id);
        return true;
    });
    $('body').on('blur', 'textarea.cell_input_active', function () {
        var id = $(this).attr("id");
        var cell_id = get_cell_id_from_id(id);
        cell_blur(cell_id);
        return true;
    });
    $('body').on('keyup', 'textarea.cell_input_active', function (event) {
        var id = $(this).attr("id");
        var cell_id = get_cell_id_from_id(id);
        return input_keyup(cell_id, event);
    });
    $('body').on('keydown', 'textarea.cell_input_active', function (event) {
        var id = $(this).attr("id");
        var cell_id = get_cell_id_from_id(id);
        return input_keydown(cell_id, event);
    });
    $('body').on('keypress', 'textarea.cell_input_active', function (event) {
        var id = $(this).attr("id");
        var cell_id = get_cell_id_from_id(id);
        return input_keypress(cell_id, event);
    });
    $('body').on('click', 'input.eval_button_active', function () {
        var id = $(this).attr("id");
        var cell_id = get_cell_id_from_id(id);
        evaluate_cell(cell_id, 0);
    });
}


function get_cell_id_from_id(id) {
    /*
    * A function to get the cell_id from the button's id attribute
    */
    var num_re = /[0-9]+/;
    var match_result = num_re.exec(id);
    var cell_id = toint(match_result[0]);
    return cell_id;
}


function true_function() {
    /*
    A function that always returns true.
    */
    return true;
}
input_keypress = true_function;


function get_keyboard() {
    /*
    Determine which keycodes we want, then make a request back to the
    server for those keycodes.  When the server returns the javascript
    with exactly those keycodes, we eval that javascript.

    OUTPUT:
        set some global variables that record platform specific key
        codes
    */
    var b, o, warn = false;

    input_keypress = cell_input_key_event;
    input_keydown = true_function;

    if (browser_op) {
        b = "o";
    } else if (browser_ie) {
        b = "i";
        input_keypress = true_function;
        input_keydown = cell_input_key_event;
    } else if (browser_saf) {
        b = "s";
        input_keypress = true_function;
        input_keydown = cell_input_key_event;
    } else if (browser_konq) {
        b = "k";
        warn = true;
    } else {
        b = "m";
    }

    if (os_mac) {
        o = "m";
    } else if (os_lin) {
        o = "l";
    } else {
        o = "w";
    }

    if (!b || !o || warn) {
        alert(translations['Your browser / OS combination is not supported.\\nPlease use Firefox or Opera under Linux, Windows, or Mac OS X, or Safari.']);
    }

    $.getScript('/javascript/dynamic/keyboard/' + b + o);
}


function get_element(id) {
    /*
    Return the DOM element with the given id.  If no element has the
    id, return null.

    INPUT:
        id -- an integer or string
    OUTPUT:
        a DOM element or null.
    */
    var elem = $('#' + id);
    if (elem.length) {
        return elem[0];
    } else {
        return null;
    }
}


function set_class(id, cname) {
    /*
    Set the class of the DOM element with given id to cname.

    INPUT:
        id -- an integer or string
        cname -- a string
    OUTPUT:
        Sets the class of the DOM element with the
        given id to be class.
    */
    $('#' + id).attr('class', cname);
}


function key_event(e) {
    /*
    Normalizes the different possible keyboard event structures for
    different browsers.  NOTE: We use key_event as an object.

    INPUT:
        e -- a DOM event
    OUTPUT:
        Sets properties of the DOM object in a uniform way.

    TODO: Use jQuery's Event, instead.
   */
    // IE uses the global variable event.
    e = e || window.event;

    // Record whether alt, control, and shift were pressed.
    this.v = 0;
    if (e.altKey) {
        this.v += 1;
    }
    if (e.ctrlKey) {
        this.v += 2;
    }
    if (e.shiftKey) {
        this.v += 4;
    }

    // We set the specific key that was pressed (no modifier), which
    // is string as a string pair n,m.  See keyboards.py for details.
    this.m = e.keyCode + "," + e.which;
    return this;
}


function time_now() {
    /*
    Return the time right now as an integer since Unix epoch in
    milliseconds.

    OUTPUT:
        an integer
    */
    return (new Date()).getTime();
}


function current_selection(input) {
    /*
    Return the text that is currently selected in a given text area.

    INPUT:
        input -- a DOM object (a textarea)
    OUTPUT:
        a string
    */
    var range;
    if (browser_ie) {
        range = document.selection.createRange();
        return range.text;
    } else {
        return input.value.substring(input.selectionStart, input.selectionEnd);
    }
}


function get_selection_range(input) {
    /*
    Return the start and end positions of the currently selected text
    in the input text area (a DOM object).

    INPUT:
        input -- a DOM object (a textarea)
    OUTPUT:
        an array of two nonnegative integers
    */
    var end, range, start, tmprange;
    if (browser_ie) {
        range = document.selection.createRange();

        tmprange = range.duplicate();
        tmprange.moveToElementText(input);
        tmprange.setEndPoint("endToStart", range);
        start = tmprange.text.length;

        tmprange = range.duplicate();
        tmprange.moveToElementText(input);
        tmprange.setEndPoint("endToEnd", range);
        end = tmprange.text.length;

        return [start, end];
    } else {
        return [input.selectionStart, input.selectionEnd];
    }
}


function set_selection_range(input, start, end) {
    /*
    Select a range of text in a given textarea.

    INPUT:
        input -- a DOM input text area
        start -- an integer
        end -- an integer
    OUTPUT:
        changes the state of the input textarea.
    */
    var range;
    if (browser_ie) {
        input.value = input.value.replaceAll("\r\n", "\n");
        range = document.selection.createRange();
        range.moveToElementText(input);
        range.moveStart('character', start);
        range.setEndPoint("endToStart", range);
        range.moveEnd('character', end - start);
        range.select();
    } else {
        input.selectionStart = start;
        input.selectionEnd = end;
    }
}


function get_cursor_position(cell) {
    /*
    Return an integer that gives the position of the text cursor in
    the cells input field.

    INPUT:
        cell -- an input cell (not the id but the actual DOM element)
    OUTPUT:
        a single integer
    */
    return get_selection_range(cell)[1];
}


function set_cursor_position(cell, n) {
    /*
    Move the cursor position in the cell to position n.

    WARNING: Does nothing when n is 0 on Opera at present.

    INPUT:
        cell -- an actual cell in the DOM, returned by get_cell
        n -- a non-negative integer
    OUTPUT:
        changes the position of the cursor.
    */
//    if (browser_op && !n) {
        // program around a "bug" in opera where using this hack to
        // position the cursor selects the entire text area (which is
        // very painful, since then the user accidentally deletes all
        // their code).
//        return;
//    }
    // TODO: note for explorer:  may need to focus cell first.
    set_selection_range(cell, n, n);
}


///////////////////////////////////////////////////////////////////
// Misc page functions -- for making the page work nicely
///////////////////////////////////////////////////////////////////
function hide_java_applets() {
    /*
    Hides all Jmol applets by moving them off the screen and putting a
    box of the same size in the same place.
     */
    $('.jmol_applet').each(function () {
        var me = $(this),
            width = me.width(),
            height = me.height();
        me.css({
            marginLeft: '-' + (width + 1000) + 'px'
        })
        me.after(
            $('<table><tbody><tr><td align="center" valign="middle">' + 
              translations["Java Applet Hidden"] + '</td></tr></tbody></table>').css({
                marginTop: '-' + height.toString() + 'px',
                width: width.toString() + 'px',
                height: height.toString() + 'px',
                border: '1px solid black',
                backgroundColor: '#ccc',
                color: 'black'
            })
        );
    });
}


function show_java_applets() {
    /*
    Shows all the java applets hid with applet_hide().
    */
    $('.jmol_applet').each(function () {
        $(this).css({
            marginLeft: '0px'
        }).next().remove();
    });
}


function modal_prompt(form_options, options, modal_options) {
    /*
    Displays a prompt with a modal dialog. Use this instead of
    prompt().

    INPUT:
        form_options -- options passed to jQuery.Form. All options
        have the same behavior as jQuery.Form's except success, which
        is passed the form and prompt as arguments. Please refer to
        the jQuery.Form documentation
        (http://jquery.malsup.com/form/#options-object) for more
        information.

        success -- function to be called when the form is
        submitted. It is passed the generated form and prompt as
        arguments.

     OR, for convenience:

        form_options -- function to be called when the form is
        submitted. It is passed the generated form and prompt as
        arguments.

        options -- an object with any of the following attributes:
           - title -- the title of the modal prompt.
           - message -- the message to be displayed in the prompt.
           - default -- the default value of the prompt.
           - submit -- the value of the submit button. Defaults to "OK".
           - overlay_close -- whether to close the dialog if the
             overlay is clicked. Defaults to true.
           - id -- id for the modal prompt.
           - form_id -- id for the form.
           - css -- CSS to be applied to the prompt. Consider editing
             the stylesheet files instead of using this option.
           - post_submit_behavior -- any of "close", "destroy", which
             also removes the dialog code or a custom function to be
             called after submitting the form. Defaults to "destroy"

        modal_options -- options passed to jQuery UI Dialog. Refer to
        the jQuery UI Dialog documentation
        (http://jqueryui.com/demos/dialog/#default>) for more
        options. Default options are:
           - autoOpen: true -- automatically opens the dialog. If set
             to false, open the dialog with <prompt>.dialog('open').
           - modal: true -- makes the dialog modal, i.e., UI blocking.
           - bgiframe: true -- a fix for an IE issue regarding
             <select> elements. Not recommended for disabling.
           - width: "20em" -- width of the dialog box.

    OUTPUT:
        returns the generated prompt
    */
    var title, message, default_value, submit_value, css, new_prompt, new_form, overlay_close, close_behavior, close_dialog, input, old_success_function;

    // Options setup.
    options = options || {};
    title = options.title || '';
    message = options.message || '';
    default_value = options['default'] || '';
    submit_value = options.submit || 'OK';
    css = options.css || {};

    overlay_close = options.overlay_close;
    if (typeof(options.overlay_close) === 'undefined') { 
        overlay_close = true;
    }

    close_behavior = options.close_behavior || 'destroy';
    close_dialog = function () {
        if (close_behavior === 'destroy') {
            new_prompt.dialog('destroy');
            new_prompt.remove();
        } else if (close_behavior === 'close') {
            new_prompt.dialog('close');
        } else if (typeof(close_behavior) === 'function') {
            close_behavior();
        }
        show_java_applets();
    };
    
    modal_options = $.extend({
        autoOpen: true,
        bgiframe: true,
        modal: true,
        width: '20em',
        close: close_dialog
    },
    modal_options);

    new_prompt = $(modal_prompt_element);
    $('body').append(new_prompt);
    new_prompt.css(css);

    new_form = new_prompt.find('form');
    if (options.id) {
        new_prompt.attr('id', options.id);
    }
    if (options.form_id) {
        new_form.attr('id', options.form_id);
    }

    // Prompt setup.
    new_prompt.find('div.message').html(message);
    input = new_prompt.find('input', 'div.field').attr('value', default_value).css('width', '100%');
    new_prompt.find('button[type="submit"]').html(submit_value);

    modal_options.title = modal_options.title || title;

    if (overlay_close) {
        $('div.ui-widget-overlay').live('click', close_dialog);
    }

    // Form setup.
    old_success_function = form_options.success;
    form_options.success = function () {
        old_success_function(new_form, new_prompt);
        close_dialog();
    };

    new_form.ajaxForm(form_options);
    hide_java_applets();
    new_prompt.dialog(modal_options);
    input.select();
}


function refresh() {
    /*
    This function simply refreshes the current HTML page, thus completely
    reloading the DOM from the server.
    */
    window.location.replace(location.href);
}


function refresh_cell_list() {
    /*
    This function refreshes all the cells in the worksheet using an
    async call back to the server.
    */
    async_request(worksheet_command('cell_list'), refresh_cell_list_callback);
}


function refresh_cell_list_callback(status, response) {
    /*
    In conjunction with refresh_cell_list, this function does the
    actual update of the HTML of the list of cells.  Here
    response is a pair consisting of the updated state_number and
    the new HTML for the worksheet_cell_list div DOM element.
    */

    var s, X, z;
    if (status !== 'success') {
        return;
    }
    X = decode_response(response);
    state_number = parseInt(X.state_number, 10);

    // Now we replace the HTML for every cell *except* the current
    // cell.
    z = get_element(current_cell);
    if (z) {
        s = z.innerHTML;
    }

    refresh();

    if (z) {
        z = get_element(current_cell);
        z.innerHTML = s;
        cell_input_resize(current_cell);
        jump_to_cell(current_cell, 0);
    }
}


String.prototype.replaceAll = function (old_sub, new_sub) {
    /*
    Replace all instances of the given substring by another string.

    INPUT:
        this -- the initial string
        old_sub -- the substring to replace
        new_sub -- the replacement
    OUTPUT:
        the updated string
    */
    // The regular expression engine should avoid infinite loops, e.g.:
    // 'a'.replaceAll('a', 'a');
    return this.replace(new RegExp(old_sub, 'g'), new_sub);
};


function is_whitespace(s) {
    /*
    Return true precisely if the input string s consists only of
    whitespace, e.g., spaces, tabs, etc.

    INPUT:
        s -- a string
    OUTPUT:
        true or false
    */

    // We check using the whitespace_pat regular expression defined at
    // the top of this file.
    var m = whitespace_pat.exec(s);
    return (m[1] === s);
}


function first_variable_name_in_string(s) {
    /*
    This function returns the first valid variable name in a string.

    INPUT:
        s -- a string
    OUTPUT:
        a string
    */
    var m = one_word_pat.exec(s);
    if (m === null) {
        return s;
    }
    return m[1];
}


function lstrip(s) {
    /*
    Given a string s, strip leading whitespace from s and return the
    resulting string.

    INPUT:
        s -- a string
    OUTPUT:
        a string
    */
    var i = 0, n = s.length;
    while (i < n && (s[i] === ' ' || s[i] === '\n' || s[i] === '\t')) {
        i = i + 1;
    }
    return s.slice(i);
}


function resize_all_cells() {
    /*
    Resizes all cells that do not start with %hide; called whenever
    the window gets resized.

    GLOBAL INPUT:
        cell_id_list -- a list of integers
    */
    var i, id, len = cell_id_list.length;
    for (i = 0; i < len; i += 1) {
        // Get the id of the cell to resize
        id = cell_id_list[i];
        if (!is_compute_cell(id)) {
            continue;
        }
        // Make sure it is not hidden, and if not resize it.
        if (get_cell(id).className !== "cell_input_hide") {
            cell_input_resize(id);
        }
    }
}


function input_keyup(id, event) {
    /*
    Resizes and auto-idents cells on key up.

    INPUT:
        id -- integer or string; cell id
        event -- a keyup event
    GLOBAL INPUT:
        keypress_resize_delay -- amount of time to wait between resizes
        last_keypress_resize -- last time we resized
        will_resize_soon -- if a keyup event is ignored for the
        purpose of resizing, then we queue one up.  Avoid a
        timeout-flood with this lock.
    */
    var cell, e, indent, m, position, t, text;
    id = toint(id);

    if (skip_keyup) {
        skip_keyup = false;
        return false;
    }

    t = time_now();
    if ((t - last_keypress_resize) > keypress_resize_delay) {
        last_keypress_resize = t;
        cell_input_resize(id);
    } else if (!will_resize_soon) {
        will_resize_soon = true;
        setTimeout(function () {
            cell_input_resize(id);
            will_resize_soon = false;
        }, keypress_resize_delay);
    }

    // Automatic indentation.
    if (browser_iphone) {
        return;
    }

    e = new key_event(event);
    if (!e) {
        return;
    }

    if (key_enter(e)) {
        cell = get_cell(id);
        /* Warning!  Very subtle regular expression (for non-JAPHs):

         (?:\n|^)        -- starting from the last line ending (or beginning
                            of the cell) (don't capture contents)

         ( *)            -- capture as many spaces as we can find

         (?:.*?)         -- everything else in the string, but save room for
                            the following terms (don't capture contents)

         (:?)            -- capture an optional colon before the following
                            term

         [ \t\r\v\f]*\n$ -- ignore whitespace at the end of the line
        */
        // TODO: Really fix auto-indentation in IE.
        position = get_cursor_position(cell);
        text = text_cursor_split(cell);

        // We use exec instead of test, since the latter does not
        // populate RegExp.$1, etc., with captured groups in IE.
        m = /(?:\n|^)( *)(?:.*?)(:?)[ \t\r\v\f]*\n$/.exec(text[0]);
        if (m) {
            indent = m[1];
            if (m[2] === ':') {
                indent = indent + "    ";
            }

            cell.value = text[0] + indent + text[1];
            set_cursor_position(cell, position + indent.length);
        }
    }
}


///////////////////////////////////////////////////////////////////
// Completions interface stuff
///////////////////////////////////////////////////////////////////
function handle_introspection(id, cell_input, event) {
    /*
    Handles introspection key events.

    INPUT:
        id -- integer or string; cell id
        cell_input -- input cell
        event -- keypress event
    OUTPUT:
        a boolean
    */
    var before, col, intr, row, select_replacement = true;

    intr = introspect[id];
    if (intr.replacing && !intr.docstring) {
        // We're in the completions menu.
        col = intr.replacement_col;
        row = intr.replacement_row;

        // TODO: Embed the total number of rows and columns in a
        // completions menu.
        if (key_menu_up(event)) {
            // Up arrow pressed.
            row -= 1;
            // Wrap around vertically.
            if (!replacement_element_exists(id, row, col)) {
                row = 1;
                while (replacement_element_exists(id, row, col)) {
                    row += 1;
                }
                row -= 1;
            }
        } else if (key_menu_down(event)) {
            // Down arrow pressed.
            row += 1;
            if (!replacement_element_exists(id, row, col)) {
                row = 0;
            }
        } else if (key_menu_right(event)) {
            // Right arrow pressed.
            col += 1;
            if (!replacement_element_exists(id, row, col)) {
                col = 0;
            }
        } else if (key_menu_left(event)) {
            // Left arrow pressed.
            col -= 1;
            // Wrap around horizontally.
            if (!replacement_element_exists(id, row, col)) {
                col = 1;
                while (replacement_element_exists(id, row, col)) {
                    col += 1;
                }
                col -= 1;
            }
        } else {
            select_replacement = false;
        }
        if (select_replacement) {
            select_replacement_element(id, row, col);
            return false;
        }
        if (key_menu_pick(event)) {
            // Enter pressed.  Do the replacement.
            do_replacement(id, intr.replacement_word, true);
            skip_keyup = true;
            return false;
        }
    }

    if (key_request_introspections(event)) {
        // We start over if the input has changed.
        if (intr.changed) {
            intr.changed = false;
            evaluate_cell_introspection(id, null, null);
            return false;
        }

        // We began with a docstring or source code.  Toggle between
        // the two.
        if (!intr.replacing && intr.docstring) {
            before = intr.before_replacing_word;

            if (before.slice(-2) === '??') {
                before = before.slice(0, -1);
            } else {
                before += '?';
            }

            intr.before_replacing_word = before;
            evaluate_cell_introspection(id, before, intr.after_cursor);
            return false;
        }

        // We began with a list of completions.  Toggle between the
        // list and the docstring of the latest replacement candidate.
        if (intr.replacing && !intr.docstring) {
            intr.docstring = true;
            evaluate_cell_introspection(id, intr.before_replacing_word +
                                        intr.replacement_word + '?',
                                        intr.after_cursor);
            return false;
        }
        if (intr.replacing && intr.docstring) {
            intr.docstring = false;
            evaluate_cell_introspection(id, intr.before_replacing_word +
                                        intr.replacing_word, intr.after_cursor);
            return false;
        }

    } else if (key_close_helper(event)) {
        // ESC pressed.  Stop introspecting.
        halt_introspection(id);
        return false;
    }

    // Any other key.  Return true to continue handling this event.
    if (intr.replacing && !intr.docstring) {
        halt_introspection(id);
    }
    return true;
}


function do_replacement(id, word, do_trim) {
    /*
    Replaces an object's name with an item from a cell's completions
    menu.

    INPUT:
        id -- integer or string; cell id
        word -- a string; the replacement
        do_trim -- true or false; whether to trim the replacement
    */
    var cell_input, pos;
    id = toint(id);

    // Get the input cell and focus on it.
    cell_input = get_cell(id);
    cell_focus(id, false);

    // If necessary get only the first word out of the input word
    // string.
    if (do_trim) {
        word = first_variable_name_in_string(word);
    }

    // Do the actual completion.
    cell_input.value = introspect[id].before_replacing_word + word +
        introspect[id].after_cursor;

    // Put the cursor right after the word we just put in.
    pos = introspect[id].before_replacing_word.length + word.length;
    set_cursor_position(cell_input, pos);

    // Done completing, so get rid of the completions menu.
    halt_introspection(id);
}


function get_replacement_element(id, row, col) {
    /*
    Returns the highlighted DOM element in a cell's completions menu.

    INPUT:
        id -- integer or string; cell id
        row -- integer; vertical position of element
        col -- integer; horizontal position of element
    OUTPUT:
        a DOM element
    */
    return get_element("completion" + id + "_" + row + "_" + col);
}


function replacement_element_exists(id, row, col) {
    /*
    Returns whether a non-empty replacement exists in the given
    position in a cell's completions menu.

    INPUT:
        id -- integer or string; cell id
        row -- integer; vertical position of element
        col -- integer; horizontal position of element
    OUTPUT:
        a boolean
    */
    var elem = get_replacement_element(id, row, col);
    return elem !== null && $.trim($(elem).text()) !== '';
}

function select_replacement_element(id, row, col) {
    /*
    (Un-)highlights prospective replacement elements in a cell's
    completions menu.

    INPUT:
        id -- integer or string; cell id
        row -- integer; vertical position of element
        col -- integer; horizontal position of element
    */
    var e, intr;

    id = toint(id);
    intr = introspect[id];

    e = get_replacement_element(id, intr.replacement_row, intr.replacement_col);
    if (!e) {
        return;
    }
    e.className = 'completion_menu_two';

    intr.replacement_row = toint(row);
    intr.replacement_col = toint(col);

    e = get_replacement_element(id, intr.replacement_row, intr.replacement_col);
    if (!e) {
        return;
    }
    e.className = 'completion_menu_two completion_menu_selected';
    intr.replacement_word = $.trim($(e).text()) || intr.replacement_word;
}


function update_introspection_text(id, text) {
    /*
    Updates a cell's introspection text.

    INPUT:
        id -- integer or string; cell id
        text -- string; the new text
    */
    var d, intr = introspect[id];

    var introspect_div = $("#introspect_div_" + id);
    if (introspect_div.length == 0) {
        return;
    }
    
    if (intr.loaded) {
        introspect_div.html(text);
        try {
            MathJax.Hub.Queue(["Typeset",MathJax.Hub,introspect_div.get(0)]);
        } catch (e) {
            introspect_div.html('Error typesetting mathematics' + introspect_div.html());
        }

        introspect_div.find('.docstring').prepend('<div class="click-message" style="cursor: pointer">' + translations["Click here to pop out"] + '</div><div class="unprinted-note">' + translations["unprinted"] + '</div>');

        if (intr.replacing && !intr.docstring) {
            select_replacement_element(id, intr.replacement_row,
                                       intr.replacement_col);
        }
    } else {
        introspect_div.html(text);
    }
}


function halt_introspection(id) {
    /*
    Closes a cell's introspection "window" (completions menu or
    docstring).

    INPUT:
        id -- integer or string; cell id
    */
    var intr;
    id = toint(id);
    if (!introspect[id]) {
        introspect[id] = {};
    }
    intr = introspect[id];

    intr.loaded = false;
    update_introspection_text(id, '');

    intr.changed = false;
    intr.docstring = false;
    intr.replacing = false;
    intr.replacing_word = '';
    intr.replacement_word = '';
    intr.replacement_col = 0;
    intr.replacement_row = 0;
}


///////////////////////////////////////////////////////////////////
// Paren Matching
///////////////////////////////////////////////////////////////////
function paren_jump(cell, i, c, eat) {
    /*
    Replaces / inserts the desired paren, and moves the cursor to
    immediately after the paren.

    INPUT:
        cell -- a textarea object
        i -- integer; the index of where to insert/replace a paren
        c -- string; the character to insert (may be empty)
        eat -- boolean; whether or not to eat the character at i
    */
    var j = i;
    if (eat) {
        j += 1;
    }
    cell.value = cell.value.substring(0, i) + c + cell.value.substring(j);
    set_cursor_position(cell, i + c.length);
}


function paren_match(cell) {
    /*
    Fix parentheses / braces / brackets.  If mis-matched parentheses
    are found, fix them.  If an unmatched paren is found, insert it at
    the cursor.  This is implemented via a character-by-character
    lexer, so quotes and comments are handled appropriately.  Perhaps
    in the future this lexer will be generalized so it can be used for
    other stuff.

    EXAMPLES:  (the pipe character indicates cursor position)
        IN:
            this = some(sample.code(
                        "foo))",
            #           bar)),
                        baz|
        OUT:
            this = some.code(
                        "foo)",
            #           bar),
                        baz)|

        IN:
            foo = bar(baz(],a,b,c)|
        OUT:
            foo = bar(baz()|,a,b,c)

        IN:
            foo = bar()|
        OUT:
            foo = bar()|

        IN:
            foo = bar]bar()|
        OUT:
            foo = bar|bar()

        IN:
            foo = barbar).baz|
        OUT:
            foo = barbar|.baz

    INPUT:
        cell -- cell textarea
    OUTPUT:
        the text in the cell is possibly changed, and the cursor may
        move.
    */
    var c, comment = false, deparen = [], escape = false, i, n, p,
        pstack = [], quote = '', txt, squo = "'", dquo = '"', hash = "#",
        cr = '\n', esc = '\\', empty = '', lpar = '(', rpar = ')',
        lbrk = '[', rbrk = ']', lbrc = '{', rbrc = '}';

    deparen[lpar] = rpar;
    deparen[lbrc] = rbrc;
    deparen[lbrk] = rbrk;
    txt = cell.value.substring(0, get_cursor_position(cell));
    n = txt.length;

    for (i = 0; i < n; i += 1) {
        c = txt[i];
        if (quote !== empty) {
            if (escape) {
                escape = false;
            } else if (c === quote) {
                quote = empty;
            } else if (c === esc) {
                escape = true;
            }
        } else if (comment) {
            if (c === cr) {
                comment = false;
            }
        } else switch (c) {
        case lpar:
        case lbrc:
        case lbrk:
            pstack.push(c);
            break;
        case rpar:
        case rbrc:
        case rbrk:
            if (pstack.length <= 0) {
                paren_jump(cell, i, '', true);
                return;
            }
            p = pstack.pop();
            if (deparen[p] !== c) {
                paren_jump(cell, i, deparen[p], true);
                return;
            }
            break;
        case squo:
            quote = squo;
            break;
        case dquo:
            quote = dquo;
            break;
        case hash:
            comment = true;
            break;
        }
    }
    p = pstack.pop();
    i = txt.length;
    if (quote === empty && !comment && typeof(p) !== 'undefined') {
        paren_jump(cell, i, deparen[p], false);
    }
}


///////////////////////////////////////////////////////////////////
// WORKSHEET functions -- for switching between and managing 
// worksheets
///////////////////////////////////////////////////////////////////
function new_worksheet() {
    /*
    Ask the server to create a new worksheet, which is then opened
    replacing the current worksheet.
    */
    open("/new_worksheet");
}


function set_worksheet_list_checks() {
    /*
    Go through and set all check boxes the same as they are in the
    control box.  This is called when the user clicks the checkbox in
    the top left of the list of worksheets, which toggles all the
    checkboxes below it to be either on or off (select all or none).

    GLOBAL INPUT:
        worksheet_filenames -- list of strings
    */
    var C, i, id, X;
    C = get_element("controlbox");
    for (i = 0; i < worksheet_filenames.length; i += 1) {
        id = worksheet_filenames[i].replace(/[^\-A-Za-z_0-9]/g, '-');
        X = get_element(id);
        X.checked = C.checked;
    }
}


function checked_worksheet_filenames() {
    /*
    For each filename listed in worksheet_filenames, look up the
    corresponding input check box, see if it is checked, and if so,
    add it to the list.

    GLOBAL INPUT:
        worksheet_filenames -- list of strings
    OUTPUT:
        string of worksheet filenames that are checked, encoded as JSON
    */
    var i, id, X, checked_filenames = [];

    // Concatenate the list of all worksheet filenames that are
    // checked together separated by the separator string.
    for (i = 0; i < worksheet_filenames.length; i += 1) {
        id = worksheet_filenames[i].replace(/[^\-A-Za-z_0-9]/g, '-');
        X = get_element(id);
        if (X.checked) {
            checked_filenames.push(worksheet_filenames[i]);
            X.checked = 0;
        }
    }
    return encode_response(checked_filenames);
}


function worksheet_list_button(action) {
    /*
    For each filename listed in worksheet_filenames, look up the
    corresponding input check box, see if it is checked, and if so, do
    the corresponding action.

    INPUT:
        action -- URL that defines a message to send to the server
    GLOBAL INPUT:
        worksheet_filenames -- list of strings
    OUTPUT:
        calls the server and requests an action be performed on all
        the listed worksheets
    */
    // Send the list of worksheet names and requested action back to
    // the server.
    async_request(action, worksheet_list_button_callback, {
        filenames: checked_worksheet_filenames()
    });
}


function worksheet_list_button_callback(status, response) {
    /*
    Handle result of performing some action on a list of worksheets.

    INPUT:
        status, response -- standard AJAX return values
    OUTPUT:
        display an alert if something goes wrong; refresh this browser
        window no matter what.
    */
    if (status === 'success') {
        if (response !== '') {
            alert(response);
        }
    } else {
        alert(translations['Error applying function to worksheet(s).'] + response);
    }
    window.location.reload(true);
}


function delete_button() {
    /*
    This javascript function is called when the worksheet list delete
    button is pressed.  Each worksheet whose box is checked gets sent
    to the trash.
    */
    worksheet_list_button("/send_to_trash");
}


function make_active_button() {
    /*
    Sends each checked worksheet to the active worksheets folder.
    */
    worksheet_list_button("/send_to_active");
}


function archive_button() {
    /*
    Sends each checked worksheet to the archived worksheets folder.
    */
    worksheet_list_button("/send_to_archive");
}


function stop_worksheets_button() {
    /*
    Saves and then quits sage process for each checked worksheet.
    */
    worksheet_list_button("/send_to_stop");
}


function download_worksheets_button() {
    /*
    Downloads the set of checked worksheets as a zip file.
    */
    window.location.replace("/download_worksheets.zip?filenames=" +
                            checked_worksheet_filenames());
}


function history_window() {
    /*
    Display the history popup window, which displays the last few hundred
    commands typed into any worksheet.
    */
    window.open("/history", "", "menubar=1,scrollbars=1,width=800," +
                "height=600,toolbar=1,resizable=1");
}


function upload_worksheet_button() {
    /*
    Replace the current display window with the upload entry box.
    */
    window.location.replace("/upload");
}


function copy_worksheet() {
    /*
    Make a copy of the current worksheet then load the copy into the
    current frame.
    */
    window.location.replace(worksheet_command("copy"));
}


function download_worksheet() {
    /*
    Download the current worksheet to the file with name select by the
    user.  The title of the worksheet is also changed to match the
    filename.

    INPUT:
        base_filename
    */
    var title = prompt(translations['Title of saved worksheet'], worksheet_name), winref;
    if (title) {
        winref = open(worksheet_command("download/" + title + '.sws'));
    }
}


function worksheet_settings() {
    /*
    Bring up the worksheet settings menu.
    */
    window.location.replace(worksheet_command("settings"));
}


function share_worksheet() {
    /*
    Display the worksheet sharing window.
    */
    window.location.replace(worksheet_command("share"));
}


function publish_worksheet() {
    /*
    Public the current worksheet.
    */
    window.open(worksheet_command("publish"), "",
                "menubar=1,location=1,scrollbars=1,width=800," +
                "height=600,toolbar=1,  resizable=1");
}


function save_as(typ) {
    /*
    Save the current worksheet to a file.
    */
    open(worksheet_command('save_as') + '?typ=' + typ);
}

function save_worksheet() {
    /*
    Save a snapshot of the current worksheet.
    */
    async_request(worksheet_command('save_snapshot'), save_worksheet_callback);
}


function save_worksheet_callback(status, response) {
    /*
    Verify that saving the current worksheet worked.
    */
    if (status !== 'success') {
        alert(translations['Failed to save worksheet.']);
        return;
    }
}


function close_callback(status, response) {
    /*
    Called when we successfully close the current worksheet and want
    to display the user home screen (i.e., worksheet list).
    */
    if (status !== 'success') {
        alert(response);
        return;
    }
    window.location.replace('/home/' + user_name);
}


function save_worksheet_and_close() {
    /*
    Send message back to the server saving the current worksheet and
    quitting the Sage process, then close the current window returning
    to the home screen.
    */
    async_request(worksheet_command('save_and_quit'), close_callback);
}


function worksheet_discard() {
    /*
    Discard the current worksheet and quit the currently running Sage
    process, then close the current window and replace it by the home
    screen.
    */
    async_request(worksheet_command('discard_and_quit'), close_callback);
}


function rename_worksheet() {
    /*
    Rename the current worksheet.  This pops up a dialog that asks for
    the new worksheet name, then sets it in the browser, and finally
    sends a message back to the server stating that the worksheet has
    been renamed.
    */
    var callback = function (new_worksheet_name) {
        var title = $('#worksheet_title'), set_name;
        if (new_worksheet_name.length >= 30) {
            set_name = new_worksheet_name.slice(0, 30) + ' ...';
        } else {
            set_name = new_worksheet_name;
        }
        title.html(set_name);
        worksheet_name = new_worksheet_name;
        original_title = worksheet_name + ' (Sage)';
        document.title = original_title;
        async_request(worksheet_command('rename'), null, {
            name: new_worksheet_name
        });
    };
    modal_prompt({
        success: function (form, prompt) {
            callback($(':text', form).attr('value'));
        }
    }, {
        title: translations["Rename worksheet"],
        message: translations['Please enter a name for this worksheet.'],
        'default': worksheet_name,
        submit: translations["Rename"]
    });
}


function go_system_select(form, original_system) {
    /*
    Switch the current input system from one system to another (e.g.,
    form Sage to Pari or Python).  A confirmation box is displayed.

    INPUT:
        form -- DOM element; the drop down with the list of systems
        original_system -- string; the system we're switching *from*
     */
    system_select(form.options[form.selectedIndex].value);
}


function system_select(s) {
    /*
    Send a message back to the server stating that we're switching to
    evaluating all cells using the new system s.

    INPUT:
        s -- string
    */
    async_request(worksheet_command('system/' + s));
}


function pretty_print_check(s) {
    /*
    Send a message back to the server either turn pretty typeset
    printing on or off.

    INPUT:
        s -- boolean; whether the pretty print box is checked.
    */
    async_request(worksheet_command('pretty_print/' + s));
}


function handle_data_menu(form) {
    /*
    Handle what happens when the user clicks on the worksheet data
    menu and selects an option.

    INPUT:
    form -- DOM element; the form in the worksheet with the data
      drop down menu.
    */
    var value = form.options[form.selectedIndex].value;

    if (value === "__upload_data_file__") {
        window.location.replace(worksheet_command("upload_data"));
    } else if (value !== '') {
        window.location.replace("/home/" + worksheet_filename + "/" +
                                value);
    }
    form.options[0].selected = 1;
}


function delete_worksheet(name) {
    /*
    Send the worksheet with the given name to the trash.

    INPUT:
      name -- string
    */
    async_request('/send_to_trash', delete_worksheet_callback, {
        filename: name
    });
}


function delete_worksheet_callback(status, response) {
    /*
    Replace the current page by a page that shows the worksheet in the
    trash, or if the delete worksheet function failed display an
    error.
    */
    if (status === "success") {
        window.location.replace("/?typ=trash");
    } else {
        alert(translations['Possible failure deleting worksheet.']);
    }
}


///////////////////////////////////////////////////////////////////
// WORKSHEET list functions -- i.e., functions on a specific
// worksheet in the list of worksheets display.
///////////////////////////////////////////////////////////////////
function go_option(form) {
    /*
    This is called when the user selects a menu item.

    INPUT:
      form -- DOM element; the drop-down form element
    */
    var action = form.options[form.selectedIndex].value;
    // not safe, but more straigth forward than parsing
    // what is basically an eval string and running the 
    // corresponding function and arguments
    eval(action);
    form.options[0].selected = 1;
}


function link_datafile(target_worksheet_filename, filename) {
    /*
    Tell the server to create a symbolic link from the given data file
    to the target worksheet.  This is used to share data between
    multiple worksheets.

    INPUT:
       target_worksheet_filename -- string; the name of the worksheet
       to link this file to
       filename -- string; the name of this file
     */
    // TODO: What is process?
    open(worksheet_command("link_datafile?filename=" + escape0(filename) +
                           "&target=" + escape0(target_worksheet_filename)),
         process = false);
}


function list_rename_worksheet(filename, curname) {
    /*
    Prompt for a new worksheet name, then send the requested new name
    back to the server, thus changing the worksheet name.  Prompt for
    a new worksheet name, then send the requested new name back to the
    server, thus changing the worksheet name.

    INPUT:
        filename -- string; the filename of this worksheet to rename
        curname -- string; the current name of this worksheet
    */
    var callback = function (new_name) {
        async_request('/home/' + filename + '/' + 'rename', refresh, {
            name: new_name
        });
    };
    modal_prompt(function (form, prompt) {
        callback($(':text', form).attr('value'));
    }, {
        title: translations["Rename worksheet"],
        message: translations["Please enter a name for this worksheet."],
        'default': curname,
        submit: translations["Rename"]
    });
}


function list_edit_worksheet(filename) {
    /*
    In the list of all worksheets, when the user selects "Edit" from
    the menu to edit a worksheet, this function is called, which
    simply loads that worksheet.

    INPUT:
        filename -- string
    */
    window.location.replace('/home/' + filename);
}


function list_copy_worksheet(filename) {
    /*
    When the user selects "Copy" from the list of worksheets, this
    function is called.  It simply sends a message back to the server
    asking that a copy of the worksheet is made.  The worksheet list
    is then refreshed.

    INPUT:
        filename -- string; filename of the worksheet to share
    */
    async_request('/home/' + filename + '/copy?no_load', refresh);
}


function list_share_worksheet(filename) {
    /*
    Bring up menu that allows one to share the selected worksheet from
    the worksheet list with other users.

    INPUT:
        filename -- string; filename of the worksheet to share
    */
    window.location.replace('/home/' + filename + '/share');
}


function list_publish_worksheet(filename) {
    /*
    Publish the given worksheet, when this is selected from the
    worksheet list, and popup the published worksheet.

    INPUT:
        filename -- string; filename of the worksheet to share
    */
    window.open('/home/' + filename + '/publish', "",
                "menubar=1,scrollbars=1,width=800,height=600,toolbar=1,  resizable=1");
}


function list_revisions_of_worksheet(filename) {
    /*
    Display all revisions of the selected worksheet.  This brings up
    the revisions browser.

    INPUT:
        filename -- string; filename of the worksheet to share
    */
    window.location.replace('/home/' + filename + '/revisions');
}


///////////////////////////////////////////////////////////////////
// Server pinging support, so server knows page is being viewed.
///////////////////////////////////////////////////////////////////
function server_ping_while_alive() {
    /*
    Ping the server every server_ping_time milliseconds to announce
    that we are still viewing this page.
    */
    async_request(worksheet_command('alive'), server_ping_while_alive_callback);
    setTimeout(function () {
        server_ping_while_alive();
    }, server_ping_time);
}


function server_ping_while_alive_callback(status, response) {
    /*
    Whenever the server ping callback occurs, this function runs, and
    setsif the server didn't respond it calls server_down(); otherwise it
    calls server_up().

    Also, each time the server is up and responds, the server includes
    the worksheet state_number is the response.  If this number is out
    of sync with our view of the worksheet state, then we force a
    refresh of the list of cells.  This is very useful in case the
    user uses the back button and the browser cache displays an
    invalid worksheet list (which can cause massive confusion), or the
    user open the same worksheet in multiple browsers, or multiple
    users open the same shared worksheet.
    */
    if (status === "failure") {
        set_class('ping', 'pingdown');
    } else {
        set_class('ping', 'ping');
        if (state_number >= 0 && parseInt(response, 10) > state_number) {
            // Force a refresh of just the cells in the body.
            refresh_cell_list();
        }
    }
}


///////////////////////////////////////////////////////////////////
// CELL functions -- for the individual cells
///////////////////////////////////////////////////////////////////
function get_cell(id) {
    /*
    Returns a cell's input textarea.

    INPUT:
        id -- integer or string; cell id
    OUTPUT:
        a DOM element or null
    GLOBAL INPUT:
        cell_element_cache -- an associative array that maps ids to
        elements
    */
    var v;
    id = toint(id);

    // TODO: Just use jQuery with context?
    v = cell_element_cache[id];
    if (!v) {
        v = get_element('cell_input_' + id);
        cell_element_cache[id] = v;
    }
    return v;
}


function cell_blur(id) {
    /*
    This function is called when the cell with the given id is
    blurred.  It removes whitespace around the input, and if the cell
    has changed sends the changed input back to the server.

    INPUT:
        id -- integer or string; cell id
    OUTPUT:
       true -- to avoid infinite recursion.
    */
    var cell, v;

    id = toint(id);
    cell = get_cell(id);
    if (!cell) {
        return true;
    }

    // Set the style back to the non-active input cell
    cell.className = 'cell_input';

    // If cell starts with %hide, hide the input.
    v = lstrip(cell.value).slice(0, 5);
    if (v === '%hide') {
        cell.className = 'cell_input_hide';
        cell.style.height = '1em';
    }

    if (cell_has_changed) {
        send_cell_input(id);
    }

    // It is very important to return true here, or one gets an
    // infinite javascript recursion.
    return true;
}


function send_cell_input(id) {
    /*
    Send the input text of the current cell back to the server.  This
    is typically called when the cursor leaves the current cell.

    INPUT:
       id -- an integer or string; cell id
    OUTPUT:
       makes an async call back to the server sending the input text.
    */
    var cell = get_cell(id);
    if (!cell) {
        return;
    }

    // When the input changes we set the CSS to indicate that the cell
    // with this new text has not been evaluated.
    cell_set_not_evaluated(id);

    async_request(worksheet_command('eval'), null, {
        save_only: 1,
        id: id,
        input: cell.value
    });
}


function evaluate_text_cell_input(id, value, settings) {
    /*
    Send the input text of the current cell back to the server.

    INPUT:
       id -- integer or string; cell id
       value -- string; new cell contents
       settings -- object
    OUTPUT:
       makes an async call back to the server sending the input text.
    */
    async_request(worksheet_command('eval'), evaluate_text_cell_callback, {
        text_only: 1,
        id: id,
        input: value
    });
    //update jmol applet list
    jmol_delete_check();
}


function evaluate_text_cell_callback(status, response) {
    /*
    Display the new content of a text cell, parsing for math if
    needed.

    INPUT:
        status -- string
        response -- string; encoded JSON object with parsed keys

             id -- string or integer; evaluated cell's id
             cell_html -- string; the cell's updated contents
    */
    var new_html, text_cell, X;
    if (status === "failure") {
        // Failure evaluating a cell.
        return;
    }
    X = decode_response(response);

    if (X.id === -1) {
        // Something went wrong, e.g., the requested cell doesn't
        // exist.
        alert(translations['You requested to evaluate a cell that, for some reason, the server is unaware of.']);
        return;
    }

    text_cell = get_element('cell_outer_' + X.id);
    new_html = separate_script_tags(X.cell_html);
    $(text_cell).replaceWith(new_html[0]);
    // Get the new text cell.
    text_cell = get_element('cell_outer_' + X.id);
    setTimeout(new_html[1], 50);

    try { MathJax.Hub.Queue(["Typeset",MathJax.Hub,text_cell]); 
	} catch (e) { text_cell.innerHTML = 'Error typesetting mathematics' + text_cell.innerHTML; }
}


function cell_focus(id, leave_cursor) {
    /*
    Set the focus on the cell with the given id.

    INPUT:
        id -- integer or string; cell id
        leave_cursor -- boolean; whether to move the cursor to the top
        left of the input cell
    OUTPUT:
        focuses on a given cell, possibly moves the cursor, and sets
        the global variable cell_has_changed to false, since we have
        just entered this cell and it hasn't been changed yet.
    */
    var cell;

    id = toint(id);
    cell = get_cell(id);

    if (!cell) {
        return true;
    }

    // Focus on the cell with the given id and resize it.
    cell_input_resize(id);
    cell.focus();

    // Possibly also move the cursor to the top left in this cell.
    if (!leave_cursor) {
        set_cursor_position(cell, 0);
    }
    // Set since we're now in a new cell, whose state hasn't changed
    // yet.
    cell_has_changed = false;
    return true;
}


function cell_focused(cell, id) {
    /*
    This function is called when the cell gets focus.  It sets the CSS
    so that the input part of the cell is highlighted.

    INPUT:
        cell -- DOM element
        id -- integer or string; cell id
    OUTPUT:
        sets the global variable current_cell and update display of
        the evaluate link.
    */
    id = toint(id);

    cell.className = "cell_input_active";

    // This makes sure the input textarea is resized right when it is
    // clicked on.
    cell_input_resize(id);

    if (current_cell === id) {
        return;
    }
    if (current_cell !== -1) {
        set_class("eval_button" + current_cell, "eval_button");
    }
    current_cell = id;
    set_class("eval_button" + id, "eval_button_active");
}


function cell_input_resize(id) {
    /*
    Resize the given input cell so that it has the right number of
    rows for the number of rows currently typed into the input cell.

    INPUT:
        id -- integer or string; cell id
    OUTPUT:
        changes the height of the corresponding DOM object to fit the
        input

    ALGORITHM:
        Create a hidden div with the same style as the textarea, then
        copy all the text into it, set the height of the textarea in
        pixels based on the height of the div, then delete the div.
    */
    var cell_input = get_cell(id), resizer = get_element('cell_resizer');

    if (!cell_input) {
        return;
    }

    // TODO: This isn't quite accurate for the most common sorts of
    // input cells.  In particular, backslashes appear to cause
    // miscalculation.  Perhaps scrollTop is a viabl alternative?
    resizer.style.width = cell_input.offsetWidth + 'px';
    resizer.innerHTML = cell_input.value
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/\r?\n/g, '<br>')
        .replace(/\s\s/g, ' &nbsp;') + '&nbsp;';

    cell_input.style.height = resizer.offsetHeight + 'px';

    if (slide_hidden) {
        cell_input.className = "cell_input_active";
        slide_hidden = false;
    }
    return;
}


function cell_delete(id) {
    /*
    Send a request back to the server that we would like to delete the
    cell with given id.

    INPUT:
        id -- integer or string; cell id
    */
    if ($.inArray(id, queue_id_list) !== -1) {
        // Deleting a running cell causes evaluation to be
        // interrupted.  In most cases this avoids potentially tons of
        // confusion.
        async_request(worksheet_command('interrupt'));
    }
    async_request(worksheet_command('delete_cell'), cell_delete_callback, {
        id: id
    });
    //update jmol applet list
    jmol_delete_check();
}


function cell_delete_callback(status, response) {
    /*
    Deletes a cell (removes it from the DOM and cell_id_list),
    depending on the server response.

    INPUT:

        status -- string
        response -- string; encoded JSON object with parsed keys

            id -- string or integer; deleted cell's id
            command -- string; 'delete' (delete the cell) or 'ignore'
            (do nothing)
            prev_id -- string or integer; id of preceding cell
            cell_id_list -- list; updated cell id list

    */
    var cell, X;

    if (status === "failure") {
        return;
    }

    X = decode_response(response);

    if (X.command === 'ignore') {
        // Don't delete, e.g., if there's only one compute cell left.
        return;
    }


    cell = get_element('cell_outer_' + X.id);
    if (!cell) {
        return;
    }
    get_element('worksheet_cell_list').removeChild(cell);
    cell_id_list.splice($.inArray(X.id, cell_id_list), 1);
    delete introspect[X.id];
    delete cell_element_cache[X.id];

    // If we are in slide mode, we call slide_mode() again to
    // recalculate the slides.
    if (in_slide_mode) {
        current_cell = -1;
        slide_mode();
    //update jmol applet list
    jmol_delete_check();

    }
}


function cell_delete_output(id) {
    /*
    Ask the server to delete the output of a cell.

    INPUT:
        id -- integer or string; cell id
    */
    id = toint(id);

    if ($.inArray(id, queue_id_list) !== -1) {
        // Deleting a running cell causes evaluation to be interrupted.
        // In most cases this avoids potentially tons of confusion.
        async_request(worksheet_command('interrupt'));
    }
    async_request(worksheet_command('delete_cell_output'),
                  cell_delete_output_callback, {
                      id: id
                  });
    //update jmol applet list
    jmol_delete_check();

}


function cell_delete_output_callback(status, response) {
    /*
    Callback for after the server deletes a cell's output.  This
    function removes the cell's output from the DOM.

    INPUT:
        status -- string ('success' or 'failure')
        response -- [command]SEP[id]
               command -- string ('delete_output')
               id -- id of cell whose output is deleted.
    */
    var X;
    if (status !== 'success') {
        // Do not delete output, for some reason.
        return;
    }
    X = decode_response(response);

    // Delete the output.
    get_element('cell_output_' + X.id).innerHTML = "";
    get_element('cell_output_nowrap_' + X.id).innerHTML = "";
    get_element('cell_output_html_' + X.id).innerHTML = "";

    // Set the cell to not evaluated.
    cell_set_not_evaluated(X.id);
    //update list of jmol applets
    jmol_delete_check();
}


function cell_input_key_event(id, e) {
    /*
    This function is called each time a key is pressed when the cursor
    is inside an input cell.

    INPUT:
        id -- integer or string; cell id
        e -- key event
    GLOBAL_INPUT:
        control_key_pressed -- used to detect if the control key was
        pressed; this is really only relevant to handling Opera's
        quirky even model.
    OUTPUT:
        All kinds of interesting things can happen:
            - introspection
            - cell join
            - cell split
            - cell delete
            - a cell may be evaluated
    */
    // TODO: Use js-hotkeys?
    var after, before, cell_input, i, selection_is_empty, selection_range;

    if (browser_iphone) {
        return;
    }

    e = new key_event(e);
    if (!e) {
        return;
    }

    /*********** SPLIT AND JOIN HANDLING ********/

    // Record that just the control key was pressed.  We do this since
    // on Opera it is the only way to catch control + key.
    if (key_control(e)) {
        control_key_pressed = 1;
        return;
    }

    id = toint(id);
    // Check for the split and join keystrokes.  The extra
    // control_key_pressed cases are needed for Safari.
    if (key_split_cell(e) ||
        (key_split_cell_noctrl(e) && control_key_pressed)) {
        doing_split_eval = false;
        split_cell(id);
        return false;
    } else if (key_spliteval_cell(e) ||
               (key_enter(e) && control_key_pressed)) {
        doing_split_eval = true;
        jump_to_cell(id, 1);
        control_key_pressed = 0;
        split_cell(id);
        return false;
    } else if (key_join_cell(e) ||
               (key_delete_cell(e) && control_key_pressed) ||
               (key_delete_cell(e) && is_whitespace(get_cell(id).value))) {
        control_key_pressed = 0;
        join_cell(id);
        return false;
    }

    // Turn off recording that the control key may have pressed last,
    // since we *only* would use that in the above if statement.
    // NOTE: This is only needed on Opera.
    control_key_pressed = 0;

    /*********** END of SPLIT AND JOIN HANDLING ********/

    cell_input = get_cell(id);

    if (introspect[id].loaded &&
        !handle_introspection(id, cell_input, e)) {
        return false;
    }

    selection_range = get_selection_range(cell_input);
    selection_is_empty = (selection_range[0] === selection_range[1]);

    // Will need IE version... if possible.
    if (!in_slide_mode && key_up_arrow(e) && selection_is_empty) {
        before = cell_input.value.substring(0, selection_range[0]);
        i = before.indexOf('\n');
        if (i === -1 || before === '') {
            jump_to_cell(id, -1, true);
            return false;
        } else {
            return true;
        }
    } else if (!in_slide_mode && key_down_arrow(e) && selection_is_empty) {
        after = cell_input.value.substring(selection_range[0]);
        i = after.indexOf('\n');
        if ((i === -1 || after === '') && id !== extreme_compute_cell(-1)) {
            jump_to_cell(id, 1);
            return false;
        } else {
            return true;
        }
    } else if (key_send_input(e)) {
        // User pressed shift-enter (or whatever the submit key is).
        doing_split_eval = false;
        evaluate_cell(id, false);
        return false;
    } else if (key_send_input_newcell(e)) {
        doing_split_eval = false;
        evaluate_cell(id, true);
        return false;
    } else if (key_comment(e) && !selection_is_empty) {
        return comment_cell(cell_input);
    } else if (key_uncomment(e) && !selection_is_empty) {
        return uncomment_cell(cell_input);
    } else if (key_unindent(e)) {
        // Unfortunately, shift-tab needs to get caught before
        // not-shift tab.
        unindent_cell(cell_input);
        return false;
    } else if (key_request_introspections(e) && selection_is_empty) {
        // Introspection: tab completion, ?, ??.
        evaluate_cell_introspection(id, null, null);
        return false;
    } else if (key_indent(e) && !selection_is_empty) {
        indent_cell(cell_input);
        return false;
    } else if (key_interrupt(e)) {
        interrupt();
        return false;
    } else if (key_page_down(e)) {
        if (in_slide_mode) {
            slide_next();
        } else {
            jump_to_cell(id, 5);
        }
        return false;
    } else if (key_page_up(e)) {
        if (in_slide_mode) {
            slide_prev();
        } else {
            jump_to_cell(id, -5);
        }
        return false;
    } else if (key_request_history(e)) {
        history_window();
    } else if (key_request_log(e)) {
        // TODO: Write a function text_log_window or do ...?
        text_log_window(worksheet_filename);
    } else if (key_fix_paren(e)) {
        paren_match(cell_input);
        return false;
    }

    // An actual non-controlling character was sent, which means this
    // cell has changed.  When the cursor leaves the cell, we'll use
    // this to know to send the changed version back to the server.
    // We do still have to account for the arrow keys which don't
    // change the text.
    if (! (key_up_arrow(e) || key_down_arrow(e) ||
           key_menu_right(e) || key_menu_left(e))) {
        cell_has_changed = true;
        introspect[id].changed = true;
    }

    return true;
}


function is_compute_cell(id) {
    /*
    Return true precisely if the input id is the id of a compute cell.

    INPUT:
        id -- integer or string; cell id
    */
    return (get_cell(id) !== null);
}


function extreme_compute_cell(dir) {
    /*
    Return the id of the first or last compute cell.

    INPUT:
        dir -- integer; the direction: if 1 (not 1) return the first
        (last) compute cell's id
    OUTPUT:
        id -- integer or string; the first or last compute cell's id
    */
    var i, id, len = cell_id_list.length;
    if (dir === 1) {
        for (i = 0; i < len; i += 1) {
            id = cell_id_list[i];
            if (is_compute_cell(id)) {
                break;
            }
        }
    } else {
        for (i = len - 1; i > -1; i -= 1) {
            id = cell_id_list[i];
            if (is_compute_cell(id)) {
                break;
            }
        }
    }
    return id;
}


function id_of_cell_delta(id, delta, all_cells) {
    /*
    Return the id of the cell that is delta positions from the cell
    with given id, where delta is an integer, either positive,
    negative, or 0.

    INPUT:
        id -- integer or string; cell id
        delta -- integer; offset "index"
        all_cells -- boolean; whether to ignore non-compute cells
    OUTPUT:
        integer or string
    */
    var i, j, len = cell_id_list.length, s;

    if (len === 0) {
        return;
    }
    if (!delta || delta === 0) {
        return id;
    }

    i = $.inArray(id, cell_id_list);
    if (i === -1) {
        return id;
        // Better not to move.
    } else {
        if (delta < 0) {
            delta = -delta;
            s = -1;
        } else {
            s = 1;
        }
        for (j = 0; j < delta; j += 1) {
            i = i + s;
            while (!all_cells && i >= 0 && i < len &&
                   !is_compute_cell(cell_id_list[i])) {
                i = i + s;
            }
        }
        if (i < 0) {
            i = 0;
        } else if (i >= len) {
            i = len - 1;
        }
        if (!all_cells && !is_compute_cell(cell_id_list[i])) {
            return id;
        }
        return cell_id_list[i];
    }
}

function jump_to_cell(id, delta, bottom) {
    /*
    Put the focus and cursor in the cell that is positioned delta
    spots above or below the cell with given id.  If bottom is true
    the cursor is positioned at the bottom of the cell that is put in
    focus.

     INPUT:
         id -- integer or string; cell id
         delta -- integer; offset "index"
         bottom -- boolean; whether to put cursor at end of cell
     GLOBAL INPUT:
         ignore_next_jump -- if this variable is set globally to true,
         then this function immediately returns after setting it to
         false.  This is used because several functions create new
         cells with unknown id's then jump to them (example, when
         inserting a new cell after the current one).  In some cases,
         e.g., when splitting or joining cells, it is necessary to
         temporarily disable this behavior, even though we do call
         those functions.  This is done by simply setting
         ignore_next_jump to true.
     OUTPUT:
         Changes the focused cell.  Does not send any information back
         to the server.
     */
    if (ignore_all_jumps) {
        return;
    }

    if (ignore_next_jump) {
        ignore_next_jump = false;
        return;
    }

    if (delta && delta !== 0) {
        id = id_of_cell_delta(id, delta);
    }

    if (in_slide_mode) {
        jump_to_slide(id);
    } else {
        cell_focus(id, bottom);
    }
}


function escape0(input) {
    /*
    Escape the string for sending via a URL; also replace all +'s by
    %2B.

    INPUT:
        input -- string
    OUTPUT:
        a string
    */
    //TODO: Use the built-in encodeURIComponent function.
    input = escape(input);
    input = input.replace(/\+/g, "%2B");
    return input;
}


function text_cursor_split(cell) {
    /*
    Returns a pair of substrings, the first from the start of the cell
    to the cursor position, and the second from the cursor position to
    the end of the cell.

    INPUT:
        cell -- DOM textarea; an input cell
    OUTPUT:
        array of two strings
    */
    var a, b, R = get_selection_range(cell);
    b = cell.value.substr(0, R[1]);
    a = cell.value.substr(b.length);
    return [b, a];
}


function indent_cell(cell) {
    /*
    Indent all the highlighted text in the given input cell by 4
    spaces.

    INPUT:
        cell -- DOM textarea; an input cell
    */
    var a, b, c, i, lines, R = get_selection_range(cell), start;

    start = 1 + cell.value.lastIndexOf("\n", R[0]);
    a = cell.value.substring(0, start);
    b = cell.value.substring(start, R[1]);
    c = cell.value.substring(R[1]);

    lines = b.split("\n");

    for (i = 0; i < lines.length; i += 1) {
        lines[i] = "    " + lines[i];
    }

    b = lines.join("\n");

    cell.value = a + b + c;
    set_selection_range(cell, a.length, a.length + b.length);
}


function unindent_cell(cell) {
    /*
    Unindent the current line or highlighted text in the given input cell
    by 4 spaces.

    INPUT:
        cell -- DOM textarea; an input cell
    */
    var a, b, c, i, lines, R = get_selection_range(cell), start;

    start = 1 + cell.value.lastIndexOf("\n", R[0]);
    a = cell.value.substring(0, start);
    b = cell.value.substring(start, R[1]);
    c = cell.value.substring(R[1]);

    lines = b.split("\n");

    for (i = 0; i < lines.length; i += 1) {
        // Square brackets pull the captured pattern.
        lines[i] = unindent_pat.exec(lines[i])[1];
    }

    b = lines.join("\n");

    cell.value = a + b + c;
    if (R[0] === R[1]) { // nothing is selected
        set_cursor_position(cell, a.length + b.length);
    } else {
        set_selection_range(cell, a.length, a.length + b.length);
    }
}


function comment_cell(cell) {
    /*
    Comment out all the highlighted (selected) text in the given input
    cell.

    INPUT:
        cell -- DOM textarea; an input cell
    */
    var a, b, c, i, lines, R = get_selection_range(cell), start;

    if (R[0] === R[1]) {
        return true;
    }

    start = 1 + cell.value.lastIndexOf("\n", R[0]);
    a = cell.value.substring(0, start);
    b = cell.value.substring(start, R[1]);
    c = cell.value.substring(R[1]);

    lines = b.split("\n");

    for (i = 0; i < lines.length; i += 1) {
        lines[i] = "#" + lines[i];
    }

    b = lines.join("\n");

    cell.value = a + b + c;
    set_selection_range(cell, a.length, a.length + b.length);
}


function uncomment_cell(cell) {
    /*
    Uncomment the highlighted (selected) text in the given input cell.

    INPUT:
        cell -- DOM textarea; an input cell
    */
    var a, b, c, i, lines, m, R = get_selection_range(cell), start;

    if (R[0] === R[1]) {
        return true;
    }

    start = 1 + cell.value.lastIndexOf("\n", R[0]);
    a = cell.value.substring(0, start);
    b = cell.value.substring(start, R[1]);
    c = cell.value.substring(R[1]);

    lines = b.split("\n");

    for (i = 0; i < lines.length; i += 1) {
        m = uncomment_pat.exec(lines[i]);
        lines[i] = m[1] + m[2];
    }

    b = lines.join("\n");

    cell.value = a + b + c;
    set_selection_range(cell, a.length, a.length + b.length);
}


function join_cell(id) {
    /*
    Join the cell with given id to the cell before it.

    The output of the resulting joined cells is the output of the
    second cell, *unless* the input of the second cell is only
    whitespace, in which case the output is the output of the first
    cell.  We do this since a common way to delete a cell is to empty
    its input, then hit backspace.  It would be very confusing if the
    output of the second cell were retained.  WARNING: Backspace on
    the first cell if empty deletes it.

    INPUT:
        id -- integer or string; cell id.
    OUTPUT:
        change the state of the worksheet in the DOM, global
        variables, etc., and updates the server on this change.
    */
    var cell, cell_next, cell_prev, id_prev, n, val_prev;

    id_prev = id_of_cell_delta(id, -1);
    cell = get_cell(id);

    // The top cell is a special case.  Here we delete the top cell if
    // it is empty.  Otherwise, we simply return doing nothing.
    if (id_prev === id) {
        // Yes, top cell.
        if (is_whitespace(cell.value)) {
            // Special case -- deleting the first cell in a worksheet
            // and its whitespace get next cell
            cell_next = get_cell(id_of_cell_delta(id, 1));
            // Put cursor on next one.
            cell_next.focus();
            // Delete this cell.
            cell_delete(id);
            return;
        } else {
            return;
        }
    }

    cell_prev = get_cell(id_prev);

    // We delete the cell above the cell with given id except in the
    // one case when the cell with id has empty input, in which case
    // we just delete that cell.
    if (is_whitespace(cell.value)) {
        cell_prev.focus();
        cell_delete(id);
        return;
    }

    // The lower cell in the join is now not empty.  So we delete the
    // previous cell and put its contents in the bottom cell.
    val_prev = cell_prev.value;

    cell.focus();
    cell_delete(id_prev);

    // The following is so that joining two cells keeps a newline
    // between the input contents.
    n = val_prev.length;
    if (val_prev[n - 1] !== '\n') {
        val_prev += '\n';
        n += 1;
    }
    cell.value = val_prev + cell.value;

    // Send a message back to the server reporting that the cell has
    // changed (as a result of joining).
    send_cell_input(id);

    // Set the cursor position in the joined cell to about where it
    // was before the join.
    set_cursor_position(cell, n);

    // Finally resize the joined cell to account for its new text.
    cell_input_resize(id);
}


function split_cell(id) {
    /*
    Split the cell with the given id into two cells, inserting a new
    cell after the current one and placing the cursor at the beginning
    of the new cell.

    INPUT:
        id -- integer or string; cell id
    OUTPUT:
        changes the state of the worksheet, DOM, and sends a message
        back to the server.
    */
    var cell = get_cell(id), txt = text_cursor_split(cell);

    if (txt[1].length > 0 && txt[1][0] === '\n') {
        txt[1] = txt[1].slice(1);
    }

    cell.value = txt[1];
    cell_input_resize(id);
    send_cell_input(id);
    // Tell the server about how the input just got split in half.

    set_cursor_position(cell, 0);

    // Make sure that the cursor doesn't move to the new cell.
    ignore_next_jump = true;
    insert_new_cell_before(id, txt[0]);
}


function worksheet_command(cmd) {
    /*
    Create a string formatted as a URL to send back to the server and
    execute the given cmd on the current worksheet.

    INPUT:
        cmd -- string
    OUTPUT:
        a string
    */
    if (cmd === 'eval' 
	|| cmd === 'new_cell_before' 
	|| cmd === 'new_cell_after'
	|| cmd === 'new_text_cell_before'
	|| cmd === 'new_text_cell_after') {
        state_number = parseInt(state_number, 10) + 1;
    }
    // worksheet_filename differs from actual url for public interacts
    // users see /home/pub but worksheet_filename is /home/_sage_
    return ('/home/' + worksheet_filename + '/' + cmd);
}


function evaluate_cell(id, newcell) {
    /*
    Evaluates a cell.

    INPUT:
        id -- integer or string; cell id
        newcell -- boolean; whether to request insertion of a new cell
                   after the current one
    */
    var cell_input;

    if (worksheet_locked) {
        alert(translations['This worksheet is read only. Please make a copy or contact the owner to change it.']);
        return;
    }

    // Does the input cell exist?
    id = toint(id);
    cell_input = get_cell(id);
    if (!cell_input) {
        return;
    }

    // Request a new cell to insert after this one?
    newcell = (newcell || (id === extreme_compute_cell(-1))) ? 1 : 0;
    if (evaluating_all) {
        newcell = 0;
    }

    // Don't resend the input to the server upon leaving focus (see
    // send_cell_input).
    cell_has_changed = false;

    // Ask the server to start computing.
    async_request(worksheet_command('eval'), evaluate_cell_callback, {
        newcell: newcell,
        id: id,
        input: cell_input.value
    });
    //update jmol applet list
    jmol_delete_check();

}


function evaluate_cell_introspection(id, before, after) {
    /*
    Runs introspection in a cell.

    INPUT:
        id -- integer or string; the id a cell
        before -- null or string; all text before the cursor
        after -- null or string; all text after the cursor
    OUTPUT:
        sends a message back to the server to do an introspection on
        this cell; also set the cell running.
    */
    var cell_input, f, in_text, intr, m;
    id = toint(id);
    intr = introspect[id];
    cell_input = get_cell(id);

    if (before === null) {
        // We're starting from scratch.
        halt_introspection(id);

        in_text = text_cursor_split(cell_input);
        before = in_text[0];
        after = in_text[1];
        intr.before_replacing_word = before;
        intr.after_cursor = after;

        m = command_pat.exec(before);
        f = function_pat.exec(before);

        if (before.slice(-1) === "?") {
            // We're starting with a docstring or source code.
            intr.docstring = true;
        } else if (m) {
            // We're starting with a list of completions.
            intr.replacing = true;
            intr.replacing_word = m[1];
            intr.before_replacing_word = before.substring(0, before.length -
                                                          m[1].length);
        } else if (f !== null) {
            // We're in an open function paren -- give info on the
            // function.
            before = f[1] + "?";
            // We're starting with a docstring or source code.
            intr.docstring = true;
        } else {
            // Just a tab.
            cell_has_changed = true;
            do_replacement(id, '    ', false);
            return;
        }
    }

    async_request(worksheet_command('introspect'), evaluate_cell_callback, {
        id: id,
        before_cursor: before,
        after_cursor: after
    });
}


function evaluate_cell_callback(status, response) {
    /*
    Updates the queued cell list, marks a cell as running, changes the
    focus, inserts a new cell, and/or evaluates a subsequent cell,
    depending on the server response.  Also starts the cell update
    check.

    INPUT:
        status -- string
        response -- string; encoded JSON object with parsed keys

            id -- string or integer; evaluated cell's id
            command -- string; 'insert_cell', 'no_new_cell', or
            'introspect'
            next_id -- optional string or integer; next cell's id
            interact -- optional boolean; whether we're updating an
            interact
            new_cell_html -- optional string; new cell's contents
            new_cell_id -- optional string or integer; id of new cell
            to create

    */
    var X;
    if (status === "failure") {
        // alert("Unable to evaluate cell.");
        return;
    }

    X = decode_response(response);
    X.interact = X.interact ? true : false;

    if (X.id === -1) {
        // Something went wrong, e.g., the evaluated cell doesn't
        // exist.  TODO: Can we remove this?
        return;
    }

    if (X.command && (X.command.slice(0, 5) === 'error')) {
	// TODO: (Re)use an unobtrusive jQuery UI dialog.
    // console.log(X, X.id, X.command, X.message);
        return;
    }

    // Given a "successful" server response, we update the queued cell
    // list and mark the cell as running.
    queue_id_list.push(X.id);
    cell_set_running(X.id, X.interact);

    function go_next(evaluate, jump) {
        // Helper function that evaluates and/or jumps to a suggested
        // or the next compute cell, unless it's the current cell or
        // we're just updating an interact.
        var i, id, candidates = [X.next_id, id_of_cell_delta(X.id, 1)];

        if (X.interact) {
            return true;
        }
        for (i = 0; i < candidates.length; i += 1) {
            id = candidates[i];
            if (id !== X.id && is_compute_cell(id)) {
                if (evaluate) {
                    evaluate_cell(id, false);
                }
                if (jump) {
                    jump_to_cell(id, 0);
                }
                return true;
            }
        }
        return false;
    }

    if (evaluating_all) {
        // Evaluate the suggested next cell, another cell, or stop.
        if (!go_next(true, false)) {
            evaluating_all = false;
        }
    }

    if (X.command === 'insert_cell') {
        // Insert a new cell after the evaluated cell.
        do_insert_new_cell_after(X.id, X.new_cell_id, X.new_cell_html);
        jump_to_cell(X.new_cell_id, 0);
    } else if (X.command === 'introspect') {
	    introspect[X.id].loaded = false;
	    update_introspection_text(X.id, 'loading...');
    } else if (in_slide_mode || doing_split_eval ||
	           is_interacting_cell(X.id)) {
        // Don't jump.
    } else {
        // "Plain" evaluation.  Jump to a later cell.
        go_next(false, true);
    }

    start_update_check();
    //update jmol applet list
    jmol_delete_check();

}


function is_interacting_cell(id) {
    /*
    Return true if the cell with given id is currently an @interact
    cell.

    INPUT:
        id -- integer or string; cell id
    OUTPUT:
        boolean
    */
    return (get_element("cell-interact-" + id) !== null);
}


function cell_output_set_type(id, typ, do_async) {
    /*
    Set the output type of the cell with given id.

    INPUT:
        id -- integer or string; cell id
        typ -- string; 'wrap', 'nowrap', 'hidden'
        do_async -- boolean; whether to inform the server
    */

    // We do the following specifically because interact cells do not
    // work at all when displayed in nowrap mode, which is VERY BAD.
    // So instead for interacts one gets a toggle to and from hidden.
    if (typ === "nowrap" && is_interacting_cell(id)) {
        // If the type is nowrap and the cell-interact-[id] div exists
        // (i.e., we are interacting) then just make the thing hidden.
        typ = "hidden";
    }

    /* OK, now set the cell output type. */
    set_class('cell_div_output_' + id, 'cell_div_output_' + typ);
    set_class('cell_output_' + id, 'cell_output_' + typ);
    set_class('cell_output_nowrap_' + id, 'cell_output_nowrap_' + typ);
    set_class('cell_output_html_' + id, 'cell_output_html_' + typ);

    // Do async request back to the server.
    if (do_async) {
        async_request(worksheet_command('set_cell_output_type'), null, {
            id: id,
            type: typ
        });
    }
}


function cycle_cell_output_type(id) {
    /*
    When called the cell with given id has its output cycled from one
    type to the next.  There are three types: word wrap, no word wrap,
    hidden.

    INPUT:
        id -- integer or string; cell id
    */
    var cell_div;
    id = toint(id);
    cell_div = get_element('cell_div_output_' + id);

    if (cell_div.className === 'cell_div_output_hidden' ||
        cell_div.className === 'cell_div_output_running') {
        cell_output_set_type(id, 'wrap');
        return;
    }

    if (cell_div.className === 'cell_div_output_wrap') {
        cell_output_set_type(id, 'nowrap');
    } else {
        cell_output_set_type(id, 'hidden');
    }
}


function cell_set_evaluated(id) {
    /*
    Set the cell with given id to be evaluated.  This is purely a CSS
    style setting.

    INPUT:
        id -- integer or string; cell id
    */
    var D = get_element('cell_' + id);
    D.className = "cell_evaluated";
}


function cell_set_not_evaluated(id) {
    /*
    Set the cell with given id to be not evaluated.  This is purely a
    CSS style setting.

    INPUT:
        id -- integer or string; cell id
    */
    var D = get_element('cell_' + id);
    D.className = "cell_not_evaluated";
    cell_set_done(id);
}


function cell_set_running(id, interact) {
    /*
    Clears a cell's output and marks it as running.  This does not
    contact the server.

    INPUT:
        id -- integer or string; cell id
        interact -- boolean; whether we're just updating an interact
    */
    var cell_div, cell_number, out;
    id = toint(id);

    if (interact) {
        // Delete links to files output by earlier computations.
        out = get_element('cell_output_html_' + id);
        if (out) {
            out.innerHTML = '';
        }
    } else {
        // Delete all output. The true means not @interact.
        set_output_text(id, '', '', '', '', '', true);

        // If the output type is hidden, make it visible.
        cell_div = get_element('cell_div_output_' + id);
        if (cell_div.className ===  'cell_div_output_hidden') {
            cycle_cell_output_type(id);
        }
        // Now set it running.
        cell_div.className = 'cell_output_running';
    }

    cell_number = get_element('cell_number_' + id);
    cell_number.className = 'cell_number_running';
}


function cell_set_done(id) {
    /*
    Change the CSS for the cell with given id to indicate that it is
    no longer computing.

    INPUT:
        id -- integer or string; cell id
    */
    var cell_div, cell_number;

    cell_div = get_element('cell_div_output_' + id);
    cell_div.className = 'cell_div_output_wrap';
    cell_number = get_element('cell_number_' + id);
    cell_number.className = 'cell_number';
}


function check_for_cell_update() {
    /*
    Ask the server if there is any new output that should be placed in
    an output cell.

    OUTPUT:
        * if the queued cell list is empty, cancel update checking.
        * makes an async request
        * causes the title bar compute spinner to spin
    */
    var cell_id, busy_text, num_queued;

    // Cancel update checks if no cells are doing computations.
    if (queue_id_list.length === 0) {
        cancel_update_check();
        return;
    }

    // Record in a global variable when the last update occurred.
    update_time = time_now();

    // Check on the "lead" cell currently computing to see what's up.
    cell_id = queue_id_list[0];

    async_request(worksheet_command('cell_update'),
                  check_for_cell_update_callback, { 
                      id: cell_id 
                  });

    // Spin the little title spinner in the title bar.
    try {
        title_spinner_i = (title_spinner_i + 1) % title_spinner.length;
        busy_text = title_spinner[title_spinner_i] + original_title;
        num_queued = queue_id_list.length;
        if (num_queued > 1) {
            busy_text = num_queued + ' ' + busy_text;
        }
        document.title = busy_text;
    } catch (e) {}
}


function check_for_cell_update_callback(status, response) {
    /*
    Updates cell data from the server

    INPUT:
        status -- string
        response -- string; encoded JSON object with parsed keys

            id -- string or integer; queried cell's id
            status -- string; 'e' (empty queue), 'd' (done with
                      queried cell), or 'w' (still working)
            output -- string; cell's latest output text
            output_wrapped -- string; word-wrapped output
            output_html -- string; HTML output
            new_input -- string; updated input (e.g., from tab
                         completion)
            interrupted -- string; 'restart', 'false', or 'true',
                           whether/how the cell's computation was 
                           interrupted
            introspect_html -- string; updated introspection text
    */
    var elapsed_time, eval_hook, msg, X;

    // Make sure the update happens again in a few hundred
    // milliseconds, unless a problem occurs below.
    if (status !== "success") {
        // A problem occured -- stop trying to evaluate.
        if (update_error_count > update_error_threshold) {
            cancel_update_check();
            halt_queued_cells();
            elapsed_time = update_error_count * update_error_delta / 1000;
            msg = translations['Error updating cell output after '] + " " + elapsed_time + translations['s (canceling further update checks).'];
            
            /* alert(msg); */
            return;
        }
        cell_output_delta = update_error_delta;
        update_error_count += 1;
        continue_update_check();
        return;
    } else {
        if (update_error_count > 0) {
            update_error_count = 0;
            update_count = 0;
            update_falloff_level = 1;
            cell_output_delta = update_falloff_deltas[1];
        }
    }

    if (response === '') {
        // If the server returns nothing, we just ignore that response
        // and try again later.
        continue_update_check();
        return;
    }

    X = decode_response(response);

    if (X.status === 'e') {
        cancel_update_check();
        halt_queued_cells();
        return;
    }

    // Evaluate and update the cell's output.
    eval_hook = set_output_text(X.id, X.status, X.output, X.output_wrapped,
                                X.output_html, X.introspect_html, false);

    if (X.status === 'd') {
        cell_set_done(X.id);
        queue_id_list.splice($.inArray(X.id, queue_id_list), 1);

        if (X.interrupted === 'restart') {
            restart_sage();
        } else if (X.interrupted === 'false') {
            cell_set_evaluated(X.id);
        } else {
            cancel_update_check();
            halt_queued_cells();
        }

        if (queue_id_list.length === 0) {
            cancel_update_check();
        }

        if (X.new_input !== '') {
            set_input_text(X.id, X.new_input);
        }

        update_count = 0;
        update_falloff_level = 0;
        cell_output_delta = update_falloff_deltas[0];
    } else {
        if (update_count > update_falloff_threshold &&
            update_falloff_level + 1 < update_falloff_deltas.length) {
            update_falloff_level += 1;
            update_count = 0;
            cell_output_delta = update_falloff_deltas[update_falloff_level];
        } else {
            update_count += 1;
        }
    }

    if (eval_hook === 'trigger_interact') {
         interact(X.id, {}, 1);
    } else if (eval_hook === 'restart_interact') {
        evaluate_cell(X.id, 0);
    }

    continue_update_check();
}


function continue_update_check() {
    /*
    If enough time has elapsed, check for more output from the server.
    If not, wait longer and try again later.

    GLOBAL INPUT:
        update_time -- global variable that records when last update
        check occurred.
    */
    var time_elapsed = time_now() - update_time;
    if (time_elapsed < cell_output_delta) {
        update_timeout = setTimeout(function () {
            check_for_cell_update();
        }, cell_output_delta - time_elapsed);
    } else {
        check_for_cell_update();
    }
}


function start_update_check() {
    /*
    Start the updating check system.  This system checks for update
    from the server with an exponential backup strategy.
    */
    if (updating) {
        return;
    }

    // Set several global variables that cells are computing so we
    // have to check for output.
    updating = true;
    update_count = 0;
    update_falloff_level = 0;

    // The starting value for how long we wait between checks for new
    // updates.
    cell_output_delta = update_falloff_deltas[0];

    // Do one initial check without waiting, since some calculations
    // are very fast and doing this feels snappy.
    check_for_cell_update();
}


function cancel_update_check() {
    /*
    Turn off the loop that checks for now output updates in the
    worksheet.

    This just cancels the updating timer and gets rid of the spinning
    "active" indicator in the title bar.
    */
    updating = false;
    clearTimeout(update_timeout);
    document.title = original_title;
    reset_interrupts();
}


function set_output_text(id, status, output_text, output_text_wrapped,
                         output_html, introspect_html, no_interact) {
    /*
    Evaluate and update a cell's output.

    INPUT:
        id -- integer or string; cell id
        status -- string; 'd' (done) or anything else (still working)
        output_text -- string
        output_text_wrapped -- string; word wrapped version of text
        output_html -- string; html formatted output
        introspect_html -- string; when user is introspecting this
        html will go in the introspection dialog box
        no_interact -- boolean; whether to consider this @interact
        output
    OUTPUT:
        a boolean or a string; whether to trigger or restart an
        interact cell
    */
    var cell_interact, cell_output, cell_output_html, cell_output_nowrap, i, j, new_interact_output;

    if (typeof(id) === 'number' && id < 0) {
        // Negative id's come up for special internal usage, and
        // should be ignored.
        return false;
    }

    // Evaluate javascript, but *only* after the entire cell output
    // has been loaded (hence the status === 'd') below.
    if (status === 'd' && !is_interacting_cell(id)) {
        output_text_wrapped = eval_script_tags(output_text_wrapped);
        output_html = eval_script_tags(output_html);
    }

    // Handle an interact update.
    if (!no_interact && is_interacting_cell(id)) {
        // Comment this out to show output only at the end.
        if (status !== 'd') {
            return false;
        }

        i = output_text_wrapped.indexOf(INTERACT_START);
        j = output_text_wrapped.indexOf(INTERACT_END);
        // An error occurred accessing the data for this cell.  Just
        // force reload of the cell, which will certainly define that
        // data.
        if (output_text_wrapped.indexOf(INTERACT_RESTART) !== -1) {
            return 'restart_interact';
        }
        if (i === -1 || j === -1) {
            return false;
        }

        new_interact_output = output_text_wrapped.slice(i + 16, j);
        new_interact_output = eval_script_tags(new_interact_output);

        cell_interact = get_element('cell-interact-' + id);
        cell_interact.innerHTML = new_interact_output;
        MathJax.Hub.Queue(["Typeset",MathJax.Hub,cell_interact]);

        return false;
    }
    // Fill in output text got so far.
    cell_output = get_element('cell_output_' + id);
    if (!cell_output) {
        // This can happen, e.g., if a cell is deleted from the DOM,
        // but the server has some output it still wants to put in the
        // cell.  This happens because once a cell is running there is
        // no stopping it beyond an explicit interrupt (since
        // interrupt may or may not succeed -- this is the real world
        // with hard to kill C code, etc.).
        return false;
    }
    cell_output_nowrap = get_element('cell_output_nowrap_' + id);
    cell_output_html = get_element('cell_output_html_' + id);
    cell_output.innerHTML = output_text_wrapped;
    cell_output_nowrap.innerHTML = output_text;
    cell_output_html.innerHTML = output_html;

    // Call MathJax on the final output.
    if (status === 'd' ) {
        try {
            MathJax.Hub.Queue(["Typeset",MathJax.Hub,cell_output]);
        } catch (e) {
            cell_output.innerHTML = 'Error typesetting mathematics' + cell_output.innerHTML;
            cell_output_nowrap.innerHTML = 'Error typesetting mathematics' +
                cell_output_nowrap.innerHTML;
        }
    }

    // Update introspection.
    if (status === 'd') {
        if (introspect_html !== '') {
            introspect[id].loaded = true;
            update_introspection_text(id, introspect_html);
        } else {
            halt_introspection(id);
        }
    }

    // Trigger a new interact cell?
    if (status === 'd' && introspect_html === '' && is_interacting_cell(id)) {
        // This is the first time that the underlying Python interact
        // function (i.e., interact.recompute) is actually called!
        return 'trigger_interact';
    }

    return false;
}


function set_input_text(id, text) {
    /*
    Fill in input text for the cell with given id.  This is used by
    the tab completion system, so it also sets the cell with given id
    to be in focus and positions the cursor in exactly the right spot.

    INPUT:
        id -- integer or string; cell id
        text -- a string
    */
    var cell_input = get_cell(id), pos;
    cell_input.value = text;

    jump_to_cell(id, 0);
    pos = text.length - introspect[id].after_cursor.length;
    set_cursor_position(cell_input, pos);

    return false;
}


///////////////////////////////////////////////////////////////////
// Dynamic evaluation of javascript related in cell output.
///////////////////////////////////////////////////////////////////
function CellWriter() {
    /*
    When a new cell is loaded, this class is used to let javascript
    write directly to the document. After that, make sure javascript
    writes to a CellWriter object.  This is used in order to get jmol
    to work.
    */
    this.buffer = "";
    this.write = function (s) {
        this.buffer += s;
    };
}


function eval_script_tags(text) {
    /*
    Find all the tags in the given script and eval them, where tags
    are javascript code in <script>...</script> tags.  This allows us
    put javascript in the output of computations and have it
    evaluated.  Moreover, if the javascript writes to the global
    cell_writer object (with cell_write.write(string)), then that
    output is textually substituted in place of the
    <script>...</script>.

    INPUT:
        text -- string
    OUTPUT
        string with all script tags removed
    */

    var i, j, k, left_tag, right_tag, s, script, new_text, script_end, left_match;

    left_tag = new RegExp(/<(\s)*script([^>]*)?>/i);
    right_tag = new RegExp(/<(\s*)\/(\s*)script(\s)*>/i);

    script = '';
    new_text='';
    s = text;
    i = s.search(left_tag);
    while (i !== -1) {
        left_match = s.match(left_tag);
        j = s.search(right_tag);
        k = i + (left_match[0] + '').length;
	script_end=j + (s.match(right_tag)[0] + '').length;
        if (j === -1 || j < k) {
            break;
        }
        // MathJax uses the script tag with a type='math/tex(display|inline)'
        // to encode characters (as a sort of CDATA thing).  We *don't* want
        // to execute these script tags since they need to appear inline.
        if (!left_match[2] || left_match[2].indexOf('math/tex')===-1) {
            code = s.slice(k, j);
            try {
		cell_writer = new CellWriter();
		eval(code);
            } catch (e) {
		alert(e);
            }
            new_text += s.slice(0, i) + cell_writer.buffer;
	} else {
	    new_text += s.slice(0, script_end);
	}
        s = s.slice(script_end);
        i = s.search(left_tag);
    }
    new_text+=s;
    return new_text;
}


function separate_script_tags(text) {
    /*
    Find all the tags in the given script and return a list of two
    strings.  The first string is the html in text, the second is the
    contents of any <script>...</script> tags.

    INPUT:
        text -- string
    OUTPUT
        list of two strings:
            [text w/o script tags (but includes math/tex script tags), content of script tags]


    This is similar to what jQuery does when inserting html.
    See http://stackoverflow.com/questions/610995/jquery-cant-append-script-element
    */
    var i, j, k, left_tag, right_tag, s, script, new_text, script_end, left_match;
    
    left_tag = new RegExp(/<(\s)*script([^>]*)?>/i);
    right_tag = new RegExp(/<(\s*)\/(\s*)script(\s)*>/i);

    script = '';
    new_text='';
    s = text;
    i = s.search(left_tag);
    while (i !== -1) {
        left_match = s.match(left_tag);
        j = s.search(right_tag);
        k = i + (left_match[0] + '').length;
	script_end=j + (s.match(right_tag)[0] + '').length;
        if (j === -1 || j < k) {
            break;
        }
        // MathJax uses the script tag with a type='math/tex(display|inline)'
        // to encode characters (as a sort of CDATA thing).  We *don't* want
        // to extract these script tags since they need to appear inline.
        if (!left_match[2] ||  left_match[2].indexOf('math/tex') === -1) {
            script += s.slice(k, j);
	    new_text += s.slice(0, i);
	} else {
	    new_text += s.slice(0, script_end);
	}
        s = s.slice(script_end);
        i = s.search(left_tag);
    }
    new_text+=s;
    return [new_text, script];
}


///////////////////////////////////////////////////////////////////
// Single Cell Functions
///////////////////////////////////////////////////////////////////
function slide_mode() {
    /*
    Switch into single cell mode.  This involves changing a bunch of
    CSS and some global variables.
    */
    var i, id, len = cell_id_list.length;

    in_slide_mode = true;
    set_class('left_pane', 'hidden');
    set_class('cell_controls', 'hidden');
    set_class('slide_controls', 'slide_control_commands');
    set_class('left_pane_bar', 'hidden');

    for (i = 0; i < len; i += 1) {
        id = cell_id_list[i];
        if (is_compute_cell(id)) {
            set_class('cell_outer_' + id, 'hidden');
        }
    }
    slide_show();
}


function cell_mode() {
    /*
    Switch from single cell mode back to normal worksheet mode.  This
    involves changing CSS and global variables.
    */
    var i, id, len = cell_id_list.length;

    in_slide_mode = false;
    set_class('left_pane', 'pane');
    set_class('cell_controls', 'control_commands');
    set_class('slide_controls', 'hidden');
    set_class('worksheet', 'worksheet');
    set_class('left_pane_bar', 'left_pane_bar');

    for (i = 0; i < len; i += 1) {
        id = cell_id_list[i];
        if (is_compute_cell(id)) {
            set_class('cell_outer_' + id, 'cell_visible');
        }
    }
}


function slide_hide() {
    /*
    Hide the currently displayed slide.

    GLOBAL INPUT:
        current_cell -- integer
    */
    set_class('cell_outer_' + current_cell, 'hidden');
}


function slide_show() {
    /*
    Switch into slide show mode.  This involves changing a lot of CSS
    in the DOM.
    */
    var input, s;

    if (current_cell !== -1) {
        set_class('cell_outer_' + current_cell, 'cell_visible');
    } else {
        if (cell_id_list.length > 0) {
            current_cell = extreme_compute_cell(1);
        }
        set_class('cell_outer_' + current_cell, 'cell_visible');
    }

    if (current_cell !== -1) {
        input = get_cell(current_cell);
        if (!input) {
            s = lstrip(input.value).slice(0, 5);
            cell_focus(current_cell, false);
            if (s === '%hide') {
                slide_hidden = true;
                input.className = 'cell_input_hide';
                input.style.height = '1.5em';
            }
        }
    }
    update_slideshow_progress();
}


function slide_first() {
    /*
    Move to the first input cell in single cell mode.

    GLOBAL INPUT:
        the first cell is the first entry in the cell_id_list.
    */
    jump_to_slide(extreme_compute_cell(1));
}


function slide_last() {
    /*
    Move to the last input cell in single cell mode.

    GLOBAL INPUT:
        the last cell is the last entry in the cell_id_list.
    */
    jump_to_slide(extreme_compute_cell(-1));
}


function slide_next() {
    /*
    Move to the next cell in single cell mode.
    */
    jump_to_slide(id_of_cell_delta(current_cell, 1));
}


function slide_prev() {
    /*
    Move to the previous cell in single cell mode.
    */
    jump_to_slide(id_of_cell_delta(current_cell, -1));
}


function jump_to_slide(id) {
    /*
    Move to the display only the cell with the given id.

    INPUT:
        id -- integer or string; cell id
    OUTPUT:
        sets the global variable current_cell to the id.
    */
    slide_hide();
    current_cell = toint(id);
    slide_show();
}


function update_slideshow_progress() {
    /*
    There is a bar at the top of the screen that shows how far through
    the worksheet we currently are in the list of cells (in single
    cell mode).  This function updates the CSS of that "progress
    meter" to have the right percentage filled in.
    */
    var bar, i, n, text;

    i = $.inArray(current_cell, cell_id_list) + 1;
    n = cell_id_list.length;
    bar = get_element("slideshow_progress_bar");
    if (bar) {
        bar.style.width = "" + 100 * i / n + "%";
    }
    text = get_element("slideshow_progress_text");
    if (text) {
        text.innerHTML = i + " / " + n;
    }
}


///////////////////////////////////////////////////////////////////
// Insert and move cells
///////////////////////////////////////////////////////////////////
function make_new_cell(id, html) {
    /*
    Create a new cell in the DOM with given id and html defining it.
    This does not send a message back to the server.

    INPUT:
        id -- integer or string; cell id
        html -- string
    */
    var in_cell, new_cell, new_html;

    new_html = separate_script_tags(html);

    new_cell = document.createElement("div");
    in_cell = document.createElement("div");

    new_cell.appendChild(in_cell);

    new_cell.id = 'cell_outer_' + id;
    in_cell.id = 'cell_' + id;

    in_cell.innerHTML = new_html[0];
    setTimeout(new_html[1], 50);

    halt_introspection(id);
    return new_cell;
}


function make_new_text_cell(id, html) {
    /*
    Create a new cell in the DOM with given id and html defining it.
    This does not send a message back to the server.

    INPUT:
        id -- integer or string; cell id
        html -- string
    */
    var new_cell, new_html;
    new_html = separate_script_tags(html);
    new_cell = $(new_html[0]);
    setTimeout(new_html[1], 50);
    return new_cell;
}


function do_insert_new_cell_before(id, new_id, new_html) {
    /*
    Insert a new cell with the given new_id and new_html before the
    cell with given id.

    INPUT:
        id -- integer or string; cell id
        new_id -- integer or string; new cell's id
        new_html -- string; new cell's HTML
    GLOBAL INPUT:
        doing_split_eval -- boolean; whether both cells id and new_id
    */
    var i, new_cell = make_new_cell(new_id, new_html);
    $('#cell_outer_' + id).before(new_cell);

    i = $.inArray(id, cell_id_list);
    cell_id_list.splice(i, 0, new_id);

    // Deal with one special case when this function is called, where
    // we evaluate both of the cells that result from a split.  It is
    // annoying to put this code here, but it is much simpler than
    // coding it in any other way, because we don't know the new_id
    // until this point.
    if (doing_split_eval) {
        evaluate_cell(id, false);
        evaluate_cell(new_id, false);
    }
}


function do_insert_new_text_cell_before(id, new_id, new_html) {
    /*
    Insert a new cell with the given new_id and new_html before the
    cell with given id.

   INPUT:
        id -- integer or string; cell id
        new_id -- integer or string; new cell's id
        new_html -- string; new cell's HTMl
     */
    var i, new_cell = make_new_text_cell(new_id, new_html);
    $('#cell_outer_' + id).before(new_cell);

    i = $.inArray(id, cell_id_list);
    cell_id_list.splice(i, 0, new_id);
}


function insert_new_cell_after(id, input) {
    /*
    Send a message back to the server requesting that a new cell with
    the given input be inserted before the cell with given id.

    INPUT:
        id -- integer or string; cell id
        input -- string (default: ''); cell input text
    */
    input = input || '';
    async_request(worksheet_command('new_cell_after'),
                  insert_new_cell_after_callback,
                  { id: id, input: input });
}


function insert_new_cell_after_callback(status, response) {
    /*
    Callback that is called when the server inserts a new cell after a
    given cell.

    INPUT:
        status -- string
        response -- string; 'locked' (user not allowed to insert new
        cells) or encoded JSON object with parsed keys

            id -- string or integer; preceding cell's id
            new_id -- string or integer; new cell's id
            new_html -- string; new cell's HTML

    */
    var X;

    if (status === "failure") {
        alert(translations['Problem inserting new input cell after current input cell.\\n'] + response);
        return;
    }
    if (response === "locked") {
        alert(translations['Worksheet is locked. Cannot insert cells.']);
        return;
    }

    X = decode_response(response);
    do_insert_new_cell_after(X.id, X.new_id, X.new_html);
    jump_to_cell(X.new_id, 0);
}


function insert_new_text_cell_after(id, input) {
    /*
    Insert a new text cell after the cell with given id.  This sends a
    message to the server requesting that a new cell be inserted, then
    via a callback modifies the DOM.

    INPUT:
        id -- integer or string; cell id
        input -- string (default: ''); cell input text
    */
    input = input || '';
    async_request(worksheet_command('new_text_cell_after'),
                  insert_new_text_cell_after_callback,
                  { id: id, input: input });
}


function insert_new_text_cell_after_callback(status, response) {
    /*
    Callback that is called when the server inserts a new cell after a
    given cell.

    INPUT:
        status -- string
        response -- string; 'locked' (user not allowed to insert new
        cells) or encoded JSON object with parsed keys

            id -- string or integer; preceding cell's id
            new_id -- string or integer; new cell's id
            new_html -- string; new cell's HTML

    */
    var X;
    if (status === "failure") {
        alert(translations['Problem inserting new text cell before current input cell.'] );
        return;
    }
    if (response === "locked") {
        alert(translations['Worksheet is locked. Cannot insert cells.']);
        return;
    }

    X = decode_response(response);
    do_insert_new_text_cell_after(X.id, X.new_id, X.new_html);
}


function do_insert_new_cell_after(id, new_id, new_html) {
    /*
    Insert a new cell with the given new_id and new_html after the
    cell with given id.

    INPUT:
        id -- integer or string; cell id
        new_id -- integer or string; new cell's id
        new_html -- string; new cell's HTML
    */
    // Find the cell id of the cell right after the cell with id.
    var i = id_of_cell_delta(id, 1);

    if (i === id) {
        // i is the last cell.
        append_new_cell(new_id, new_html);
    } else {
        do_insert_new_cell_before(i, new_id, new_html);
    }
}


function do_insert_new_text_cell_after(id, new_id, new_html) {
    /*
    Insert a new text cell with the given new_id and new_html after
    the cell with given id.

    INPUT:
        id -- integer or string; cell id
        new_id -- integer or string; new cell's id
        new_html -- string; new cell's HTML
    */
    // Find the cell id of the cell right after the cell with id.
    var i = id_of_cell_delta(id, 1);

    if (i === id) {
        // i is the last cell.
        append_new_text_cell(new_id, new_html);
    } else {
        do_insert_new_text_cell_before(i, new_id, new_html);
    }
}


function insert_new_cell_before(id, input) {
    /*
    Insert a new cell before the cell with given id.  This sends a
    message to the server requesting that a new cell be inserted, then
    via a callback modifies the DOM.

    INPUT:
        id -- integer or string; cell id
        input -- string (default: ''); cell input text
    */
    input = input || '';
    async_request(worksheet_command('new_cell_before'),
                  insert_new_cell_before_callback, {
                      id: id,
                      input: input
                  });
}


function insert_new_cell_before_callback(status, response) {
    /*
    See the documentation for insert_new_cell_after_callback, since
    response is encoded in exactly the same way there.
    */
    var X;
    if (status === "failure") {
        alert(translations['Problem inserting new input cell before current input cell.\\n'] + response);
        return;
    }
    if (response === "locked") {
        alert(translations['Worksheet is locked. Cannot insert cells.']);
        return;
    }

    X = decode_response(response);
    do_insert_new_cell_before(X.id, X.new_id, X.new_html);
    jump_to_cell(X.new_id, 0);

}


function insert_new_text_cell_before(id, input) {
    /*
    Insert a new text cell before the cell with given id.  This sends
    a message to the server requesting that a new cell be inserted,
    then via a callback modifies the DOM.

    INPUT:
        id -- integer or string; cell id
        input -- string (default: ''); cell input text
    */
    input = input || '';
    async_request(worksheet_command('new_text_cell_before'),
                  insert_new_text_cell_before_callback, {
                      id: id,
                      input: input
                  });
}


function insert_new_text_cell_before_callback(status, response) {
    /*
    See the documentation for insert_new_text_cell_after_callback,
    since response is encoded in exactly the same way there.
    */
    var X;
    if (status === "failure") {
        alert(translations['Problem inserting new text cell before current input cell.\\n'] + response);
        return;
    }
    if (response === "locked") {
        alert(translations['Worksheet is locked. Cannot insert cells.']);
        return;
    }

    X = decode_response(response);
    do_insert_new_text_cell_before(X.id, X.new_id, X.new_html);
}


function append_new_cell(id, html) {
    /*
    Append a new cell with given id to the end of the list of cells,
    then position the cursor in that cell.  This modifies the DOM and
    nothing else.

    INPUT:
        id -- integer or string; cell id
        html -- string; cell HTML
    */
    var new_cell, worksheet;
    new_cell = make_new_cell(id, html);

    worksheet = get_element('worksheet_cell_list');
    worksheet.appendChild(new_cell);

    cell_id_list.push(id);

    if (in_slide_mode) {
        set_class('cell_outer_' + id, 'hidden');
        update_slideshow_progress();
    } else {
        jump_to_cell(id, 0);
    }
}


function append_new_text_cell(id, html) {
    /*
    Append a new text cell with given id to the end of the list of
    cells, then position the cursor in that cell.  This modifies the
    DOM and nothing else.

    INPUT:
        id -- integer or string; cell id
        html -- string; cell HTML
    */
    var new_cell = make_new_text_cell(id, html);
    $('#worksheet_cell_list').append(new_cell);
    cell_id_list.push(id);
}


///////////////////////////////////////////////////////////////////
// CONTROL functions
///////////////////////////////////////////////////////////////////
function interrupt() {
    /*
    Send a message to the server that we would like to interrupt all
    running calculations in the worksheet.
    */
    if (!updating) {
        return;
    }
    async_request(worksheet_command('interrupt'), interrupt_callback);
}


function reset_interrupts() {
    /*
    Stops sending periodic interrupt commands, closes any running
    alerts, and resets state variables.
    */
    var is = interrupt_state;

    if (is.alert) {
        is.alert.achtung('close');
    }
    is.alert = null;
    is.count = 0;
}




function evaluate_all() {
    /*
    Iterate through every input cell in the document, in order, and
    evaluate it.  Previously, we just called evaluate on everything
    all at once.  This is undesirable, since packets often arrive
    out-of-order, so the cells get evaluated out-of-order.

    Set the global variable evaluating_all = true.  Then, we kick off
    evaluations by evaluating the first cell.  In
    cell_evaluate_callback, we check to see if evaluating_all is set,
    and proceed from there.  This way, each cell is evaluated
    immediately after the server acknowledges that it has received the
    previous request.
    */
    evaluating_all = true;
    evaluate_cell(extreme_compute_cell(1), false);
}


function hide_all() {
    /*
    Hide every output cell in the worksheet (via CSS) then send a
    message back to the server recording that we hid all cells, so if
    we refresh the browser or visit the page with another browser,
    etc., the cells are still hidden.
    */
    var i, id, len = cell_id_list.length;
    for (i = 0; i < len; i += 1) {
        id = cell_id_list[i];
        if (is_compute_cell(id)) {
            cell_output_set_type(id, 'hidden', false);
        }
    }
    async_request(worksheet_command('hide_all'));
}


function show_all() {
    /*
    Show ever output cell in the worksheet, and send a message to the
    server reporting that we showed every cell.
    */
    var i, id, len = cell_id_list.length;
    for (i = 0; i < len; i += 1) {
        id = cell_id_list[i];
        if (is_compute_cell(id)) {
            cell_output_set_type(id, 'wrap', false);
        }
    }
    async_request(worksheet_command('show_all'));
}


function delete_all_output() {
    /*
    Delete the contents of every output cell in the worksheet (in the
    DOM) then send a message back to the server recording that we
    deleted all cells, so if we refresh the browser or visit the page
    with another browser, etc., the cells are still deleted.

    Things that could go wrong:
         1. Message to server to actually do the delete is not
            received or fails.  Not so bad, since no data is lost; a
            mild inconvenience.
         2. User accidentally clicks on delete all.  There is no
            confirm dialog.  Not so bad, since we save a revision
            right before the delete all, so they can easily go back to
            the previous version.
    */
    var i, id, len = cell_id_list.length;

    // Iterate over each cell in the worksheet.
    for (i = 0; i < len; i += 1) {
        id = cell_id_list[i];
        if (!is_compute_cell(id)) {
            continue;
        }

        // First delete the actual test from the output of each cell.
        get_element('cell_output_' + id).innerHTML = "";
        get_element('cell_output_nowrap_' + id).innerHTML = "";
        get_element('cell_output_html_' + id).innerHTML = "";

        // Then record that the cell hasn't been evaluated and
        // produced that output.
        cell_set_not_evaluated(id);
    }
    // Finally tell the server to do the actual delete.  We first
    // delete from DOM then contact the server for maximum snappiness
    // of the user interface.
    async_request(worksheet_command('delete_all_output'));
    //update jmol applet info
    jmol_delete_all_output();
}


function halt_queued_cells() {
    /*
    Set all cells so they do not look like they are being evaluates or
    queued up for evaluation, and empty the list of active cells from
    the global queue_id_list variable.
    */
    var i;
    for (i = 0; i < queue_id_list.length; i += 1) {
        cell_set_not_evaluated(queue_id_list[i]);
    }

    // We use splice here, so that we can "overload" the list for
    // debugging.  See debug.js.
    queue_id_list.splice(0, queue_id_list.length);

    reset_interrupts();
}


function set_all_cells_to_be_not_evaluated() {
    /*
    Change the CSS so that all cells are displayed as having not been
    evaluated.
    */
    var i, id, len = cell_id_list.length;
    for (i = 0; i < len; i += 1) {
        id = cell_id_list[i];
        if (is_compute_cell(id)) {
            cell_set_not_evaluated(id);
        }
    }
}


function restart_sage() {
    /*
    Restart the running Sage process that supports calculations in
    this worksheet.

    This function immediately changes the DOM so it looks like no
    cells are running and none have been evaluated, then it sends a
    message back to the server requesting that the worksheet Sage
    process actually be stopped.
    */
    halt_queued_cells();
    set_all_cells_to_be_not_evaluated();
    async_request(worksheet_command('restart_sage'));
}


function quit_sage() {
    /*
    Called when the worksheet process is terminated.  All actively
    computing cells are stopped, and a request is sent to the server
    to quit the worksheet process.
    */
    halt_queued_cells();
    set_all_cells_to_be_not_evaluated();
    async_request(worksheet_command('quit_sage'));
}


function login(username, password) {
    /*
    Set the username and password for this user in a cookie.  This is
    called when the user logs in from the login screen to set the
    user's credentials.

    INPUT:
        username -- string
        password -- string
    */
    document.cookie = "username=" + username;
    document.cookie = "password=" + password;
    window.location = "/";
}

///////////////////////////////////////////////////////////////////
// Various POPUP WINDOWS
///////////////////////////////////////////////////////////////////
function history_window() {
    /*
    Popup the history window.
    */
    window.open("/history", "",
                "menubar=1,scrollbars=1,width=800,height=600, toolbar=1,resizable=1");
}


function print_worksheet() {
    /*
    Display a version of this worksheet that is suitable for printing.
    */
    window.open(worksheet_command("print"), "",
                "menubar=1,scrollbars=1,width=800,height=600,toolbar=1,  resizable=1");
}


function help() {
    /*
    Popup the help window.
    */
    window.open("/help", "",
                "menubar=1,location=1,scrollbars=1,width=800,height=650,toolbar=1,  resizable=1");
}


function bugreport() {
    /*
    Popup the bug report window.
    */
    window.open("http://sagemath.org/report-issue", "", "menubar=1,location=1,scrollbars=1,width=800,height=650,toolbar=1,  resizable=1");
}


///////////////////////////////////////////////////////////////////
// Interact
///////////////////////////////////////////////////////////////////
function interact(id, update, recompute) {
    /*
    Sends an interact request back to the server.  This is called by
    individual interact controls.

    INPUT:
        id -- integer or string; cell id
        update -- dictionary; data to update
            variable -- string; name of variable to update
            adapt_number -- integer; number of control to update
            value -- string; updated value, base-64 encoded
        recompute -- integer; whether to recompute the interact
    */
    id = toint(id);

    cell_has_changed = false;
    current_cell = id;

    update = update || {};

    async_request(worksheet_command('eval'), evaluate_cell_callback, {
        id: id,
        interact: 1,
        variable: update.variable || '',
        adapt_number: update.adapt_number || -1,
        value: update.value || '',
        recompute: recompute,
        newcell: 0
    });
}


///////////////////////////////////////////////////////////////////
// Base 64 encoding and decoding (mainly used for @interact).
///////////////////////////////////////////////////////////////////

//////////////////////////////////////////////////////////////////
// The following header applies to the encode64 and decode64 functions
// This code was written by Tyler Akins and has been placed in the
// public domain.  It would be nice if you left this header intact.
// Base64 code from Tyler Akins -- http://rumkin.com
//////////////////////////////////////////////////////////////////
var keyStr = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=";


function encode64(input) {
    /*
    Base 64 encode the given input.

    INPUT:
        input -- string
    OUTPUT:
        string
    */
    // I had to add this, since otherwise when input is numeric there
    // are errors below.
    var chr1, chr2, chr3, enc1, enc2, enc3, enc4, i = 0, output = "";

    try {
        input = input.toString();
    } catch (e) {
        return input;
    }

    while (i < input.length) {
        chr1 = input.charCodeAt(i++);
        chr2 = input.charCodeAt(i++);
        chr3 = input.charCodeAt(i++);

        enc1 = chr1 >> 2;
        enc2 = ((chr1 & 3) << 4) | (chr2 >> 4);
        enc3 = ((chr2 & 15) << 2) | (chr3 >> 6);
        enc4 = chr3 & 63;

        if (isNaN(chr2)) {
            enc3 = 64;
            enc4 = 64;
        } else if (isNaN(chr3)) {
            enc4 = 64;
        }

        output = output + keyStr.charAt(enc1) + keyStr.charAt(enc2) +
            keyStr.charAt(enc3) + keyStr.charAt(enc4);
    }

    return output;
}


function decode64(input) {
    /*
    Base 64 decode the given input.

    INPUT:
        input -- string
    OUTPUT:
        string
    */
    var chr1, chr2, chr3, enc1, enc2, enc3, enc4, i = 0, output = "";

    // remove all characters that are not A-Z, a-z, 0-9, +, slash, or =
    input = input.replace(/[^A-Za-z0-9\+\/\=]/g, "");

    while (i < input.length) {
        enc1 = keyStr.indexOf(input.charAt(i++));
        enc2 = keyStr.indexOf(input.charAt(i++));
        enc3 = keyStr.indexOf(input.charAt(i++));
        enc4 = keyStr.indexOf(input.charAt(i++));

        chr1 = (enc1 << 2) | (enc2 >> 4);
        chr2 = ((enc2 & 15) << 4) | (enc3 >> 2);
        chr3 = ((enc3 & 3) << 6) | enc4;

        output = output + String.fromCharCode(chr1);

        if (enc3 !== 64) {
            output = output + String.fromCharCode(chr2);
        }
        if (enc4 !== 64) {
            output = output + String.fromCharCode(chr3);
        }
    }

    return output;
}

///////////////////////////////////////////////////////////////////
// Trash
///////////////////////////////////////////////////////////////////

function empty_trash() {
    /*

      This asks for confirmation from the user before submitting the
      empty trash form, which sends a POST request. GET requests are not
      allowed by the server.

    */
    if(confirm(translations["Emptying the trash will permanently delete all items in the trash. Continue?"])) {
        $('#empty-trash-form').submit();
    }
}
