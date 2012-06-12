/*global $, queue_id_list, cell_id_list, console, document, opera, setTimeout, window */
/*jslint white: true, onevar: true, undef: true, nomen: true, eqeqeq: true, plusplus: true, bitwise: true, regexp: true, strict: true, newcap: true, immed: true */
//"use strict";

// For debugging, diagnostics, etc.
var sagenb_debug = (function debugging(options) {
    var dlg, funcs, i, s, settings;

    // Defaults, overridden by an optional options argument.
    settings = {
        // Whether to wrap functions in proxies for logging.  This
        // takes effect *only* on load.
        proxify: false,
        // Turn on/off logging of already proxified functions w/o
        // reloading.
        log: true,
        // Whether to log to a floating jQuery UI dialog.
        // Experimental.
        dialog: false
    };
    $.extend(settings, options || {});

    if (!window.console) {
        window.console = {};
        if (window.opera) {
            window.console.log = opera.postError;
        } else {
            window.console.log = function () {};
        }
    }

    // Wrap selected functions in proxies.  This allows us to log
    // their arguments, globals, etc., when they're called.  If
    // proxify is false on load, nothing special happens.
    if (!settings.proxify) {
        return {settings: settings};
    }

    // Function names.  Make a list with sed, Python, or JS:
    // sed -nre "s/^function\s+(\w+)\s*\(.*/\1/p" notebook_lib.js
    /*
    import re
    s = r'(?<!//)(?:(?:\s*var\s+)?(\w+)\s*=)?\s*function\s+(\w+)?\s*\('
    m = re.findall(s, open('notebook_lib.js').read(), re.MULTILINE)
    funcs = reduce(lambda x, y: x + y, [[x for x in g if len(x)] for g in m])
    */
    /*
    function get_func_names() {
        var funcs = [];
        for (x in window) {
            if (typeof(window[x]) === 'function') {
                if (x.slice(0, 4) !== 'key_' && x.slice(0, 4) !== 'jmol' &&
                    x.slice(0, 5) !== '_jmol') {
                    funcs.push(x);
                }
            }
        }
        return funcs;
    }
    */

    funcs = [
        // 'toint',
        // 'decode_response',
        // 'encode_response',
        // 'initialize_the_notebook',
        // 'true_function',
        // 'get_keyboard',
        // 'mathjax_init',
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
        // 'cell_focus',
        // 'cell_focused',
        // 'cell_input_resize',
        // 'cell_delete',
        // 'cell_delete_callback',
        // 'cell_delete_output',
        // 'cell_delete_output_callback',
        // 'cell_input_key_event',
        // 'is_compute_cell',
        // 'extreme_compute_cell',
        // 'id_of_cell_delta',
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
        // 'evaluate_cell_introspection',
         'evaluate_cell_callback',
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
        // 'halt_queued_cells',
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
        // 'empty_trash',
        ''
    ];

    for (i = 0; i < funcs.length; i += 1) {
        if (typeof(window[funcs[i]]) !== 'function') {
            continue;
        }

        // Evaluate here, for immediate closure.
        window[funcs[i]] = (function () {
            // Private variables.
            var name = funcs[i] + ' ', orig = window[funcs[i]];

            return function () {
                if (settings.log) {
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

    // We "subclass" Array to log changes to it *when* they happen.
    // Since we'd like to monitor the queue_id_list, we reimplement
    // just the methods we use in notebook_lib.js.
    function A2() {
        // The constructor requires at least one argument: the array's
        // name or description.
        var args = Array.prototype.slice.call(arguments).slice(1);
        this.name = arguments[0];
        this.store = [];
        Array.prototype.push.apply(this.store, args);
        return Array.prototype.push.apply(this, args);
    }

    // Same as A2.prototype = new Array();
    A2.prototype = [];

    function prep_dialog() {
        var par;
        dlg = $('<div id="debug"></div>').dialog({
            autoOpen: false,
            minHeight: '',
            height: 'auto',
            width: '300',
            title: 'debug'
        });

        par = dlg.parent();
        par.css({
            left: $(document).width() - par.width() - 30 + 'px',
            padding: '1px',
            top: $(window).scrollTop() + 'px'
        });
        $(window).bind('scroll.pin', function () {
            setTimeout(function () {
                par.css({top: $(window).scrollTop() + 'px'});
            }, 1000);
        });

        $('.ui-dialog-titlebar', par).css({
            paddingTop: 0,
            paddingBottom: 0
        });
    }

    function update_dialog(name, value) {
        var s = 'Cells: ';
        $.map(cell_id_list, function (id) {
            if ($.inArray(id, queue_id_list) !== -1) {
                s += '<span style="color: red;">' + id + '</span>' + ' ';
            } else {
                s += id + ' ';
            }
        });
        s += '<br />' + name + ': ' + value.toString();

        if (!dlg) {
            prep_dialog();
        }
        dlg.dialog('open').html(s);
    }

    A2.prototype.display = function () {
        if (settings.log) {
            if (settings.dialog) {
                update_dialog(this.name, this.store);
            } else {
                console.log(this.name + ' ', this.store);
            }
        }
    };

    A2.prototype.push = function (x) {
        var ret = Array.prototype.push.call(this, x);
        this.store.push(x);
        this.display();
        return ret;
    };

    A2.prototype.splice = function () {
        var ret = Array.prototype.splice.apply(this, arguments);
        this.store.splice.apply(this.store, arguments);
        this.display();
        return ret;
    };

    $(document).ready(function () {
        var q2, i;

        if (!$('#worksheet_cell_list').length) {
            return;
        }

        q2 = new A2('Queued');
        for (i = 0; i < queue_id_list.length; i += 1) {
            q2.push(queue_id_list[i]);
        }
        queue_id_list = q2;
        queue_id_list.display();
    });

    // Example: To turn off logging w/o reloading the page:
    // sagenb_debug.settings.log = false;
    return {settings: settings};
// Pass just {} to use the default settings.
}({proxify: false}));
