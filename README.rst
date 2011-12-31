.. This README does not explain how to handle installation into versions
   of Sage which do not yet ship the flask notebook, as the packaging of
   the notebook's dependencies is still in flux. Please see
   http://code.google.com/r/jasongrout-flask-sagenb/ for more
   information. # XXX 2011-12-22



This is the standalone Sage Notebook.

Most of the notebook does not depend on having Sage installed. Only
a few miscellaneous functions are imported from Sage. We welcome help in
making the notebook completely independent from Sage, or indeed, any
other help with the Sage notebook. Sage notebook development discussions
happen on the sage-notebook_ mailing list.

.. _sage-notebook: http://groups.google.com/group/sage-notebook



Installation
============

Install Sage, then do ``sage -python setup.py install`` in the current
directory. Then run the notebook from within Sage as follows::

    sage: import sagenb.notebook.notebook_object as nb
    sage: nb.notebook(directory="mynotebook")

This will create a directory ``mynotebook.sagenb``, and all notebook
data is stored in that directory.

SSL support
-----------

SSL is required for OpenID and accessing HTTPS from the Sage shell. Your
Sage install should usually support SSL out of the box, but if you
compiled it from source on a machine without the libssl headers, it may
not. You can check for SSL support by running ``import ssl`` in the Sage
console. If you get an error, then do the following.

1. Install the libssl headers on your system. On Debian-based systems,
   one way to do this is to run ``sudo apt-get install libssl-dev``.
2. Recompile Sage's internal Python interpreter by running ``sage -f
   python``.



Development
===========

Development of the sage notebook currently occurs on github using
the git revision control system.  However, since Sage ships with
Mercurial, a mercurial repository is provided in the spkg which
mirrors the git repository.

To update to the latest source, run the commands below.

.. warning:: This will discard any changes you have made to the files.

::

    cd $SAGE_ROOT/devel/sagenb
    hg pull git://github.com/sagemath/sagenb.git
    hg update

To switch to using git to manage the repository, do the following
after you have done the above.

.. warning:: This will discard any changes you have made to sage
   notebook files.

::

    git config --local core.bare false
    git reset --hard
    git remote add upstream git://github.com/sagemath/sagenb.git
    git pull upstream master
