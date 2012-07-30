/* The general Sage Notebook javascript "namespace"
 * and object. 
 * 
 * AUTHORS - Samuel Ainsworth (samuel_ainsworth@brown.edu)
 */

// the sagenb "namespace"
var sagenb = {};

sagenb.init = function() {
	// update username
	if(sagenb.username === "guest") {
		$("#user_navbar_area").html(
'<div class="btn-group pull-right nav">' +
	'<a href="#" class="btn"><i class="icon-user"></i>' + gettext('Login') + '</a>' +
'</div>'
		);
	}
	else {
		$("#user_navbar_area").html(
'<div class="btn-group pull-right nav">' +
	'<a class="btn dropdown-toggle" data-toggle="dropdown" href="#">' +
		'<i class="icon-user"></i> <span id="username">' + sagenb.username + ' </span>' +
		'<span class="caret"></span>' +
	'</a>' +
	'<ul class="dropdown-menu">' +
		'<li><a href="/" id="home"><i class="icon-home"></i> ' + gettext('Home') + '</a></li>' +
		'<li><a href="/home/pub" id="published"><i class="icon-share"></i> ' + gettext('Published') + '</a></li>' +
		'<li><a href="#" id="log"><i class="icon-list"></i> ' + gettext('Log') + '</a></li>' +
		'<li><a href="/settings" id="settings"><i class="icon-wrench"></i> ' + gettext('Settings') + '</a></li>' +
		'<li><a href="/logout" id="sign_out"><i class="icon-off"></i> ' + gettext('Sign out') + '</a></li>' +
		'<li class="divider"></li>' +
		'<li class="nav-header">' + gettext('Support') + '</li>' +
		'<li><a href="#" id="help"><i class="icon-book"></i> ' + gettext('Help') + '</a></li>' +
		'<li><a href="#" id="report_a_problem"><i class="icon-exclamation-sign"></i> ' + gettext('Report a Problem') + '</a></li>' +
	'</ul>' +
'</div>'
		);
	}
	
	/* swap control/command on mac operating system */
	sagenb.ctrlkey = "Ctrl";
	if(navigator.userAgent.indexOf("Mac") !== -1) {
		sagenb.ctrlkey = "Cmd";
	}
	
	$("#log").click(sagenb.history_window);
	$("#report_a_problem").click(function(e) {
		window.open('http://spreadsheets.google.com/viewform?key=pCwvGVwSMxTzT6E2xNdo5fA', '', 'menubar=1,location=1,scrollbars=1,width=800,height=650,toolbar=1,resizable=1');
	});
	$("#help").click(sagenb.help);
	$(document).bind("keydown", "F1", function(evt) { sagenb.help(); return false; });
	
	sagenb.spinner = new Spinner({
		hwaccel: true
	});
	
	//// IMPORT DIALOG ////
	$("#import_modal .btn-primary").click(function(e) {
		$("#import_modal .tab-pane.active form").submit();
	});
	$("#import_modal .btn").click(function(e) {
		$.each($("#import_modal form"), function(i, form) {
			form.reset();
		});
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
    window.open("/history", "", "menubar=1,scrollbars=1,width=800,height=600,toolbar=1,resizable=1");
};
sagenb.help = function() {
    /*
    Popup the help window.
    */
    window.open("/help", "", "menubar=1,location=1,scrollbars=1,width=800,height=650,toolbar=1,  resizable=1");
}