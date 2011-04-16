/*
	Copyright 2008 SLB Software, LLC.

	This program is free software: you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation, either version 3 of the License, or
	(at your option) any later version.

	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.

	You should have received a copy of the GNU General Public License
	along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/

/**
 * Compute an HMAC based on SHA-256 using the supplied key and message data.
 * key - a secret encryption key.  can be either a string or an array of bytes.
 * data - the message to be hashed.  can be either a string or an array of bytes.
 * returnBytes - optional, defaults to false.
 * If returnBytes is false, then the hash value is returned as a 64 
 * hexadecimal-character string.
 * If returnBytes is true, then the hash value is returned as a 32 byte array.
 */
function hmac_sha256(key, data, returnBytes) {
	var	keyBytes, i, ipad, opad, dataBytes;

	if (key.length > 64) {
		keyBytes = sha256(key, true);
	} else if (typeof(key) == "string") {
		keyBytes = [];
		for (i = 0 ; i < key.length ; ++i)
			keyBytes[i] = key.charCodeAt(i);
	} else
		keyBytes = key;

	ipad = [];
	opad = [];
	for (i = 0 ; i < keyBytes.length ; ++i) {
		ipad[i] = keyBytes[i] ^ 0x36;
		opad[i] = keyBytes[i] ^ 0x5c;
	}
	for ( ; i < 64 ; ++i) {
		ipad[i] = 0x36;
		opad[i] = 0x5c;
	}

	if (typeof(data) == "string") {
		dataBytes = [];
		for (i = 0 ; i < data.length ; ++i)
			dataBytes[i] = data.charCodeAt(i);
	} else
		dataBytes = data;

	return sha256(opad.concat(sha256(ipad.concat(dataBytes), true)), returnBytes);
}

/**
 * Computes an SHA-256 hash.
 * data - the data to be hashed.  can be either a string or an array of bytes.
 * returnBytes - optional, defaults to false.
 * If returnBytes is false, then the hash value is returned as a 64 
 * hexadecimal-character string.
 * If returnBytes is true, then the hash value is returned as a 32 byte array.
 * Returns an array of 32 bytes: the computed hash value.
 */
