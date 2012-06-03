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

function lstrip(s) {
    /*
    Given a string s, strip leading whitespace from s and return the
    resulting string.

    INPUT:
        s -- a string
    OUTPUT:
        a string
    */
    var i = 0, n = s.length;
    while (i < n && (s[i] === ' ' || s[i] === '\n' || s[i] === '\t')) {
        i = i + 1;
    }
    return s.slice(i);
}


function system_to_codemirror_mode(system) {
	var mode = "";
	
	switch(system) {
		case "sage":
			/* TODO write a specific mode for sage
			* for now, python and sage are so similar
			* we don't bother making a difference.
			*/
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