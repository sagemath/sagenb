/*global $, window */
/*jslint white: true, onevar: true, undef: true, nomen: true, eqeqeq: true, plusplus: true, bitwise: true, regexp: true, strict: true, newcap: true, immed: true */
//"use strict";

$(window).load(function () {
    var body = $('body'), body_id = body.attr('id');
    if (body_id === 'worksheet-listing-page') {
        checkForGearsInstalled();
    }

    if (body.hasClass('worksheet-online')) {
        initialize_the_notebook();
    }
});
