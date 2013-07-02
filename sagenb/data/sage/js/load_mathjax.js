/* This script dynamically loads MathJax from either
 * the notebook server or the CDN
 * 
 * $.ajax and $.getScript don't work with the way MathJax
 * picks up it's own url
 */

(function() {
	var mathjax_config = "?config=TeX-AMS-MML_HTMLorMML";

	var mathjax_url;
	if(window.location.hostname.indexOf("localhost") > -1) {
		mathjax_url = "/data/mathjax-MathJax-07669ac/MathJax.js";
	} else {
		mathjax_url = "http://cdn.mathjax.org/mathjax/latest/MathJax.js";
	}
	
	var head = document.getElementsByTagName("head")[0];
	var config_script = document.createElement("script");
	config_script.type = "text/x-mathjax-config";
	config_script[(window.opera ? "innerHTML" : "text")] =
		"MathJax.Hub.Config({\n" +
		"  tex2jax: { inlineMath: [['$','$'], ['\\\\(','\\\\)']] }\n" +
		"});";
	head.appendChild(config_script);

	var script = document.createElement("script");
	script.type = "text/javascript";
	script.src  = mathjax_url + mathjax_config;
	head.appendChild(script);
})();