TODO
====

Big Stuff
---------

 * Interact cells
 * Single-cell mode
     - Create hash tag routes (...#cell15, etc) so that someone can reference a single cell in a presentation with a url
 * Testing, testing, testing
 * Code completion
 * Sharing dialog
 * Data dialog
 * Use three.js or something else instead of Jmol
 * Use sockets.io instead of async_request
     - use TornadIO2 https://github.com/MrJoes/tornadio2
 * Add option to store the notebook in a database instead of filesystem.
     - figure out which database systems to support

Medium Stuff
------------

 * Login page
 * Import worksheet dialog/page
 * Help page
 * Log dialog
 * automatic minify on .js and .css files
     - Add a route in base.py or somewhere else
     - Make sure it's disabled in debug mode
 * Create automatic print-friendly option
 * Template the different html files. For example create a base template which worksheet.html and the worksheet listing page extend.

Small Stuff
-----------

 * Logout
 * Report a problem dialog
 * Evaluate all cells
 * Change worksheet system dialog
 * Restart sage
 * Interrupt
 * Add grab image button to Jmol
 * Clean up LESS
 * Clean up javascript
     - maybe use prototypes
     - maybe separate the different cell types.. not sure if this is a good idea or not
     - incorporate some of the innovations used by IPython
 * Clean up base.py and worksheet.py in flask_version/

Files
=====


Frontend
========

The frontend of the Sage Notebook is built on Twitter's Bootstrap framework, MathJax, LESS, TinyMCE, and CodeMirror. Content is loaded dynamically -- no more sending HTML back-and-forth between the server and the browser. All communication is done with JSON using the encode_response and decode_response functions.

CSS vs LESS vs SASS/SCSS
------------------------

Although plain CSS is more standard, CSS preprocessing is very similar and significantly speeds up development. The choice between LESS and SASS is tough. The Notebook is written in LESS for the time being primarily because the Bootstrap framework is built on LESS. I would certainly not be offended, however, if someone was interested in rewriting the stylesheet in SASS.

Backend
=======

I'm not completely familiar with all of the backend structure. If someone would be interested helping write this, please do.