/*
 * File of misc javascript functions used
 */

function toint(x) {
	/*
	Convert a object to an integer, if it's possible.  We use this to
	convert a cell id to an integer if it's just a string
	representation of that integer.  Otherwise, we return the original
	id.  This allows us to use alphanumeric ids for special cells.

	INPUT:
		x -- any object, e.g., a string, integer, float, etc.
	OUTPUT:
		an integer or the object
	 */
	if (x === '0') {
		return 0;
	} else {
		return parseInt(x, 10) || x;
	}
}


function decode_response(text) {
	/*
	Reconstructs a JSON-encoded object from a string.  We use this to
	parse server responses into cell IDs, data, etc.  In particular,
	any key in the reconstructed object that ends in 'id' is filtered
	through toint.

	INPUT:
		text -- string
	OUTPUT:
		object
	*/
	return JSON.parse(text, function (key, value) {
		if (typeof(key) === 'string' && key.slice(-2) === 'id') {
			return toint(value);
		}
		return value;
	});
}

function encode_response(obj) {
	/*
	JSON-encodes a object to a string.

	INPUT:
		obj -- object
	OUTPUT:
		string
	*/
	return JSON.stringify(obj);
}

function system_to_codemirror_mode(system) {
	var mode = "";
	
	// TODO use an Object here instead of a massive switch statement
	switch(system) {
		case "sage":
			mode = "python";
			break;
		case "gap":
			mode = "";
			break;
		case "gp":
			mode = "";
			break;
		case "html":
			mode = "htmlmixed";
			break;
		case "latex":
			mode = "stex";
			break;
		case "maxima":
			mode = "";
			break;
		case "python":
			mode = "python";
			break;
		case "r":
			mode = "r";
			break;
		case "sh":
			mode = "shell";
			break;
		case "singular":
			mode = "";
			break;
		case "axiom":
			mode = "";
			break;
		case "kash":
			mode = "";
			break;
		case "macaulay2":
			mode = "";
			break;
		case "magma":
			mode = "";
			break;
		case "maple":
			mode = "";
			break;
		case "mathematica":
			mode = "";
			break;
		case "matlab":
			mode = "";
			break;
		case "mupad":
			mode = "";
			break;
		case "octave":
			mode = "";
			break;
		case "scilab":
			mode = "";
			break;
		
		default:
			mode = "python"
			break;
	}
	
	return mode;
}

///////////////////////////////////////////////////////////////////
// Base 64 encoding and decoding (mainly used for @interact).
///////////////////////////////////////////////////////////////////

//////////////////////////////////////////////////////////////////
// The following header applies to the encode64 and decode64 functions
// This code was written by Tyler Akins and has been placed in the
// public domain.  It would be nice if you left this header intact.
// Base64 code from Tyler Akins -- http://rumkin.com
//////////////////////////////////////////////////////////////////
var keyStr = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=";

function encode64(input) {
	/*
	Base 64 encode the given input.

	INPUT:
		input -- string
	OUTPUT:
		string
	*/
	// I had to add this, since otherwise when input is numeric there
	// are errors below.
	var chr1, chr2, chr3, enc1, enc2, enc3, enc4, i = 0, output = "";

	try {
		input = input.toString();
	} catch (e) {
		return input;
	}

	while (i < input.length) {
		chr1 = input.charCodeAt(i++);
		chr2 = input.charCodeAt(i++);
		chr3 = input.charCodeAt(i++);

		enc1 = chr1 >> 2;
		enc2 = ((chr1 & 3) << 4) | (chr2 >> 4);
		enc3 = ((chr2 & 15) << 2) | (chr3 >> 6);
		enc4 = chr3 & 63;

		if (isNaN(chr2)) {
			enc3 = 64;
			enc4 = 64;
		} else if (isNaN(chr3)) {
			enc4 = 64;
		}

		output = output + keyStr.charAt(enc1) + keyStr.charAt(enc2) +
			keyStr.charAt(enc3) + keyStr.charAt(enc4);
	}

	return output;
}

function decode64(input) {
	/*
	Base 64 decode the given input.

	INPUT:
		input -- string
	OUTPUT:
		string
	*/
	var chr1, chr2, chr3, enc1, enc2, enc3, enc4, i = 0, output = "";

	// remove all characters that are not A-Z, a-z, 0-9, +, slash, or =
	input = input.replace(/[^A-Za-z0-9\+\/\=]/g, "");

	while (i < input.length) {
		enc1 = keyStr.indexOf(input.charAt(i++));
		enc2 = keyStr.indexOf(input.charAt(i++));
		enc3 = keyStr.indexOf(input.charAt(i++));
		enc4 = keyStr.indexOf(input.charAt(i++));

		chr1 = (enc1 << 2) | (enc2 >> 4);
		chr2 = ((enc2 & 15) << 4) | (enc3 >> 2);
		chr3 = ((enc3 & 3) << 6) | enc4;

		output = output + String.fromCharCode(chr1);

		if (enc3 !== 64) {
			output = output + String.fromCharCode(chr2);
		}
		if (enc4 !== 64) {
			output = output + String.fromCharCode(chr3);
		}
	}

	return output;
}