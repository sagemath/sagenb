=============================================
Installation of the Sage notebook from github
=============================================
The current development version of the Sage notebook is present in github.
Since this development version is not yet merged into the Sage
distribution, one needs to follow a couple of additional steps to have
a working development version of the Sage notebook.

Installation Steps
------------------
The steps one needs to follow are outlined below.

#. First install the latest development version of Sage from the
   `sagemath`_ website.
#. Next, follow the directions in `ticket 13121`_ to upgrade your notebook
   to version 0.10.1 (or the latest version).
#. Create a fork of the `sagenb`_ git repository on the github website. To
   create the fork, go to `sagenb`_ and click on "Fork" on the upper right
   corner of the webpage.
#. Clone your fork on to your local machine as follows. Note that the
   ``SAGE_ROOT`` variable below corresponds to the directory in which the
   Sage distribution is present, and ``username`` is your login name in
   github::

    $ cd SAGE_ROOT/devel
    $ git clone git@github.com:username/sagenb.git sagenb-github
    $ rm sagenb
    $ ln -s sagenb-github sagenb
    $ cd sagenb
    $ ../../sage --python setup.py develop

#. You can also add the `sagenb`_ git repository as a remote branch called
   ``upstream``::

    $ git remote add upstream git@github.com:sagemath/sagenb
    $ git fetch upstream

#. You are now all set to work with the development version of the Sage
   notebook!

.. _sagemath: http://sagemath.org/download-latest.html
.. _`ticket 13121`: http://trac.sagemath.org/sage_trac/ticket/13121
.. _sagenb: https://github.com/sagemath/sagenb
