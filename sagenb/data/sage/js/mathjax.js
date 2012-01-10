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

// Remove http when standalone mathJax
MathJax.Ajax.loadComplete("http://localhost:8000/javascript/sage/mathjax.js");
