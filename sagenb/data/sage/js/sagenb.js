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
	
	$("#report_a_problem").click(function(e) {
		window.open('http://spreadsheets.google.com/viewform?key=pCwvGVwSMxTzT6E2xNdo5fA', '', 'menubar=1,location=1,scrollbars=1,width=800,height=650,toolbar=1,resizable=1');
	});
};