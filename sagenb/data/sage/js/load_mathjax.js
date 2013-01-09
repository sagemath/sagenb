/* This script dynamically loads MathJax from either
 * the notebook server or the CDN
 */

(function() {
	var mathjax_config = "?config=TeX-AMS-MML_HTMLorMML";
	
	/* $.ajax and $.getScript don't work with the way MathJax
	 * picks up it's own url
	 */
	
	function doLoad(url) {
		document.write('<script type="text/javascript" src="' + url + '"><\/script>');
	}
	
	if(window.location.hostname.indexOf("localhost") > -1) {
		// we are running on localhost
		doLoad("/data/mathjax-MathJax-07669ac/MathJax.js" + mathjax_config);
	} else {
		// we aren't running localhost
		doLoad("http://cdn.mathjax.org/mathjax/latest/MathJax.js" + mathjax_config);
		if(typeof MathJax === undefined) {
			// CDN failed, load from notebook server
			doLoad("/data/mathjax-MathJax-07669ac/MathJax.js" + mathjax_config);
		}
	}
})();