function sha256(data, returnBytes) {
	function add(x, y) {
		return (x + y) & 0xffffffff;
	}

	function rot(x, n) {
		return (x >>> n) | (x << (32 - n));
	}

	function unpack(dword, dest) {
		dest.push((dword >>> 24) & 0xff);
		dest.push((dword >>> 16) & 0xff);
		dest.push((dword >>> 8) & 0xff);
		dest.push(dword & 0xff);
	}

	function dwordToHex(dword) {
		return (0x10000 + ((dword >>> 16) & 0xffff)).toString(16).substring(1)
			  + (0x10000 + ( dword         & 0xffff)).toString(16).substring(1);
	}

	var	bin, l, h0, h1, h2, h3, h4, h5, h6, h7, w, a, b, c, d, e, f, g, h, i, j, T1, T2;

	// pack input bytes into 32 bit words
	bin = [];
	if (typeof(data) == "string") {
		for (i = 0 ; i < data.length ; ++i)
			bin[i >> 2] |= (data.charCodeAt(i) & 0xff) << ((3 - (i & 3)) << 3);
	} else {
		for (i = 0 ; i < data.length ; ++i)
			bin[i >> 2] |= (data[i] & 0xff) << ((3 - (i & 3)) << 3);
	}

	// append a 1 bit
	l = data.length << 3;
	bin[data.length >> 2] |= 0x80 << (24 - (l & 31));

	// append 0 bits until length in bits % 512 == 448
	while ((bin.length & 15) != 14)
		bin.push(0);

	// append 64-bit source length
	bin.push(0);
	bin.push(l);

	// initial hash value
	h0 = 0x6a09e667;
	h1 = 0xbb67ae85;
	h2 = 0x3c6ef372;
	h3 = 0xa54ff53a;
	h4 = 0x510e527f;
	h5 = 0x9b05688c;
	h6 = 0x1f83d9ab;
	h7 = 0x5be0cd19;

	// update hash with each input block
	w = [];
	for (i = 0 ; i < bin.length ; i += 16) {
		a = h0;
		b = h1;
		c = h2;
		d = h3;
		e = h4;
		f = h5;
		g = h6;
		h = h7;

		for (j = 0 ; j < 64 ; ++j) {
			if (j < 16)
				w[j] = bin[j + i];
			else {
				T1 = w[j - 2];
				T2 = w[j - 15];

				w[j] =
						add(
							add(
								add(
									(rot(T1, 17) ^ rot(T1, 19) ^ (T1 >>> 10)),
									w[j - 7]
								),
								(rot(T2, 7) ^ rot(T2, 18) ^ (T2 >>> 3))
							),
							w[j - 16]
						);
			}

			T1 =
					add(
						add(
							add(
								add(
									h,
									(rot(e, 6) ^ rot(e, 11) ^ rot(e, 25))
								),
								((e & f) ^ ((~e) & g))
							),
							[
								0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
								0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
								0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
								0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
								0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
								0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
								0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
								0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
							][j]
						),
						w[j]
					);

			T2 =
					add(
						(rot(a, 2) ^ rot(a, 13) ^ rot(a, 22)),
						((a & b) ^ (a & c) ^ (b & c))
					);

			h = g;
			g = f;
			f = e;
			e = add(d, T1);
			d = c;
			c = b;
			b = a;
			a = add(T1, T2);
		}

		h0 = add(a, h0);
		h1 = add(b, h1);
		h2 = add(c, h2);
		h3 = add(d, h3);
		h4 = add(e, h4);
		h5 = add(f, h5);
		h6 = add(g, h6);
		h7 = add(h, h7);
	}

	if (returnBytes) {
		// convert to byte array
		bin = [];
		unpack(h0, bin);
		unpack(h1, bin);
		unpack(h2, bin);
		unpack(h3, bin);
		unpack(h4, bin);
		unpack(h5, bin);
		unpack(h6, bin);
		unpack(h7, bin);

		return bin;
	} else {
		// convert to string
		return dwordToHex(h0)
			  + dwordToHex(h1)
			  + dwordToHex(h2)
			  + dwordToHex(h3)
			  + dwordToHex(h4)
			  + dwordToHex(h5)
			  + dwordToHex(h6)
			  + dwordToHex(h7);
	}
}
window['hmac_sha256'] = hmac_sha256;
window['sha256'] = sha256;
/*
	// Test cases

	function testSha256(data, expected) {
		if (sha256(data) != expected)
			print("testSha256 failed for: " + data);
	}

	testSha256(
			"The quick brown fox jumps over the lazy dog",
			"d7a8fbb307d7809469ca9abcb0082e4f8d5651e46d3cdb762d02d0bf37c9e592"
	);

	testSha256(
			"The quick brown fox jumps over the lazy cog",
			"e4c4d8f3bf76b692de791a173e05321150f7a345b46484fe427f6acc7ecc81be"
	);

	testSha256(
			"",
			"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
	);

	function hexToByteArray(hex) {
		var	ary, i;

		ary = [];
		for (i = 2 ; i < hex.length ; i += 2)
			ary.push(parseInt(hex.substring(i, i + 2), 16));

		return ary;
	}

	function testHmacSha256(key, data, expected) {
		var	hash;

		if (key.match(/^0x/))
			key = hexToByteArray(key);

		if (data.match(/^0x/))
			data = hexToByteArray(data);

		hash = hmac_sha256(key, data);

		if (hash != expected)
			print("testHmacSha256 failed for: key=" + key + ", data=" + data);
	}

	testHmacSha256(
			"0x0102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f20",
			"abc",
			"a21b1f5d4cf4f73a4dd939750f7a066a7f98cc131cb16a6692759021cfab8181"
	);

	testHmacSha256(
			"0x0102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f20",
			"abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq",
			"104fdc1257328f08184ba73131c53caee698e36119421149ea8c712456697d30"
	);

	testHmacSha256(
			"0x0102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f20",
			"abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopqabcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq",
			"470305fc7e40fe34d3eeb3e773d95aab73acf0fd060447a5eb4595bf33a9d1a3"
	);

	testHmacSha256(
			"0x0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b0b",
			"Hi There",
			"198a607eb44bfbc69903a0f1cf2bbdc5ba0aa3f3d9ae3c1c7a3b1696a0b68cf7"
	);

	testHmacSha256(
			"Jefe",
			"what do ya want for nothing?",
			"5bdcc146bf60754e6a042426089575c75a003f089d2739839dec58b964ec3843"
	);

	testHmacSha256(
			"0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
			"0xdddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
			"cdcb1220d1ecccea91e53aba3092f962e549fe6ce9ed7fdc43191fbde45c30b0"
	);

	testHmacSha256(
			"0x0102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f202122232425",
			"0xcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcd",
			"d4633c17f6fb8d744c66dee0f8f074556ec4af55ef07998541468eb49bd2e917"
	);

	testHmacSha256(
			"0x0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c0c",
			"Test With Truncation",
			"7546af01841fc09b1ab9c3749a5f1c17d4f589668a587b2700a9c97c1193cf42"
	);

	testHmacSha256(
			"0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
			"Test Using Larger Than Block-Size Key - Hash Key First",
			"6953025ed96f0c09f80a96f78e6538dbe2e7b820e3dd970e7ddd39091b32352f"
	);

	testHmacSha256(
			"0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
			"Test Using Larger Than Block-Size Key and Larger Than One Block-Size Data",
			"6355ac22e890d0a3c8481a5ca4825bc884d3e7a1ff98a2fc2ac7d8e064c3b2e6"
	);

//*/
