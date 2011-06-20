//if notebook_lib.js becomes modular, escape0 can be loaded from it 
//

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

function rate_worksheet() {
    /*
    Save the comment and rating that the uses chooses for a public worksheet.

    INPUT:
        rating -- integer
    */
    var rating, comment;
    comment = $("#rating_comment").val();
    rating = $(':radio[name="rating"]:checked').val();
    //i18n
    if (!rating){
        alert("Select a rating.");
        return;
    }
    window.location.replace("rate?rating=" + rating +
                                              "&comment=" + escape0(comment));
}

$(function (){
    $('#rate_button').click(rate_worksheet);
    $('#rating_comment').one('click', function (){
        this.value = '';
    });
});
