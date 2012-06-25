/* The general Sage Notebook javascript "namespace"
 * and object. 
 * 
 * AUTHORS - Samuel Ainsworth (samuel_ainsworth@brown.edu)
 */

// the sagenb "namespace"
var sagenb = {};

// the username
sagenb.username = "";
sagenb.ctrlkey = "";
// other general variables go here

sagenb.init = function() {
	// TODO is this wrong? ie, is it possible to look at someone else's worksheet?
	// grab the username from the url
	sagenb.username = window.location.pathname.substring(6).split("/")[0];
	
	// update username
	$("#username").text(sagenb.username);
	
	/* swap control/command on mac operating system */
	sagenb.ctrlkey = "Ctrl";
	if(navigator.userAgent.indexOf("Mac") !== -1) {
		sagenb.ctrlkey = "Cmd";
	}
	
	$("#log").click(sagenb.history_window);
	$("#report_a_problem").click(function(e) {
		window.open('http://spreadsheets.google.com/viewform?key=pCwvGVwSMxTzT6E2xNdo5fA', '', 'menubar=1,location=1,scrollbars=1,width=800,height=650,toolbar=1,resizable=1');
	});
	
	sagenb.spinner = new Spinner({
		hwaccel: true
	});
};

sagenb.start_loading = function() {
	$(".the_page").fadeTo(0, 0.5);
	sagenb.spinner.spin($("body")[0]);
};
sagenb.done_loading = function() {
	$(".the_page").fadeTo('slow', 1);
	sagenb.spinner.stop();
};

sagenb.show_connection_error = function() {
	$(".alert_connection").show();
};
sagenb.hide_connection_error = function() {
	$(".alert_connection").hide();
};

sagenb.async_request = function(url, callback, postvars) {
    var settings = {
        url: url,
        async: true,
        cache: false,
        dataType: "text"
    };

    if ($.isFunction(callback)) {
        settings.error = function (XMLHttpRequest, textStatus, errorThrown) {
            callback("failure", errorThrown);
        };
        settings.success = function (data, textStatus) {
            callback("success", data);
        };
    }

    if (postvars) {
        settings.type = "POST";
        settings.data = postvars;
    } else {
        settings.type = "GET";
    }

    $.ajax(settings);
}
sagenb.generic_callback = function(extra_callback) {
	/* Constructs a generic callback function. The extra_callback
	* argument is optional. If the callback receives a "success"
	* status (and extra_callback is a function), extra_callback 
	* will be called and passed the status and response arguments.
	* If you use generic_callback with no extra_callback, you *must*
	* call generic_callback() not just generic_callback because 
	* this function is not a callback itself; it returns a callback
	* function.
	*/
	
	return function(status, response) {
		if(status !== "success") {
			sagenb.show_connection_error();
			
			// don't continue to extra_callback
			return;
		} else {
			// status was good, hide alert
			sagenb.hide_connection_error();
		}
	
		// call the extra callback if it was given
		if($.isFunction(extra_callback)) {
			extra_callback(status, response);
		}
	}
};

sagenb.history_window = function() {
    /*
    Display the history popup window, which displays the last few hundred
    commands typed into any worksheet.
    */
    window.open("/history", "", "menubar=1,scrollbars=1,width=800," +
                "height=600,toolbar=1,resizable=1");
}