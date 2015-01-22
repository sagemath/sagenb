.. nodoctest

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

SSL is required for OpenID and HTTPS support in the notebook. OpenID
only requires Python's built-in SSL support, whereas HTTPS support also
requires the Python library pyOpenSSL. In order to ensure that these are
installed, please follow the instructions in Sage's own README file
(look for the section about SSL). If you don't intend to use OpenID for
user logins, or HTTPS for connecting to the server, you can safely
ignore this section. In particular, if you're installing a copy of Sage
for your personal use only, you probably won't need OpenID or HTTPS
support in the notebook.

LDAP authentication
-------------------

HTTPS support in the Python library is required to download and install
files, in order to install LDAP authentication support. To enable HTTPS
support read the section on SSL in Sage's own README file. Enabling LDAP
authentication also requires one to install the LDAP development headers.
You can install the LDAP development headers to your system by using your
package manager. For instance, on a Debian/Ubuntu Linux system you may
install LDAP and SSL by running the following command::

    $ sudo apt-get install libldap2-dev libsasl2-dev libssl-dev

Next, use the following commands to install the python-ldap package in
Sage::

    $ /path/to/sage -sh
    $ easy_install python-ldap

Once python-ldap is installed, (re)start the notebook server and the
options to setup LDAP authentication will be visible in the "Notebook
Settings" section of the "Settings."


Development
===========

Development and issue tracking of sagenb happens primarily on
Github at https://github.com/sagemath/sagenb, with certain
discussions at the sage-notebook Google group
https://groups.google.com/forum/#!forum/sage-notebook.

Instructions for getting started with sagenb development
are found in the file ``HACKING.rst``, including how to link
a local clone of the source to an existing Sage installation.

See the Sage Developer's guide, part of the Sage documentation, at
http://www.sagemath.org/doc/developer/index.html for some further
instructions.  There is also a useful, if somewhat outdated, overview
of the directory structure, evaluation and serving flow at
http://wiki.sagemath.org/devel/SageNotebook


Stylesheets (CSS)
-----------------
See ``sass/readme.txt`` for information about how to
use sagenb's SCSS files to update its CSS *properly*.


Localization
------------

The Sage notebook has various localizations available, and
welcomes updates to those as well as new ones.  The current
localizations are available in ``sagenb/translations``.

The file ``util/translations.py`` encapsulates much of the
Python Babel localization utility in an easy-to-use
interface meant for the Sage notebook.  We recommend its
use to update and create new translations.  Full help
is available by running the file in the Sage Python
shell with the ``-h`` argument::

    cd $SAGENB_ROOT
    sage -python ./util/translations.py -h

A more advanced introduction is in preparation.

Release Instructions
--------------------

Currently, sagenb is an upstream project from Sage proper.
That means any new sagenb release needs to be packaged properly
in order to be included in Sage.

Read ``ReleaseInstr.md`` for step-by-step details on how
to create such a release, including minor changes
needed on the Sage side to ``build/pkgs/sagenb/package-version.txt``
and the checksum file.
