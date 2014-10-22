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
//'#worksheet_cell_list' why was it function (e) below.
        $(document)
            .on('click','#worksheet_cell_list .introspection .docstring .click-message', function (e) {
                var ds_elem = $(this).parent(), style;

                var id = toint(ds_elem.parent().attr('id').slice(15));
                var name = introspect[id].before_replacing_word;

                if (name.slice(-2) === '??') {
                    // Source code.
                    name = name.slice(0, -2);
                    style = 'source';
                } else if (name.slice(-1) === '?' || name.slice(-1) === '(') {
                    // Docstring.
                    name = name.slice(0, -1);
                    style = 'doc';
                }

                halt_introspection(id);

                ds_elem.dialog({
                    height: 600,
                    width: '90%',
                    title: name,
                    dialogClass: 'docstring-introspection-dialog-'+style,
                    'close': function (event, ui) {
                        ds_elem.dialog('destroy').remove();
                    }
                });
                ds_elem.find('.click-message').remove();
            });
    }
});
