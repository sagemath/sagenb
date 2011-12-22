This is the standalone Sage Notebook.

Most of the notebook does not depend on having Sage installed. Only
a few miscellaneous functions are imported from Sage. We welcome help in
making the notebook completely independent from Sage, or indeed, any
other help in the Sage notebook. Sage notebook development discussions
happen on the sage-notebook_ mailing list.

.. _sage-notebook: http://groups.google.com/group/sage-notebook



Installation
------------

Install Sage, then do ``sage -python setup.py install`` in the current
directory. Then run the notebook from within Sage as follows::

    sage: import sagenb.notebook.notebook_object as nb
    sage: nb.notebook(directory="mynotebook")

This will create a directory mynotebook.sagenb, and all notebook data is
stored in that directory.
