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
	// grab the username from the url
	sagenb.username = window.location.pathname.substring(6).split("/")[0];
	
	// update username
	$("#username").text(sagenb.username);
	
	/* swap control/command on mac operating system */
	sagenb.ctrlkey = "Ctrl";
	if(navigator.userAgent.indexOf("Mac") !== -1) {
		sagenb.ctrlkey = "Cmd";
	}
	
};