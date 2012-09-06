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

If you are interested in developing the Sage Notebook, run 
``sage -python setup.py develop`` instead of ``sage -python setup.py install``

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



Development
===========

See the Sage Developer's guide, part of the Sage documentation, for
instructions. Also see https://github.com/samuela/sagenb/wiki/Development-Notes.

Miscellaneous Release Instructions
----------------------------------

The following advice for release managers of sagenb is taken from the
old SPKG.txt file that was sitting around. Most of it is probably
outdated, but here it is anyway. It is modified slightly to cause it to
make sense in some cases.

    To cut a new release of sagenb, make sure that:

    * All changes are committed.

    * ``.gitignore`` and ``MANIFEST.in`` are current.

    * The notebook runs.

    * The doctests pass: ``sage -t --sagenb``

    * The notebook will be possible to install from the new SPKG without
      an internet connection.

      * Any dependencies that must be downloaded can be added in
        ``util/fetch_deps.py`` and inserted in ``setup.py``.
        Dependencies of dependencies need not be put in ``setup.py``,
        but need to be put in ``util/fetch_deps.py`` (until we can make
        it smarter).

    * The Selenium tests pass (optional, for now).

    * The localization file ``sagenb.pot`` is up-to-date.

      * Run ``pybabel extract -F /path/to/babel.cfg /path/to/project -o
        /path/to/sagenb.po`` (get pybabel with ``easy_install
        pybabel``).

      * Copy the headers from the existing ``sagenb.pot``.

      * Replace ``sagenb.pot`` with ``sagenb.po``.

      * Then, update the version in ``setup.py`` and commit this change.

      * Run ``dist.sh``, optionally with a ``-g`` argument to package
        the git repo too.

      * Copy the newly generated ``dist/`` directory from the sagenb
        repo to the SPKG's root directory and rename it ``src/``
        , replacing the ``src/`` directory that is currently there

      * Pack up the SPKG with ``sage --pkg --no-compress`` (because
        everything in ``src/`` is already compressed)

      * Install and test the new spkg: ``sage -f sagenb-*.spkg``

      * Don't forget to push all changes in the sagenb repo to github.

    Stylesheets (CSS): see ``sass/readme.txt``.

    To add a locale to an existing install:

    * Create a new locale, or download one from
      http://wiki.sagemath.org/i18n . To create a new locale:

      * Edit and save a copy of ``sagenb.pot`` using your favorite text
        editor or POEdit (http://poedit.net)

      * (Recommended) Post the new locale to
        http://wiki.sagemath.org/i18n

    * Compile your copy via ``msgfmt sagenb.pot -o sagenb.mo``

    * Copy ``sagenb.mo`` to ``sagenb/locale/xx_YY/LC_MESSAGES/``, where
      xx_YY is a locale code (en_US, pt_BR, en_UK, etc.)
