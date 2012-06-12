MathJax.Hub.Config({
    tex2jax: {
	inlineMath: [['$','$'],['\\(','\\)']],
	processEscapes: true,
	ignoreClass: 'cell_input_print', // "input cells" in published worksheets
    },

    styles: {
	".MathJax .mo, .MathJax .mi": {
	    color: "inherit ! important"
	}
    },

    MathMenu: {showFontMenu: true},

    "HTML-CSS": {
	imageFont: null,
	availableFonts: ["TeX"]
    },

    TeX: {
	Macros: {
	    {{ theme_mathjax_macros|join(',\n') }}
	}
    },

});

// This path is a little funny because we have to load our local
// config file as '../../dynamic/mathjax_sage' when we load MathJax
MathJax.Ajax.loadComplete("[MathJax]/config/../../dynamic/mathjax_sage.js")
