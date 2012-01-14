MathJax.Hub.Config({
  imageFont: null,
  tex2jax: {
    inlineMath: [['$','$'],['\\(','\\)']],
    processEscapes: true,
  },
  styles: {
    ".MathJax .mo, .MathJax .mi": {
      color: "inherit ! important"
    }
  },
  TeX: {
    Macros: {
     {{ theme_mathjax_macros|join(',\n') }}
    }
  },
  MathMenu: {
    showFontMenu: true
  }
});

// This path is a little funny because we have to load our local
// config file as '../../dynamic/mathjax_sage' when we load MathJax
MathJax.Ajax.loadComplete("[MathJax]/config/../../dynamic/mathjax_sage.js")
