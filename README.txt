This is the first release of the standalone Sage Notebook.

INSTALLATION:

Make sure to pull the latest changes!

sage -hg pull http://sage.math.washington.edu:8100
sage -hg update
sage -python setup.py install

QUICK: Install Sage, then type "sage -python setup.py install" in the
current directory.   This is safe and won't mess anything up.  Then run
the notebook by typing:

  sage: import sagenb.notebook.notebook_object as nb;  nb.notebook()

into sage.  This will create a directory called dotsage in the
directory from which you run the above two commands.  All notebook
data is stored in there.


MORE DETAILS:

   1. Make sure you have Python 2.6 installed with the following packages:

      * Jinja-1.2-py2.6-macosx-10.3-i386.egg
      * Pygments-1.1.1-py2.6.egg
      * Sphinx-0.5.1-py2.6.egg
      * Twisted-8.2.0-py2.6.egg-info + TwistedWeb2
      * docutils-0.5-py2.6.egg
      * zope.interface-3.3.0-py2.6.egg-info

   Note that pexpect is not required.  Note that twisted.web2 is.  The
   only easy way to get the above is probably just to start with a
   Sage install.

   2. In the current directory, type:
  
     python setup.py install

   to install the sagenb package.  This will install into the
   site-packages/sagenb directory of your Python install.  It is
   completely separate from Sage, and will run even if you don't have
   the Sage library installed.  


