MathJax.Hub.Config({
  tex2jax: {
    inlineMath: [['$','$'],['\\(','\\)']],
    processEscapes: true
  },
  extensions: ["jsMath2jax.js"],
  TeX: {
    Macros: {
      {{ theme_mathjax_macros }}
    }
  }
});

MathJax.Ajax.loadComplete("/javascript/sage/mathjax.js");
