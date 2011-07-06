/*global $, window */
/*jslint white: true, onevar: true, undef: true, nomen: true, eqeqeq: true, plusplus: true, bitwise: true, regexp: true, strict: true, newcap: true, immed: true */
//"use strict";

var replicate_str = function(x, n) {
    var str = '';
    for (var i = 0; i < n; ++i) {
        str += x;
    }
};

$(function () {
    var body = $('body'), body_id = body.attr('id');

    if (body.hasClass('active-worksheet')) {
        initialize_the_notebook();
        $('.introspection .docstring .click-message', '#worksheet_cell_list')
            .live('click', function (e) {
                var ds_elem = $(this).parent(), id, name, style;

                id = toint(ds_elem.parent().attr('id').slice(15));
                name = introspect[id].before_replacing_word;

                if (name.slice(-2) === '??') {
                    // Source code.
                    name = name.slice(0, -2);
                    style = 'color: #007020';
                } else if (name.slice(-1) === '?' || name.slice(-1) === '(') {
                    // Docstring.
                    name = name.slice(0, -1);
                    style = 'color: #0000aa';
                }

                halt_introspection(id);

                ds_elem.dialog({
                    height: 600,
                    width: '90%',
                    title: '<span style="' + style + '">' + name + '<span>',
                    dialogClass: 'docstring-introspection-dialog',
                    'close': function (event, ui) {
                        ds_elem.dialog('destroy').remove();
                    }
                });
                ds_elem.find('.click-message').remove();
            });
    }
});
