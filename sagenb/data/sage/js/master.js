$(window).load(function () {
    body = $('body'), body_id = body.attr('id');
    if (body_id === 'worksheet-listing-page') {
        checkForGearsInstalled();
    }

    if (body.hasClass('worksheet-online')) {
        initialize_the_notebook();
    }
});
