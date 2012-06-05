TODO
====

Big Stuff
---------

 * Interact cells
 * Single-cell mode
 * Testing, testing, testing
 * Code completion
 * Sharing dialog
 * Data dialog
 * Use three.js instead of Jmol
 * Use WebSockets instead of async_request
   - use tornado web server
   - Wait until WebSockets are more fully supported. Browser support as of this writing is not sufficient to switch yet.

Medium Stuff
------------

 * Login page
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
 * Restart sage
 * Interrupt
 * Add grab image button to Jmol
 * Clean up LESS
 * Clean up javascript
   - maybe use prototypes
   - maybe separate the different cell types.. not sure if this is a good idea or not
   - incorporate some of the innovations used by IPython

Files
=====


Frontend
========

The frontend of the Sage Notebook is built on Twitter's Bootstrap framework, MathJax, LESS, TinyMCE, and CodeMirror. Content is loaded dynamically -- no more sending HTML back-and-forth between the server and the browser. All communication is done with JSON using the encode_response and decode_response functions.

CSS vs LESS vs SASS/SCSS
------------------------

Although plain CSS is more standard, CSS preprocessing is very similar and significantly speeds up development. The choice between LESS and SASS is tough. The Notebook is written in LESS for the time being primarily because the Bootstrap framework is built on LESS. I would certainly not be offended, however, if someone was interested in rewriting the stylesheet in SASS.