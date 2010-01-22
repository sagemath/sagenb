SAGE GRAPH EDITOR

AUTHORS:

 - Radoslav Kirov
 - Mitesh Patel

The following files in this directory are needed to run the graph
editor:

    a. sage/graphs/graph_editor.py
    b. graph_editor.html
    c. graph_editor.js
    d. processing.editor.min.js

What do they do?  Evaluating graph_editor(G) in an input cell
generates the code/markup for an inline frame, which the notebook
inserts into the corresponding output cell. The iframe loads (b) as
its content. In turn, (b) draws in jQuery / UI, the layout algorithms
in (c), and the HTML5 canvas rendering engine in (d).

Here's how the server and editor communicate with each other:

Server -> Editor:

    The Python function graph_to_js() in (a) makes a string
    representation of the relevant graph data (currently, adjacency
    lists and vertex coordinates) and puts it in a hidden HTML input
    element.  This element goes into the relevant cell's output.

    How does the editor find the data?  The function just adds the
    cell ID to the editor's URL, e.g.,
    [...]/graph_editor.html?cell_id=7.  When the iframe loads, the
    setup code in graph_editor.js extracts the ID, gets the data, and
    creates a visual representation of the graph.  Processing.js
    supplies the graphics and dynamic primitives, i.e., for drawing
    circles and lines, controlling animation, etc.
    
Editor -> Server:

    When the user clicks "Save", the notebook gets the latest graph
    data, formats it for the Sage library's graph methods (e.g., the
    Graph constructor and Graph.set_pos), optionally replaces the
    cell's input (see the replace_input option in (a)), and evaluates
    the cell.

File (d) is slightly modified version of the JS library Processing.JS
(http://processingjs.org/).  The only change is that mouse events are
attached to the whole document, rather than to the current element.

        attach(curElement,"mousemove",function(e)... 
        ----> attach(document,"mousemove",function(e)...

This makes it possible to drag vertices outside the canvas for the
erasing maneuver.

For reference, the original Processing.JS library and its minified
source files are also included here:

    e. processing.js
    f. processing.min.js

There's also an un-minified (http://jsbeautifier.org/) version of
processing.editor.min.js:

    g. processing.editor.js

Possibilities for the future:

 * Improved or alternate layout algorithms.  The function
   Edge.prototype.shrink., in graph_editor.js, runs the current spring
   model.

 * Directed graphs!  We could use Bezier curves here.
 
 * Edge and vertex colors.

 * Edge and vertex labels.

 * Use JSON for the graph data.  This is much safer than eval.  It
   would also help if it were possible to construct Graphs directly
   from stringified JSON objects.

Have fun!
