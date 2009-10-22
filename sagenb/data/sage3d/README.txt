The sage3d ('java3d') viewer requires third-party libraries.  To use the viewer:

 * Download a build from https://java3d.dev.java.net/

 * Install in $SAGE_LOCAL/lib/python/site-packages/sagenb/data/sage3d/lib

 * Edit $SAGE_LOCAL/bin/sage3d

 * sage: var('A,B,C')
   sage: implicit_plot3d(sin(A)*cos(B) + sin(B)*cos(C) + sin(C)*cos(A), (A,-2*pi,2*pi), (B,-2*pi,2*pi), (C,-2*pi,2*pi), viewer='java3d')
