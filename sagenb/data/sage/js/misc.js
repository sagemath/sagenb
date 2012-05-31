/*
 * File of misc javascript functions used
 */

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