/*global $, alert, async_request, clearTimeout, confirm, document, escape, jsMath, location, navigator, open, prompt, setTimeout, window, worksheet_filenames */
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

// This toggles a logger.  Please see the end of this file for
// details.
var sage_debug_log = true;

// Cell lists and cache.
var cell_id_list;
var active_cell_list = [];
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
// Encoding separator must match server's separator.
var SEP = '___S_A_G_E___';

// Browser & OS identification.
var browser_op, browser_saf, browser_konq, browser_moz, browser_ie, browser_iphone;
var os_mac, os_lin, os_win;

// Functions assigned during keyboard setup.
var input_keypress;
var input_keydown;
var debug_keypress;
// Bug workaround.
var skip_keyup = false;
var in_debug_input = false;

// Focus / blur.
var current_cell = -1;
var cell_has_changed = false;

// Resizing too often significantly affects performance.
var keypress_resize_delay = 250;
var last_keypress_resize = 0;
var will_resize_soon = false;

// Are we're splitting a cell and evaluating it?
var doing_split_eval = false;
// Whether the the next call to jump_to_cell is ignored.  Used to
// avoid changing focus.
var ignore_next_jump = false;
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

var jsmath_font_msg = '<a href="{{ SAGE_URL }}/jsmath">Click to download and install tex fonts.</a><br>';
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
//
// Cross-Browser Stuff
//
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


function initialize_the_notebook() {
    /*
    Do the following:
        1. Determine the browser OS, type e.g., opera, safari, etc.;
           we set global variables for each type.
        2. Figure out which keyboard the user has.
        3. Initialize jsmath.
    */
    var n, nav, nap, nua;

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
    } catch (e2) {
        alert(e2);
    }

    // Get the keyboard codes for our browser/os combination.
    get_keyboard();

    // Attempt to render any jsmath in this page.
    jsmath_init();

    // Parse the cell ID list.
    cell_id_list = $.map(cell_id_list, function (id) {
        // Reset each cell's introspection variables.
        if (is_compute_cell(id)) {
            halt_introspection(id);
        }
        return toint(id);
    });

    // Resize and paste events.
    window.onresize = resize_all_cells;
    $('textarea').live('paste', function () {
        var id = $(this).attr('id').slice(11);
        setTimeout(function () {
            send_cell_input(id);
            cell_input_resize(id);
        }, keypress_resize_delay);
    });
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
    debug_keypress = debug_input_key_event;

    if (browser_op) {
        b = "o";
    } else if (browser_ie) {
        b = "i";
        input_keypress = true_function;
        input_keydown = cell_input_key_event;
        debug_keypress = true_function;
    } else if (browser_saf) {
        b = "s";
        input_keypress = true_function;
        input_keydown = cell_input_key_event;
        debug_keypress = true_function;
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
        alert("Your browser / OS combination is not supported.  \nPlease use Firefox or Opera under Linux, Windows, or Mac OS X, or Safari.");
    }

    $.getScript('/javascript/sage/keyboard/' + b + o);
}


