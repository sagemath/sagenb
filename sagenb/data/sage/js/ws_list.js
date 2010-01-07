/*global window, $, worksheet_filenames */
/*jslint browser: true, white: true, onevar: true, undef: true, nomen: true, eqeqeq: true, plusplus: true, bitwise: true, regexp: true, strict: true, newcap: true, immed: true */
//"use strict";

/*
  INDENTATION:
  All code should have 4-space indentation, exactly like in our Python code.

  DOCSTRINGS:
  All functions below must be documented using the following format,
  with the docstring in C-style comments.

  Short description.

  Longer description.

  INPUT:
  each input variable name -- description of it.
  GLOBAL INPUT:
  each global variable that significantly impacts
  the behavior of this function and how
  OUTPUT:
  description of output or side effects.
*/

var SEP = '___S_A_G_E___';

function async_request(url, callback, postvars) {
    var settings = {url : url,
                    async : true,
                    cache : false,
                    dataType: 'text'};

    if ($.isFunction(callback)) {
        settings.error = function (XMLHttpRequest, textStatus, errorThrown) {
            callback('failure', errorThrown);
        };
        settings.success = function (data, textStatus) {
            callback('success', data);
        };
    }

    if (postvars !== null) {
        settings.type = 'POST';
        settings.data = postvars;
    } else {
        settings.type = 'GET';
    }

    $.ajax(settings);
}

function set_worksheet_list_checks() {
    /*
      Go through and set all check boxes the same as they are in the
      control box.

      This is called when the user clicks the checkbox in the top left
      of the list of worksheets, which toggles all the checkboxes below
      it to be either on or off (select all or none).

      GLOBAL INPUT:
      worksheet_filenames -- list of strings
    */
    var cbox_checked, i, ws_len, ws_name;
    cbox_checked = $('#controlbox')[0].checked;
    ws_len = worksheet_filenames.length;
    for (i = 0; i < ws_len; i += 1) {
        ws_name = worksheet_filenames[i].replace(/[\/@.]/g, '-');
        $('#' + ws_name)[0].checked = cbox_checked;
    }
}

function checked_worksheet_filenames() {
    /*
      For each filename listed in worksheet_filenames, look up the
      corresponding input check box, see if it is checked, and if so,
      add it to the list.

      GLOBAL INPUT:
      worksheet_filenames -- list of strings
      SEP -- separator string used when encoding tuples of data to send
      back to the server.
      OUTPUT:
      string of worksheet filenames that are checked, separated by SEP
    */
    var filenames = [], i, ws_box, ws_len, ws_name;
    ws_len = worksheet_filenames.length;

    // Concatenate the list of all worksheet filenames that are checked
    // together separated by the separator string.
    for (i = 0; i < ws_len; i += 1) {
        ws_name = worksheet_filenames[i];
        ws_box = $('#' + ws_name.replace(/[\/@.]/g, '-'))[0];
        if (ws_box.checked) {
            filenames.push(ws_name);
            ws_box.checked = 0;
        }
    }
    return filenames.join(SEP);
}

function worksheet_list_button_callback(status, response_text) {
    /*
      Handle result of performing some action on a list of worksheets.

      INPUT:
      status, response_text -- standard AJAX return values
      OUTPUT:
      display an alert if something goes wrong; refresh this
      browser window no matter what.
    */
    if (status === 'success') {
        if (response_text !== '') {
            alert(response_text);
        }
    } else {
        alert('Error applying function to worksheet(s).' + response_text);
    }
    window.location.reload(true);
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
      SEP -- separator string used when encoding tuples of data to send
      back to the server.
      OUTPUT:
      calls the server and requests an action be performed on all the
      listed worksheets
    */
    // Send the list of worksheet names and requested action back to
    // the server.
    async_request(action, worksheet_list_button_callback,
                  {filenames: checked_worksheet_filenames(), sep: SEP});
}

function delete_button() {
    /*
      This javascript function is called when the worksheet list delete
      button is pressed.  Each worksheet whose box is checked gets sent
      to the trash.
    */
    worksheet_list_button('/send_to_trash');
}

function make_active_button() {
    /*
      Sends each checked worksheet to the active worksheets folder.
    */
    worksheet_list_button('/send_to_active');
}

function archive_button() {
    /*
      Sends each checked worksheet to the archived worksheets folder.
    */
    worksheet_list_button('/send_to_archive');
}

function stop_worksheets_button() {
    /*
      Saves and then quits sage process for each checked worksheet.
    */
    worksheet_list_button('/send_to_stop');
}

function download_worksheets_button() {
    /*
      Downloads the set of checked worksheets as a zip file.
    */
    window.location.replace('/download_worksheets?filenames=' + checked_worksheet_filenames() + '&sep=' + SEP);
}

function history_window() {
    /*
      Display the history popup window, which displays the last few hundred
      commands typed into any worksheet.
    */
    window.open('/history', '', 'menubar=1,scrollbars=1,width=800,height=600, toolbar=1,resizable=1');
}

function delete_worksheet_callback(status, response_text) {
    /*
      Replace the current page by a page that shows the worksheet in the trash,
      or if the delete worksheet function failed display an error.
    */
    if (status === 'success') {
        window.location.replace('/?typ=trash');
    } else {
        alert('Possible failure deleting worksheet.');
    }
}

function delete_worksheet(name) {
    /*
      Send the worksheet with the given name to the trash.
      INPUT:
      name -- string
    */
    async_request('/send_to_trash', delete_worksheet_callback,
                  {filename: name});
}

function history_window() {
    /*
      Popup the history window.
    */
    window.open('/history', '', 'menubar=1,scrollbars=1,width=800,height=600,toolbar=1,resizable=1');
}

function help() {
    /*
      Popup the help window.
    */
    window.open('/help', '', 'menubar=1,location=1,scrollbars=1,width=800,height=650,toolbar=1,resizable=1');
}

function bugreport() {
    /*
      Popup the bug report window.
    */
    window.open('http://spreadsheets.google.com/viewform?key=pCwvGVwSMxTzT6E2xNdo5fA', '', 'menubar=1,location=1,scrollbars=1,width=800,height=650,toolbar=1,resizable=1');
}

function empty_trash() {
    /*
      This asks for confirmation from the user then sends a request back to the
      server asking that the trash be emptied for this user. The request to the
      server goes by accessing the url /emptytrash.  After that finishes, the
      empty trash folder is displayed.
    */
    if (confirm('Emptying the trash will permanently delete all items in the trash. Continue?')) {
        window.location.replace('/emptytrash');
    }
}
