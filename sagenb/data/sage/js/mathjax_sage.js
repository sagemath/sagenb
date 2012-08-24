MathJax.Hub.Config({
    // Need jsMath2jax so that worksheets with div/span class "math" elements still render correctly
    // This is important for backwards compatibility (notably Rob Beezer's books)
    extensions: ["jsMath2jax.js"],
     tex2jax: {
        inlineMath: [['$','$'],['\\(','\\)']],
        processEscapes: true,
        // "cell_input_print" because those are input cells in published worksheets
        // "math" so that the tex2jax plugin leaves the spans/divs with class math alone
        // (since jsMath2jax will take care of it); if we don't, then tex2jax and jsMath2jax conflict.
        // See https://groups.google.com/forum/?fromgroups=#!topic/mathjax-users/qzWdxiQvNrw
        ignoreClass: 'cell_input_print|math'
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