function jsmath_init() {
    /*
    Process all the jsmath in this page.
    */
    try {
        jsMath.Process();
    } catch (e) {}
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
//
// Misc page functions -- for making the page work nicely
//
///////////////////////////////////////////////////////////////////
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

    overlay_close = options.overlay_close;
    if (!options.overlay_close) {
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
    };

    modal_options = $.extend({
        autoOpen: true,
        bgiframe: true,
        modal: true,
        width: '20em',
        close: close_dialog
    },
    modal_options);

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


function refresh_cell_list_callback(status, response_text) {
    /*
    In conjunction with refresh_cell_list, this function does the
    actual update of the HTML of the list of cells.  Here
    response_text is a pair consisting of the updated state_number and
    the new HTML for the worksheet_cell_list div DOM element.
    */
    var X, z, s;
    if (status === 'success') {
        X = response_text.split(SEP);
        state_number = parseInt(X[0], 10);
        /* Now we replace the HTML for every cell *except* the active
           cell by the contents of X[1]. */
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
    Resize the cell once in a while and auto-indent.  Not too often.

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
//
// Completions interface stuff
//
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
        if (contains_jsmath(text)) {
            try {
                jsMath.ProcessBeforeShowing(introspect_div.get(0));
            } catch (e) {
                introspect_div.html(jsmath_font_msg + introspect_div.html());
            }
        }

        introspect_div.find('.docstring').prepend('<div class="click-message" style="cursor: pointer">Click here to pop out</div><div class="unprinted-note">unprinted</div>');

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
//
// Paren Matching
//
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
//
// WORKSHEET functions -- for switching between and managing worksheets
//
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
        SEP -- separator string used when encoding tuples of data to
        send back to the server.
    OUTPUT:
        string of worksheet filenames that are checked, separated by
        SEP
    */
    var i, id, X, filenames;
    filenames = "";

    // Concatenate the list of all worksheet filenames that are
    // checked together separated by the separator string.
    for (i = 0; i < worksheet_filenames.length; i += 1) {
        id = worksheet_filenames[i].replace(/[^\-A-Za-z_0-9]/g, '-');
        X = get_element(id);
        if (X.checked) {
            filenames = filenames + worksheet_filenames[i] + SEP;
            X.checked = 0;
        }
    }
    return filenames;
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
        SEP -- separator string used when encoding tuples of data to
        send back to the server.
    OUTPUT:
        calls the server and requests an action be performed on all
        the listed worksheets
    */
    // Send the list of worksheet names and requested action back to
    // the server.
    async_request(action, worksheet_list_button_callback, {
        filenames: checked_worksheet_filenames(),
        sep: SEP
    });
}


function worksheet_list_button_callback(status, response_text) {
    /*
    Handle result of performing some action on a list of worksheets.

    INPUT:
        status, response_text -- standard AJAX return values
    OUTPUT:
        display an alert if something goes wrong; refresh this browser
        window no matter what.
    */
    if (status === 'success') {
        if (response_text !== '') {
            alert(response_text);
        }
    } else {
        alert("Error applying function to worksheet(s)." + response_text);
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
    window.location.replace("/download_worksheets?filenames=" +
                            checked_worksheet_filenames() + "&sep=" + SEP);
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


function rate_worksheet(rating) {
    /*
    Save the comment and rating that the uses chooses for a public worksheet.

    INPUT:
        rating -- integer
    */
    var comment = get_element("rating_comment").value;
    window.location.replace(worksheet_command("rate?rating=" + rating +
                                              "&comment=" + escape0(comment)));
}


function download_worksheet() {
    /*
    Download the current worksheet to the file with name select by the
    user.  The title of the worksheet is also changed to match the
    filename.

    INPUT:
        base_filename
    */
    var title = prompt("Title of saved worksheet", worksheet_name), winref;
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


function edit_worksheet() {
    /*
    Edit the current worksheet as a plain text file.
    */
    window.location.replace(worksheet_command(""));
}


function save_worksheet() {
    /*
    Save a snapshot of the current worksheet.
    */
    async_request(worksheet_command('save_snapshot'), save_worksheet_callback);
}


function save_worksheet_callback(status, response_text) {
    /*
    Verify that saving the current worksheet worked.
    */
    if (status !== 'success') {
        alert("Failed to save worksheet.");
        return;
    }
}


function close_callback(status, response_text) {
    /*
    Called when we successfully close the current worksheet and want
    to display the user home screen (i.e., worksheet list).
    */
    if (status !== 'success') {
        alert(response_text);
        return;
    }
    window.location.replace('/');
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
        title: 'Rename worksheet',
        message: 'Please enter a name for this worksheet.',
        'default': worksheet_name,
        submit: 'Rename'
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


function delete_worksheet_callback(status, response_text) {
    /*
    Replace the current page by a page that shows the worksheet in the
    trash, or if the delete worksheet function failed display an
    error.
    */
    if (status === "success") {
        window.location.replace("/?typ=trash");
    } else {
        alert("Possible failure deleting worksheet.");
    }
}


///////////////////////////////////////////////////////////////////
//
// WORKSHEET list functions -- i.e., functions on a specific
// worksheet in the list of worksheets display.
//
///////////////////////////////////////////////////////////////////
function go_option(form) {
    /*
    This is called when the user selects a menu item.

    INPUT:
      form -- DOM element; the drop-down form element
    */
    var action = form.options[form.selectedIndex].value;
    action = action.slice(0, action.indexOf('('));

    // This is safer than using eval.
    if (action === 'delete_worksheet') {
        delete_worksheet(worksheet_filename);
    } else if (action !== '') {
        window[action]();
    }
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
        title: 'Rename worksheet',
        message: 'Please enter a name for this worksheet.',
        'default': curname,
        submit: 'Rename'
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
//
// Server pinging support, so server knows page is being viewed.
//
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


function server_ping_while_alive_callback(status, response_text) {
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
        if (state_number >= 0 && parseInt(response_text, 10) > state_number) {
            // Force a refresh of just the cells in the body.
            refresh_cell_list();
        }
    }
}


///////////////////////////////////////////////////////////////////
//
// CELL functions -- for the individual cells
//
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
}


function evaluate_text_cell_callback(status, response_text) {
    /*
    Display the new content of a text cell, parsing for math if
    needed.

    INPUT:
        status -- string
        response_text -- string that is of the form [id][cell_html]
             id -- string (integer) of the current text cell
             cell_html -- the html to put in the cell
    */
    var id, new_html, text, text_cell, X;
    if (status === "failure") {
        // Failure evaluating a cell.
        return;
    }
    X = response_text.split(SEP);
    if (X[0] === '-1') {
        // Something went wrong -- i.e., the requested cell doesn't
        // exist.
        alert("You requested to evaluate a cell that, for some reason, the server is unaware of.");
        return;
    }
    id = toint(X[0]);
    text = X[1];
    text_cell = get_element('cell_outer_' + id);
    new_html = separate_script_tags(text);
    $(text_cell).replaceWith(new_html[0]);
    // Need to get the new text cell.
    text_cell = get_element('cell_outer_' + id);
    setTimeout(new_html[1], 50);

    if (contains_jsmath(text)) {
        try {
            jsMath.ProcessBeforeShowing(text_cell);
        } catch (e) {
            text_cell.innerHTML = jsmath_font_msg + text_cell.innerHTML;
        }
    }
}


function debug_focus() {
    /*
    Called when the Javascript debugging window gets focus.  This
    window is displayed when the notebook server is run with the
    show_debug option.
    */
    var w;
    in_debug_input = true;
    w = get_element('debug_window');
    if (w) {
        w.className = 'debug_window_active';
    }
}


function debug_blur() {
    /*
    Called when the Javascript debugging window looses focus.
    */
    var w;
    in_debug_input = false;
    w = get_element('debug_window');
    if (w) {
        w.className = 'debug_window_inactive';
    }
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

    if (cell) {
        // Focus on the cell with the given id and resize it.
        cell_input_resize(id);
        cell.focus();

        // Possibly also move the cursor to the top left in this cell.
        if (!leave_cursor) {
            move_cursor_to_top_of_cell(cell);
        }
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


function move_cursor_to_top_of_cell(cell) {
    /* Move the cursor to the first position in the given input cell.

    INPUT:
        cell -- an input cell as a DOM element
    */
    set_cursor_position(cell, 0);
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
    if ($.inArray(id, active_cell_list) !== -1) {
        // Deleting a running cell causes evaluation to be
        // interrupted.  In most cases this avoids potentially tons of
        // confusion.
        async_request(worksheet_command('interrupt'));
    }
    async_request(worksheet_command('delete_cell'), cell_delete_callback, {
        id: id
    });
}


function cell_delete_callback(status, response_text) {
    /*
    When a cell is deleted this callback is called after the server
    hopefully does the deletion.  This function then removes the cell
    from the DOM and cell_id_list.

    INPUT:
        status -- string
        response_text -- string with the format [command]SEP[id]
               command -- empty or 'ignore'
               id -- id of cell being deleted.
    */
    var cell, id, X, worksheet;

    if (status === "failure") {
        return;
    }
    X = response_text.split(SEP);
    if (X[0] === 'ignore') {
        return;
        /* do not delete, for some reason */
    }
    id = toint(X[1]);
    cell = get_element('cell_outer_' + id);
    worksheet = get_element('worksheet_cell_list');
    worksheet.removeChild(cell);
    cell_id_list.splice($.inArray(id, cell_id_list), 1);

    delete introspect[id];
    delete cell_element_cache[id];

    // If we are in slide mode, we call slide_mode() again to
    // recalculate the slides.
    if (in_slide_mode) {
        current_cell = -1;
        slide_mode();
    }
}


function cell_delete_output(id) {
    /*
    Ask the server to delete the output of a cell.

    INPUT:
        id -- integer or string; cell id
    */
    id = toint(id);

    if ($.inArray(id, active_cell_list) !== -1) {
        // Deleting a running cell causes evaluation to be interrupted.
        // In most cases this avoids potentially tons of confusion.
        async_request(worksheet_command('interrupt'));
    }
    async_request(worksheet_command('delete_cell_output'),
                  cell_delete_output_callback, {
                      id: id
                  });
}


function cell_delete_output_callback(status, response_text) {
    /*
    Callback for after the server deletes a cell's output.  This
    function removes the cell's output from the DOM.

    INPUT:
        status -- string ('success' or 'failure')
        response_text -- [command]SEP[id]
               command -- string ('delete_output')
               id -- id of cell whose output is deleted.
    */
    var id;
    if (status !== 'success') {
        // Do not delete output, for some reason.
        return;
    }
    id = toint(response_text.split(SEP)[1]);

    // Delete the output.
    get_element('cell_output_' + id).innerHTML = "";
    get_element('cell_output_nowrap_' + id).innerHTML = "";
    get_element('cell_output_html_' + id).innerHTML = "";

    // Set the cell to not evaluated.
    cell_set_not_evaluated(id);
}


function debug_input_key_event(e) {
    /*
    Handle an input key even when we're in debug mode.

    INPUT:
        e -- key event
    */
    var after, debug_input, i, out;
    e = new key_event(e);
    debug_input = get_element('debug_input');

    if (key_down_arrow(e)) {
        after = text_cursor_split(debug_input)[1];
        i = after.indexOf('\n');
        if (i === -1 || after === '') {
            jump_to_cell(extreme_compute_cell(1), 0);
            return false;
        } else {
            return true;
        }
    }
    if (key_send_input(e)) {
        out = "";
        try {
            out = eval(debug_input.value);
        } catch (err) {
            out = "Error: " + err.description;
        } finally {
            debug_append(out);
            return false;
        }
    }
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
        if (i === -1 || after === '') {
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
    } else if (key_unindent(e) && !selection_is_empty) {
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
        /* Better not to move. */
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


function debug_clear() {
    /*
    Clear the debug window.
    */
    var output = get_element("debug_output");
    if (!output) {
        return;
    }
    output.innerHTML = "";
}


function debug_append(txt) {
    /*
    Append output to the debug window.

    INPUT:
        txt -- string
    */
    var output = get_element("debug_output");
    if (!output) {
        return;
    }
    output.innerHTML = txt + "\n" + output.innerHTML;
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
    var switch_id;
    if (ignore_next_jump) {
        ignore_next_jump = false;
        return;
    }

    if (delta && delta !== 0) {
        switch_id = id_of_cell_delta(id, delta);
    }

    if (switch_id === id) {
        return;
    }

    if (in_slide_mode) {
        jump_to_slide(switch_id);
    } else {
        cell_focus(switch_id, bottom);
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

    TODO: Use the built-in encodeURIComponent function.
    */
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
    Unindent all the highlighted text in the given input cell by 4
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
        // Square brackets pull the captured pattern.
        lines[i] = unindent_pat.exec(lines[i])[1];
    }

    b = lines.join("\n");

    cell.value = a + b + c;
    set_selection_range(cell, a.length, a.length + b.length);
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
    if (cmd === 'eval' || cmd === 'new_cell_before') {
        state_number = parseInt(state_number, 10) + 1;
    }
    return ('/home/' + worksheet_filename + '/' + cmd);
}


function evaluate_cell(id, newcell) {
    /*
    Evaluate the given cell, and if newcell is true (the default),
    insert a new cell after the current one.

    INPUT:
        id -- integer or string; cell id
        newcell -- whether to insert new cell after the current one
    GLOBAL INPUT:
        worksheet_locked -- if true, pop up an alert and return
        immediately
    OUTPUT:
        a message is sent to the server and the "check for updates"
        loop is started if it isn't already going; typically this will
        result in output being generated that we get later
    */
    var cell_input;

    if (worksheet_locked) {
        alert("This worksheet is read only.  Please make a copy or contact the owner to change it.");
        return;
    }

    // Append that cell id is currently having some sort of
    // computation possibly occurring.  Note that active_cell_list is
    // a global variable.
    id = toint(id);
    active_cell_list.push(id);

    // Stop from sending the input again to the server when we leave
    // focus and the send_cell_input function is called.
    cell_has_changed = false;

    // Clear the output text and set the CSS to indicate that this is
    // a running cell.
    cell_set_running(id);

    // Finally make the request back to the server to do the actual calculation.
    cell_input = get_cell(id);
    if (newcell) {
        newcell = 1;
    } else {
        newcell = 0;
    }
    async_request(worksheet_command('eval'), evaluate_cell_callback, {
        newcell: newcell,
        id: id,
        input: cell_input.value
    });
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

    intr.loaded = false;
    update_introspection_text(id, 'loading...');
    active_cell_list.push(id);
    cell_set_running(id);

    async_request(worksheet_command('introspect'), evaluate_cell_callback, {
        id: id,
        before_cursor: before,
        after_cursor: after
    });
}


function evaluate_cell_callback(status, response_text) {
    /*
    Update the focus and possibly add a new cell.  If evaluate all has
    been clicked, start evaluating the next cell (and don't add a new
    cell).

    INPUT:
        response_text -- string in the format
             [id][command][new_html][new_cell_id]

             id -- current cell id
             command -- 'append_new_cell' or 'insert_cell' or
             'no_new_cell' or 'introspect'
             new_html -- optional new cell contents
             new_cell_id -- optional (if command is 'insert_cell') id
             of new cell to create
    */
    var command, id, next_id, new_cell_id, new_html, X;
    if (status === "failure") {
        // Failure evaluating a cell.
        return;
    }
    X = response_text.split(SEP);
    id = toint(X[0]);
    command = X[1];
    new_html = X[2];
    new_cell_id = toint(X[3]);

    if (id === -1) {
        // Something went wrong -- i.e., the requested cell doesn't
        // exist.
        alert("You requested to evaluate a cell that, for some reason, the server is unaware of.");
        return;
    }

    if (evaluating_all) {
        if (is_compute_cell(id)) {
            evaluate_cell(id, false);
        } else {
            next_id = id_of_cell_delta(id, 1);
            if (is_compute_cell(next_id)) {
                evaluate_cell(next_id, false);
            } else {
                evaluating_all = false;
            }
        }
    } else if (command === 'append_new_cell') {
        // Add a new cell to the very end.
        append_new_cell(id, new_html);
    } else if (command === 'insert_cell') {
        // Insert a new cell after the one with id new_cell_id.
        do_insert_new_cell_after(new_cell_id, id, new_html);
        jump_to_cell(id, 0);
    } else if (command !== 'introspect' && !in_slide_mode &&
               !doing_split_eval) {
        // Move to the next cell after the one that we just evaluated,
        // unless it's an interact
        if (!is_interacting_cell(current_cell)) {
            jump_to_cell(current_cell, 1);
        }
    }
    start_update_check();
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

    /* OK, now set the sell output type. */
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


function cell_set_running(id) {
    /*
    Start the cell with given id running -- this is purely a style and
    content; the server is not contacted by this function.

    INPUT:
        id -- integer or string; cell id
    */
    var cell_div, cell_number;
    id = toint(id);

    // Blank the output text. The true means not @interact.
    set_output_text(id, '', '', '', '', '', true);

    // If the output type is hidden, toggle it to be visible.
    // Otherwise we leave it alone.
    if (get_element('cell_div_output_' + id).className === 'cell_div_output_hidden') {
        cycle_cell_output_type(id);
    }

    // Set the CSS.
    cell_div = get_element('cell_div_output_' + id);
    cell_div.className = 'cell_output_running';
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
        * if the active cell list is empty, cancel update checking.
        * makes an async request
        * causes the title bar compute spinner to spin
    */
    var cell_id;

    // Cancel update checks if no cells are doing computations.
    if (active_cell_list.length === 0) {
        cancel_update_check();
        return;
    }

    // Record in a global variable when the last update occurred.
    update_time = time_now();

    // Check on the cell currently computing to see what's up.
    cell_id = active_cell_list[0];

    async_request(worksheet_command('cell_update'),
                  check_for_cell_update_callback, { id: cell_id });

    // Spin the little title spinner in the title bar.
    try {
        title_spinner_i = (title_spinner_i + 1) % title_spinner.length;
        document.title = title_spinner[title_spinner_i] + original_title;
    } catch (e) {}
}


function check_for_cell_update_callback(status, response_text) {
    /*
    Callback after the server responds for our request for updates.

    INPUT:
        status -- string
        response_text -- string in the format (no []'s):

            [status (1-letter)][id][encoded_output]

             status --    'e' -- empty; no more cells in the queue
                          'd' -- done; actively computing cell just finished
                          'w' -- still working
             id -- cell id
             encoded_output -- the output:

                 output_text -- the output text so far
                 output_text_wrapped -- word wrapped version of output
                 text
                 output_html -- html output
                 new_cell_input -- if the input to the cell should be
                 changed (e.g., when doing a tab completion), this
                 gives the new input
                 interrupted -- 'restart' or 'false'; whether the
                 computation of this cell was interrupted and if so
                 why.
                 introspect_html -- new introspection html to be
                 placed in the introspection window
    */
    var D, elapsed_time, i, id, interact_hook, interrupted, introspect_html, msg, new_cell_input, output_html, output_text, output_text_wrapped, stat;

    // Make sure the update happens again in a few hundred
    // milliseconds, unless a problem occurs below.
    if (status !== "success") {
        // A problem occured -- stop trying to evaluate.
        if (update_error_count > update_error_threshold) {
            cancel_update_check();
            halt_active_cells();
            elapsed_time = update_error_count * update_error_delta / 1000;
            msg = "Error updating cell output after " + elapsed_time + "s";
            msg += "(canceling further update checks).";
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

    if (response_text === 'empty') {
        // If the server returns nothing, we just ignore that response
        // and try again later.
        continue_update_check();
        return;
    }

    i = response_text.indexOf(' ');
    id = toint(response_text.substring(1, i));
    stat = response_text.substring(0, 1);

    if (stat === 'e') {
        cancel_update_check();
        halt_active_cells();
        return;
    }

    D = response_text.slice(i + 1).split(SEP);
    output_text = D[0] + ' ';
    output_text_wrapped = D[1] + ' ';
    output_html = D[2];
    new_cell_input = D[3];
    interrupted = D[4];
    introspect_html = D[5];

    // Evaluate and update the cell's output.
    interact_hook = set_output_text(id, stat, output_text, output_text_wrapped,
                                    output_html, introspect_html, false);

    if (stat === 'd') {
        cell_set_done(id);
        active_cell_list.splice($.inArray(id, active_cell_list), 1);

        if (interrupted === 'restart') {
            restart_sage();
        } else if (interrupted === 'false') {
            cell_set_evaluated(id);
        } else {
            cancel_update_check();
            halt_active_cells();
        }

        if (active_cell_list.length === 0) {
            cancel_update_check();
        }

        if (new_cell_input !== '') {
            set_input_text(id, new_cell_input);
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

    if (interact_hook === 'trigger_interact') {
        // We treat the id here as a string.  The interact module's
        // recompute function will attempt cast it to an integer.
        interact(id, '_interact_.recompute("' + id + '")');
    } else if (interact_hook === 'restart_interact') {
        evaluate_cell(id, 0);
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
}


function contains_jsmath(text) {
    /*
    Returns true if text contains some jsmath text.  This function
    sucks, since it really just looks for class="math" and is easy to
    throw off.  Fix this!

    INPUT:
        text -- a string
    */
    // TODO: Use a RegExp.
    text = text.toLowerCase();
    return (text.indexOf('class="math"') !== -1 ||
            text.indexOf("class='math'") !== -1);
}


function set_output_text(id, stat, output_text, output_text_wrapped,
                         output_html, introspect_html, no_interact) {
    /*
    Evaluate and update a cell's output.

    INPUT:
        id -- integer or string; cell id
        stat -- string; 'd' (done) or anything else (still working)
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
    // has been loaded (hence the stat === 'd') below.
    if (stat === 'd' && !is_interacting_cell(id)) {
        output_text_wrapped = eval_script_tags(output_text_wrapped);
        output_html = eval_script_tags(output_html);
    }

    // Handle an interact update.
    if (!no_interact && is_interacting_cell(id)) {
        // Uncomment to change so that only show output at the end.
        if (stat !== 'd') {
            return false;
        }

        i = output_text_wrapped.indexOf('<?__SAGE__START>');
        j = output_text_wrapped.indexOf('<?__SAGE__END>');
        if (i === -1 || j === -1) {
            return false;
        }

        new_interact_output = output_text_wrapped.slice(i + 16, j);
        new_interact_output = eval_script_tags(new_interact_output);

        // An error occurred accessing the data for this cell.  Just
        // force reload of the cell, which will certainly define that
        // data.
        if (new_interact_output.indexOf('__SAGE_INTERACT_RESTART__') !== -1) {
            return 'restart_interact';
        } else {
            cell_interact = get_element('cell-interact-' + id);
            cell_interact.innerHTML = new_interact_output;
            if (contains_jsmath(new_interact_output)) {
                jsMath.ProcessBeforeShowing(cell_interact);
            }
        }

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

    // Call jsMath on the final output.
    if (stat === 'd' && contains_jsmath(output_text)) {
        try {
            jsMath.ProcessBeforeShowing(cell_output);
            jsMath.ProcessBeforeShowing(cell_output_nowrap);
        } catch (e) {
            cell_output.innerHTML = jsmath_font_msg + cell_output.innerHTML;
            cell_output_nowrap.innerHTML = jsmath_font_msg +
                cell_output_nowrap.innerHTML;
        }
    }

    // Update introspection.
    if (stat === 'd') {
        if (introspect_html !== '') {
            introspect[id].loaded = true;
            update_introspection_text(id, introspect_html);
        } else {
            halt_introspection(id);
        }
    }

    // Trigger a new interact cell?
    if (stat === 'd' && introspect_html === '' && is_interacting_cell(id)) {
        // This is the first time that the underlying Python interact
        // function (i.e., interact.recompute) is actually called!
        if (contains_jsmath(output_text_wrapped)) {
            try {
                jsMath.ProcessBeforeShowing(cell_output);
            } catch (e2) {
                // Do nothing.
            }
        }
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
    var code, i, j, k, left_tag, right_tag, s, script;

    left_tag = new RegExp(/<(\s)*script.*?>/i);
    right_tag = new RegExp(/<(\s*)\/(\s*)script(\s)*>/i);

    script = '';
    s = text;
    i = s.search(left_tag);
    while (i !== -1) {
        j = s.search(right_tag);
        k = i + (s.match(left_tag)[0] + '').length;
        if (j === -1 || j < k) {
            break;
        }
        code = s.slice(k, j);
        try {
            cell_writer = new CellWriter();
            eval(code);
        } catch (e) {
            alert(e);
        }
        s = s.slice(0, i) + cell_writer.buffer +
            s.slice(j + (s.match(right_tag)[0] + '').length);
        i = s.search(left_tag);
    }
    return s;
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
            [text w/o script tags, content of script tags]
    */
    var i, j, k, left_tag, right_tag, s, script;

    left_tag = new RegExp(/<(\s)*script.*?>/i);
    right_tag = new RegExp(/<(\s*)\/(\s*)script(\s)*>/i);

    script = '';
    s = text;
    i = s.search(left_tag);
    while (i !== -1) {
        j = s.search(right_tag);
        k = i + (s.match(left_tag)[0] + '').length;
        if (j === -1 || j < k) {
            break;
        }
        script += s.slice(k, j);
        s = s.slice(0, i) + s.slice(j + (s.match(right_tag)[0] + '').length);
        i = s.search(left_tag);
    }
    return [s, script];
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


function insert_new_cell_after_callback(status, response_text) {
    /*
    Callback that is called when the server inserts a new cell after a
    given cell.

    INPUT:
        status -- string
        response_text -- string; 'locked' (user is not allowed to
        insert new cells into this worksheet) OR with the format

            [new_id]SEP[new_html]SEP[id]

            new_id -- new cell's id
            new_html -- new cell's HTML
            id -- preceding cell's id
    */
    var id, new_html, new_id, X;

    if (status === "failure") {
        alert("Problem inserting new input cell after current input cell.\n" + response_text);
        return;
    }
    if (response_text === "locked") {
        alert("Worksheet is locked.  Cannot insert cells.");
        return;
    }

    // Extract the input variables that are encoded in the
    // response_text.
    X = response_text.split(SEP);
    new_id = toint(X[0]);
    new_html = X[1];
    id = toint(X[2]);

    // Insert a new cell _after_ a cell.
    do_insert_new_cell_after(id, new_id, new_html);
    jump_to_cell(new_id, 0);
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


function insert_new_text_cell_after_callback(status, response_text) {
    /*
    Callback that is called when the server inserts a new cell after a
    given cell.

    INPUT:
        status -- string
        response_text -- string; 'locked' (user is not allowed to
        insert new cells into this worksheet) OR in the format

            [new_id]SEP[new_html]SEP[id]

            new_id -- new cell's id
            new_html -- new cell's HTML
            id -- preceding cell's id
    */
    var id, new_html, new_id, X;
    if (status === "failure") {
        alert("Problem inserting new text cell before current input cell.");
        return;
    }
    if (response_text === "locked") {
        alert("Worksheet is locked.  Cannot insert cells.");
        return;
    }

    // Insert a new cell _before_ a cell.
    X = response_text.split(SEP);
    new_id = toint(X[0]);
    new_html = X[1];
    id = toint(X[2]);
    do_insert_new_text_cell_after(id, new_id, new_html);
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


function insert_new_cell_before_callback(status, response_text) {
    /*
    See the documentation for insert_new_cell_after_callback, since
    response_text is encoded in exactly the same way there.
    */
    var id, new_html, new_id, X;
    if (status === "failure") {
        alert("Problem inserting new input cell before current input cell.");
        return;
    }
    if (response_text === "locked") {
        alert("Worksheet is locked.  Cannot insert cells.");
        return;
    }

    // Insert a new cell _before_ a cell.
    X = response_text.split(SEP);
    new_id = toint(X[0]);
    new_html = X[1];
    id = toint(X[2]);
    do_insert_new_cell_before(id, new_id, new_html);
    jump_to_cell(new_id, 0);
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


function insert_new_text_cell_before_callback(status, response_text) {
    /*
    See the documentation for insert_new_text_cell_after_callback,
    since response_text is encoded in exactly the same way there.
    */
    var id, new_html, new_id, X;
    if (status === "failure") {
        alert("Problem inserting new text cell before current input cell.");
        return;
    }
    if (response_text === "locked") {
        alert("Worksheet is locked.  Cannot insert cells.");
        return;
    }

    // Insert a new cell _before_ a cell.
    X = response_text.split(SEP);
    new_id = toint(X[0]);
    new_html = X[1];
    id = toint(X[2]);
    do_insert_new_text_cell_before(id, new_id, new_html);
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
//
// CONTROL functions
//
///////////////////////////////////////////////////////////////////
function interrupt() {
    /*
    Send a message to the server that we would like to interrupt all
    running calculations in the worksheet.
    */
    async_request(worksheet_command('interrupt'), interrupt_callback);
}


function interrupt_callback(status, response_text) {
    /*
    Callback called after we send the interrupt signal to the server.
    If the interrupt succeeds, we change the CSS/DOM to indicate that
    no cells are currently computing.  If it fails, we display an
    annoying alert (it might be a good idea to change this, e.g., to
    blink red or something instead of an alert).
    */
    if (response_text === "failed") {
        alert('Unable to immediately interrupt calculation.');
        return;
    } else if (status === "success") {
        halt_active_cells();
    }
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
}


function halt_active_cells() {
    /*
    Set all cells so they do not look like they are being evaluates or
    queued up for evaluation, and empty the list of active cells from
    the global active_cell_list variable.
    */
    var i;
    for (i = 0; i < active_cell_list.length; i += 1) {
        cell_set_not_evaluated(active_cell_list[i]);
    }
    active_cell_list = [];
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
    halt_active_cells();
    set_all_cells_to_be_not_evaluated();
    async_request(worksheet_command('restart_sage'));
}


function quit_sage() {
    /*
    Called when the worksheet process is terminated.  All actively
    computing cells are stopped, and a request is sent to the server
    to quit the worksheet process.
    */
    halt_active_cells();
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
//
// Various POPUP WINDOWS
//
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
    window.open("http://spreadsheets.google.com/viewform?key=pCwvGVwSMxTzT6E2xNdo5fA", "", "menubar=1,location=1,scrollbars=1,width=800,height=650,toolbar=1,  resizable=1");
}


///////////////////////////////////////////////////////////////////
// Interact
///////////////////////////////////////////////////////////////////
function interact(id, input) {
    /*
    Cancels any current computations, then sends an interact request
    back to the server.  This is called by individual interact
    controls.

    INPUT:
        id -- integer or string; cell id
        input -- string
    */
    var cell_number;

    id = toint(id);
    active_cell_list.push(id);

    cell_has_changed = false;
    current_cell = id;

    // Delete the old images, etc., that might be sitting in the
    // output from the previous evaluation of this cell.
    get_element('cell_output_html_' + id).innerHTML = "";

    cell_number = get_element('cell_number_' + id);
    cell_number.className = 'cell_number_running';

    // The '__sage_interact__' string appears also in cell.py.
    async_request(worksheet_command('eval'), evaluate_cell_callback, {
        newcell: 0,
        id: id,
        input: '%__sage_interact__\n' + input
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
    if(confirm('Emptying the trash will permanently delete all items in the trash. Continue?')) {
        $('#empty-trash-form').submit();
    }
}


///////////////////////////////////////////////////////////////////
//
// KeyCodes (auto-generated from config.py and user's sage config
//
///////////////////////////////////////////////////////////////////


{{ KEY_CODES }}

{% include "js/jmol_lib.js" %}

{% include "js/canvas3d_lib.js" %}

{% include "js/async_lib.js" %}


// This is purely for debugging, diagnostics, etc.  Pass the options
// dictionary as the argument below.
(function debugging(options) {
    // One way to get function names:
    //    sed -nre "s/^function\s+(\w+)\s*\(.*/\1/p" notebook_lib.js
    // From JS, filtered coarsely:
    /*
    var funcs = [];
    for (x in window) {
        if (typeof(window[x]) === 'function') {
            if (x.slice(0, 4) !== 'key_' &&
                x.slice(0, 4) !== 'jmol' &&
                x.slice(0,5) !== '_jmol') {
                funcs.push(x);
            }
        }
    }
    */

    var funcs = [
        // 'toint',
        // 'initialize_the_notebook',
        // 'true_function',
        // 'get_keyboard',
        // 'jsmath_init',
        // 'get_element',
        // 'set_class',
        // 'key_event',
        // 'time_now',
        // 'current_selection',
        // 'get_selection_range',
        // 'set_selection_range',
        // 'get_cursor_position',
        // 'set_cursor_position',
        // 'modal_prompt',
        // 'refresh',
        // 'refresh_cell_list',
        // 'refresh_cell_list_callback',
        // 'is_whitespace',
        // 'first_variable_name_in_string',
        // 'lstrip',
        // 'resize_all_cells',
        // 'input_keyup',
        // 'handle_introspection',
        // 'do_replacement',
        // 'get_replacement_element',
        // 'replacement_element_exists',
        // 'select_replacement_element',
        // 'update_introspection_text',
        // 'halt_introspection',
        // 'paren_jump',
        // 'paren_match',
        // 'new_worksheet',
        // 'set_worksheet_list_checks',
        // 'checked_worksheet_filenames',
        // 'worksheet_list_button',
        // 'worksheet_list_button_callback',
        // 'delete_button',
        // 'make_active_button',
        // 'archive_button',
        // 'stop_worksheets_button',
        // 'download_worksheets_button',
        // 'history_window',
        // 'upload_worksheet_button',
        // 'copy_worksheet',
        // 'rate_worksheet',
        // 'download_worksheet',
        // 'worksheet_settings',
        // 'share_worksheet',
        // 'publish_worksheet',
        // 'save_as',
        // 'edit_worksheet',
        // 'save_worksheet',
        // 'save_worksheet_callback',
        // 'close_callback',
        // 'save_worksheet_and_close',
        // 'worksheet_discard',
        // 'rename_worksheet',
        // 'go_system_select',
        // 'system_select',
        // 'pretty_print_check',
        // 'handle_data_menu',
        // 'delete_worksheet',
        // 'delete_worksheet_callback',
        // 'go_option',
        // 'link_datafile',
        // 'list_rename_worksheet',
        // 'list_edit_worksheet',
        // 'list_copy_worksheet',
        // 'list_share_worksheet',
        // 'list_publish_worksheet',
        // 'list_revisions_of_worksheet',
        // 'server_ping_while_alive',
        // 'server_ping_while_alive_callback',
        // 'get_cell',
        // 'cell_blur',
        // 'send_cell_input',
        // 'evaluate_text_cell_input',
        // 'evaluate_text_cell_callback',
        // 'debug_focus',
        // 'debug_blur',
        // 'cell_focus',
        // 'cell_focused',
        // 'move_cursor_to_top_of_cell',
        // 'cell_input_resize',
        // 'cell_delete',
        // 'cell_delete_callback',
        // 'debug_input_key_event',
        // 'cell_input_key_event',
        // 'is_compute_cell',
        // 'extreme_compute_cell',
        // 'id_of_cell_delta',
        // 'debug_clear',
        // 'debug_append',
        // 'jump_to_cell',
        // 'escape0',
        // 'text_cursor_split',
        // 'indent_cell',
        // 'unindent_cell',
        // 'comment_cell',
        // 'uncomment_cell',
        // 'join_cell',
        // 'split_cell',
        // 'worksheet_command',
         'evaluate_cell',
         'evaluate_cell_introspection',
        // 'evaluate_cell_callback',
        // 'is_interacting_cell',
        // 'cell_output_set_type',
        // 'cycle_cell_output_type',
        // 'cell_set_evaluated',
        // 'cell_set_not_evaluated',
        // 'cell_set_running',
        // 'cell_set_done',
        // 'check_for_cell_update',
        // 'check_for_cell_update_callback',
        // 'continue_update_check',
        // 'start_update_check',
        // 'cancel_update_check',
        // 'contains_jsmath',
        // 'set_output_text',
        // 'set_input_text',
        // 'CellWriter',
        // 'eval_script_tags',
        // 'separate_script_tags',
        // 'slide_mode',
        // 'cell_mode',
        // 'slide_hide',
        // 'slide_show',
        // 'slide_first',
        // 'slide_last',
        // 'slide_next',
        // 'slide_prev',
        // 'jump_to_slide',
        // 'update_slideshow_progress',
        // 'make_new_cell',
        // 'make_new_text_cell',
        // 'do_insert_new_cell_before',
        // 'do_insert_new_text_cell_before',
        // 'insert_new_cell_after',
        // 'insert_new_cell_after_callback',
        // 'insert_new_text_cell_after',
        // 'insert_new_text_cell_after_callback',
        // 'do_insert_new_cell_after',
        // 'do_insert_new_text_cell_after',
        // 'insert_new_cell_before',
        // 'insert_new_cell_before_callback',
        // 'insert_new_text_cell_before',
        // 'insert_new_text_cell_before_callback',
        // 'append_new_cell',
        // 'append_new_text_cell',
        // 'interrupt',
        // 'interrupt_callback',
        // 'evaluate_all',
        // 'hide_all',
        // 'show_all',
        // 'delete_all_output',
        // 'halt_active_cells',
        // 'set_all_cells_to_be_not_evaluated',
        // 'restart_sage',
        // 'quit_sage',
        // 'login',
        // 'history_window',
        // 'print_worksheet',
        // 'help',
        // 'bugreport',
         'interact',
        // 'encode64',
        // 'decode64',
        // 'empty_trash'
        ''
    ], i, s;

    if (!window.console) {
        window.console = {};
        if (window.opera) {
            window.console.log = opera.postError;
        } else {
            window.console.log = function () {};
        }
    }

    // TODO: Display a live call stack of wrapped functions in a
    // floating div.

    // Wrap selected functions in proxies.  This allows us to log
    // their arguments, globals, etc., when they're called.
    if (options.proxify === true) {
        for (i = 0; i < funcs.length; i += 1) {
            if (typeof(window[funcs[i]]) !== 'function') {
                continue;
            }

            // Evaluate here, for immediate closure.
            window[funcs[i]] = (function () {
                // Private variables.
                var name = funcs[i], orig = window[funcs[i]];

                return function () {
                    // Is logging on or off?  Check a global variable.
                    // This allows us to toggle logging w/o reloading.
                    if (sage_debug_log) {
                        console.log('active_cell_list', active_cell_list);

                        if (this !== window) {
                            console.log(name, this, arguments);
                        } else {
                            console.log(name, arguments);
                        }
                    }
                    return orig.apply(this, arguments);
                };
            }());
        }
    }

// Change the settings to false for releases!
}({proxify: false}));
