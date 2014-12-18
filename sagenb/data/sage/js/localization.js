/*global $, alert, async_request, clearTimeout, confirm, document, escape, location, navigator, open, prompt, setTimeout, window, worksheet_filenames */
/*jslint maxerr: 10000, white: true, onevar: true, undef: true, nomen: true, eqeqeq: true, plusplus: true, bitwise: true, regexp: true, strict: true, newcap: true, immed: true */
//"use strict";

{# If you add any new strings to this list, please enclose them in the dummy
  translation function N_ (or nN_ for singular/plural forms). #}

translations = {
    {% for string in [N_('Your browser / OS combination is not supported.\\nPlease use Firefox or Opera under Linux, Windows, or Mac OS X, or Safari.'),
                      N_("Java Applet Hidden"),
                      N_("Click here to pop out"),
                      N_('Error applying function to worksheet(s).'),
                      N_('Title of saved worksheet'),
                      N_('Failed to save worksheet.'),
                      N_("Rename worksheet"),
                      N_("Please enter a name for this worksheet."),
                      N_("Rename"),
                      N_('Possible failure deleting worksheet.'),
                      N_("unprinted"),
                      N_('You requested to evaluate a cell that, for some reason, the server is unaware of.'),
                      N_("Error"),
                      N_('This worksheet is read only. Please make a copy or contact the owner to change it.'),
                      N_("loading..."),
                      N_('Error updating cell output after '),
                      N_('s (canceling further update checks).'),
                      N_('Problem inserting new input cell after current input cell.\\n'),
                      N_('Problem inserting new input cell before current input cell.\\n'),
                      N_('Problem inserting new text cell before current input cell.'),
                      N_('Problem inserting new text cell before current input cell.\\n'),
                      N_('Worksheet is locked. Cannot insert cells.'),
                      N_('Unable to interrupt calculation.'),
                      N_('Close this box to stop trying.'),
                      N_('Interrupt attempt'),
                      N_("<a href='javascript:restart_sage();'>Restart</a>, instead?"),
                      N_("Emptying the trash will permanently delete all items in the trash. Continue?"),
                      N_("Get Image"),
                      N_('Jmol Image'),
                      N_("To save this image, you can try right-clicking on the image to copy it or save it to a file, or you may be able to just drag the image to your desktop."),
                      N_("Sorry, but you need a browser that supports the &lt;canvas&gt; tag."),
                     ] %}
    "{{ string }}" : "{{ gettext(string) }}",
    {% endfor %}
    {% for singular, plural in [nN_('Trying again in %(num)d second...', 'Trying again in %(num)d seconds...')] %}
    "{{ singular }}" : function (n) {return n >1 ? '{{ ngettext(singular, plural, 2) }}'.replace("2", n) : '{{ ngettext(singular, plural, 1) }}'} {% if not loop.last %},{% endif %}
    {% endfor %}
};
