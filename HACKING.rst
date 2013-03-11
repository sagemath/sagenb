================================
Development of the Sage notebook
================================

Unlike most other parts of Sage (as of January 2013), development of
sagenb is done on a moving target, namely a git repository on GitHub.
Rather than making changes to the version of sagenb that came with your
copy of Sage, please first clone `the sagenb git repository`_ and
install it into your copy of Sage before you start coding. Details on
how to do this are as follows.

#.  Install `the latest development version of Sage`_ from sagemath.org.

#.  Sign up for an account at github.com, if you don't already have one,
    and log in; set up your SSH keys for authentication as directed by
    the instructions.

#.  Create your own fork of sagenb on the GitHub website. To do this, go
    to `the sagenb git repository`_ page and click on "Fork" in the
    upper right corner of the webpage.

#.  Clone your fork of sagenb to somewhere on your local disk, for
    example ``~/src/sagenb``::

        $ cd ~/src
        $ git clone git@github.com:<your username>/sagenb sagenb

#.  Where ``$SAGE_ROOT`` represents the base path of your Sage
    installation, perform the following commands::

        $ cd $SAGE_ROOT/devel
        $ rm sagenb
        $ ln -s ~/src/sagenb sagenb     # or wherever your clone is
        $ cd sagenb
        $ $SAGE_ROOT/sage --python setup.py develop

#.  You can also add the `sagenb`_ git repository as a remote branch
    called ``upstream``::

        $ git remote add upstream git@github.com:sagemath/sagenb
        $ git remote update upstream

    This will allow you to update your local repository as other
    people's changes are merged. Such an operation might look something
    like this::

        $ git remote update upstream    # learn what has changed
        $ git checkout master           # move to local master
        $ git merge upstream/master     # merge changes to local master

This completes the installation process. Now you can modify files in
your ``sagenb`` directory and submit your modifications to us using pull
requests on GitHub. (A full walkthrough of using git and GitHub are
beyond the scope of this file -- for more information see `the relevant
section in the Sage manual`_.)

If you ever need to switch to using another Sage installation for your
sagenb development, you only need to repeat step 5 with the new value of
``$SAGE_ROOT``.


.. _the sagenb git repository: http://github.com/sagemath/sagenb
.. _the latest development version of Sage: 
    http://sagemath.org/download-latest.html
.. _the relevant section in the Sage manual:
    http://sagemath.org/doc/developer/sagenb/index.html
