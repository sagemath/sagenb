"""
The Sage Notebook

AUTHORS:

  - William Stein
"""

#############################################################################
#
#       Copyright (C) 2006-2009 William Stein <wstein@gmail.com>
#  Distributed under the terms of the GNU General Public License (GPL)
#  The full text of the GPL is available at:
#                  http://www.gnu.org/licenses/
#
#############################################################################

# For debugging sometimes it is handy to use only the reference implementation.
USE_REFERENCE_WORKSHEET_PROCESSES = False

# System libraries
import os
import random
import re
import shutil
import socket
import time
import bz2
import cPickle
from cgi import escape


# Sage libraries
from sagenb.misc.misc import (pad_zeros, cputime, tmp_dir, load, save,
                              ignore_nonexistent_files, unicode_str)

# Sage Notebook
import css          # style
import js           # javascript
import worksheet    # individual worksheets (which make up a notebook)
import config       # internal configuration stuff (currently, just keycodes)
import keyboards    # keyboard layouts
import server_conf  # server configuration
import user_conf    # user configuration
import user         # users
from   template import template, prettify_time_ago


try:
    # sage is installed
    import sage
    SYSTEMS = ['sage', 'gap', 'gp', 'jsmath', 'html', 'latex', 'maxima', 'python', 'r', 'sh', 'singular', 'axiom (optional)', 'kash (optional)', 'macaulay2 (optional)', 'magma (optional)', 'maple (optional)', 'mathematica (optional)', 'matlab (optional)', 'mupad (optional)', 'octave (optional)']
except ImportError:
    # sage is not installed
    SYSTEMS = ['sage']    # but gracefully degenerated version of sage mode, e.g., preparsing is trivial


# We also record the system names without (optional) since they are
# used in some of the html menus, etc.
SYSTEM_NAMES = [v.split()[0] for v in SYSTEMS]

JSMATH = True

JEDITABLE_TINYMCE  = True

DOC_TIMEOUT = 120

class Notebook(object):
    def __init__(self, dir):

        if isinstance(dir, basestring) and len(dir) > 0 and dir[-1] == "/":
            dir = dir[:-1]

        if not dir.endswith('.sagenb'):
            raise ValueError, "dir (=%s) must end with '.sagenb'"%dir

        self._dir = dir

        # For now we only support the FilesystemDatastore storage
        # backend.
        from sagenb.storage import FilesystemDatastore
        S = FilesystemDatastore(dir)
        self.__storage = S

        # Now set the configuration, loaded from the datastore.
        try:
            self.__conf = S.load_server_conf()
        except IOError:
            # Worksheet has never been saved before, so the server conf doesn't exist.
            self.__worksheets = {}

        # Set the list of users
        try:
            self.__users = S.load_users()
        except IOError:
            self.__users = {}

        # Set the list of worksheets
        W = {}
        for username in self.__users.keys():
            for w in S.worksheets(username):
                W['%s/%s'%(username, w.id_number())] = w

        self.__worksheets = W

    def delete(self):
        """
        Delete all files related to this notebook.

        This is used for doctesting mainly. This command is obviously
        *VERY* dangerous to use on a notebook you actually care about.
        You could easily lose all data.

        EXAMPLES::

            sage: tmp = tmp_dir() + '.sagenb'
            sage: nb = sagenb.notebook.notebook.Notebook(tmp)
            sage: sorted(os.listdir(tmp))
            ['home']
            sage: nb.delete()

        Now the directory is gone.::

            sage: os.listdir(tmp)
            Traceback (most recent call last):
            ...
            OSError: [Errno 2] No such file or directory: '...
        """
        self.__storage.delete()

    def systems(self):
        return SYSTEMS

    def system_names(self):
        return SYSTEM_NAMES

    ##########################################################
    # Users
    ##########################################################
    def create_default_users(self, passwd):
        """
        Create the default users for a notebook.

        INPUT:

        -  ``passwd`` - a string

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(tmp_dir()+'.sagenb')
            sage: nb.create_default_users('password')
            Creating default users.
            sage: list(sorted(nb.users().iteritems()))
            [('_sage_', _sage_), ('admin', admin), ('guest', guest), ('pub', pub)]
            sage: list(sorted(nb.passwords().iteritems()))
            [('_sage_', 'aaQSqAReePlq6'), ('admin', 'aajfMKNH1hTm2'), ('guest', 'aaQSqAReePlq6'), ('pub', 'aaQSqAReePlq6')]
            sage: nb.create_default_users('newpassword')
            Creating default users.
            WARNING: User 'pub' already exists -- and is now being replaced.
            WARNING: User '_sage_' already exists -- and is now being replaced.
            WARNING: User 'guest' already exists -- and is now being replaced.
            WARNING: User 'admin' already exists -- and is now being replaced.
            sage: list(sorted(nb.passwords().iteritems()))
            [('_sage_', 'aaQSqAReePlq6'), ('admin', 'aajH86zjeUSDY'), ('guest', 'aaQSqAReePlq6'), ('pub', 'aaQSqAReePlq6')]
        """
        print "Creating default users."
        self.add_user('pub', '', '', account_type='user', force=True)
        self.add_user('_sage_', '', '', account_type='user', force=True)
        self.add_user('guest', '', '', account_type='guest', force=True)
        self.add_user('admin', passwd, '', account_type='admin', force=True)

    def user_exists(self, username):
        """
        Return whether a user with the given ``username`` exists.

        INPUT:

        - ``username`` - a string

        OUTPUT:

        - a bool

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(tmp_dir()+'.sagenb')
            sage: nb.create_default_users('password')
            Creating default users.
            sage: nb.user_exists('admin')
            True
            sage: nb.user_exists('pub')
            True
            sage: nb.user_exists('mark')
            False
            sage: nb.user_exists('guest')
            True
        """
        return username in self.users()

    def users(self):
        """
        Return a dictionary of users in a notebook.

        OUTPUT:

        - a string:User instance dictionary

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(tmp_dir()+'.sagenb')
            sage: nb.create_default_users('password')
            Creating default users.
            sage: list(sorted(nb.users().iteritems()))
            [('_sage_', _sage_), ('admin', admin), ('guest', guest), ('pub', pub)]
        """
        try:
            return self.__users
        except AttributeError:
            self.__users = {}
            return self.__users

    def user(self, username):
        """
        Return an instance of the User class given the ``username`` of a user
        in a notebook.

        INPUT:

        - ``username`` - a string

        OUTPUT:

        - an instance of User

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(tmp_dir()+'.sagenb')
            sage: nb.create_default_users('password')
            Creating default users.
            sage: nb.user('admin')
            admin
            sage: nb.user('admin').get_email()
            ''
            sage: nb.user('admin').password()
            'aajfMKNH1hTm2'
        """
        if not isinstance(username, str) or '/' in username:
            raise KeyError, "no user '%s'"%username
        try:
            return self.users()[username]
        except KeyError:
            if username in ['pub', '_sage_']:
                self.add_user(username, '', '', account_type='user', force=True)
                return self.users()[username]
            elif username == 'admin':
                self.add_user(username, '', '', account_type='admin', force=True)
                return self.users()[username]
            elif username == 'guest':
                self.add_user('guest', '', '', account_type='guest', force=True)
                return self.users()[username]
            raise KeyError, "no user '%s'"%username

    def create_user_with_same_password(self, user, other_user):
        r"""
        Change the password of ``user`` to that of ``other_user``.

        INPUT:

        -  ``user`` - a string

        -  ``other_user`` - a string

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(tmp_dir()+'.sagenb')
            sage: nb.add_user('bob', 'an**d', 'bob@gmail.com', force=True)
            sage: nb.user('bob').password()
            'aa4Q6Jbx/MiUs'
            sage: nb.add_user('mary', 'ccd', 'mary@gmail.com', force=True)
            sage: nb.user('mary').password()
            'aaxr0gcWJMXKU'
            sage: nb.create_user_with_same_password('bob', 'mary')
            sage: nb.user('bob').password() == nb.user('mary').password()
            True
        """
        U = self.user(user)
        O = self.user(other_user)
        passwd = O.password()
        U.set_hashed_password(passwd)

    def user_is_admin(self, user):
        """
        Return True if ``user`` is an admin.

        INPUT:

        - ``user`` - an instance of User

        OUTPUT:

        - a bool

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(tmp_dir()+'.sagenb')
            sage: nb.add_user('Administrator', 'password', '', 'admin', True)
            sage: nb.add_user('RegularUser', 'password', '', 'user', True)
            sage: nb.user_is_admin('Administrator')
            True
            sage: nb.user_is_admin('RegularUser')
            False
        """
        return self.user(user).is_admin()

    def user_is_guest(self, username):
        """
        Return True if ``username`` is a guest.

        INPUT:

        - ``username`` - a string

        OUTPUT:

        - a bool

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(tmp_dir()+'.sagenb')
            sage: nb.create_default_users('password')
            Creating default users.
            sage: nb.user_is_guest('guest')
            True
            sage: nb.user_is_guest('admin')
            False
        """
        try:
            return self.user(username).is_guest()
        except KeyError:
            return False

    def user_list(self):
        """
        Return a list of user objects.

        OUTPUT:

        - a list of User instances

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(tmp_dir()+'.sagenb')
            sage: nb.create_default_users('password')
            Creating default users.
            sage: sorted(nb.user_list(), key=lambda k: k.username())
            [_sage_, admin, guest, pub]
        """
        return list(self.users().itervalues())

    def usernames(self):
        """
        Return a list of usernames.

        OUTPUT:

        - a list of strings

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(tmp_dir()+'.sagenb')
            sage: nb.create_default_users('password')
            Creating default users.
            sage: sorted(nb.usernames())
            ['_sage_', 'admin', 'guest', 'pub']
        """
        U = self.users()
        return U.keys()

    def valid_login_names(self):
        """
        Return a list of users that can log in.

        OUTPUT:

        - a list of strings

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(tmp_dir()+'.sagenb')
            sage: nb.create_default_users('password')
            Creating default users.
            sage: nb.valid_login_names()
            ['admin']
            sage: nb.add_user('Mark', 'password', '', force=True)
            sage: nb.add_user('Sarah', 'password', '', force=True)
            sage: nb.add_user('David', 'password', '', force=True)
            sage: sorted(nb.valid_login_names())
            ['David', 'Mark', 'Sarah', 'admin']
        """
        return [x for x in self.usernames() if not x in ['guest', '_sage_', 'pub']]

    def default_user(self):
        r"""
        Return a default login name that the user will see when
        confronted with the Sage notebook login page.  Currently, this
        returns 'admin' if that is the *only* user.  Otherwise it
        returns an empty string ('').

        OUTPUT:

        - a string - the default username.

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(tmp_dir()+'.sagenb')
            sage: nb.create_default_users('password')
            Creating default users.
            sage: nb.default_user()
            'admin'
            sage: nb.add_user('AnotherUser', 'password', '', force=True)
            sage: nb.default_user()
            ''
        """
        if self.valid_login_names() == ['admin']:
            return 'admin'
        else:
            return ''

    def set_accounts(self, value):
        r"""
        Set the accounts attribute of the server configuration to
        ``value``.  This property determines whether users can create
        new accounts.

        INPUT:

        - ``value`` - a bool

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(tmp_dir()+'.sagenb')
            sage: nb.get_accounts()
            False
            sage: nb.set_accounts(True)
            sage: nb.get_accounts()
            True
            sage: nb.set_accounts(False)
            sage: nb.get_accounts()
            False
        """
        self.conf()['accounts'] = bool(value)

    def get_accounts(self):
        r"""
        Return whether or not users can create new accounts.

        OUTPUT:

        - a bool

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(tmp_dir()+'.sagenb')
            sage: nb.get_accounts()
            False
            sage: nb.set_accounts(True)
            sage: nb.get_accounts()
            True
        """
        return self.conf()['accounts']

    def add_user(self, username, password, email, account_type="user", force=False):
        """
        Add a user with the given credentials.

        INPUT:

        -  ``username`` - the username

        -  ``password`` - the password

        -  ``email`` - the email address

        -  ``account_type`` - one of 'user', 'admin', or 'guest'

        -  ``force`` - a bool (default: False)

        If the method :meth:`get_accounts` returns False then user can
        only be added if ``force`` is True.

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(tmp_dir()+'.sagenb')
            sage: nb.add_user('Mark', 'password', '', force=True)
            sage: nb.user('Mark')
            Mark
            sage: nb.add_user('Sarah', 'password', ")
            Traceback (most recent call last):
            ValueError: creating new accounts disabled.
            sage: nb.set_accounts(True)
            sage: nb.add_user('Sarah', 'password', ")
            sage: nb.user('Sarah')
            Sarah
        """
        if not self.get_accounts() and not force:
            raise ValueError, "creating new accounts disabled."

        us = self.users()
        if us.has_key(username):
            print "WARNING: User '%s' already exists -- and is now being replaced."%username
        U = user.User(username, password, email, account_type)
        us[username] = U

        # Save the user database
        self.__storage.save_users(self.users())


    def change_password(self, username, password):
        """
        Change a user's password.

        INPUT:

        - ``username`` - a string, the username

        - ``password`` - a string, the user's new password

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(tmp_dir()+'.sagenb')
            sage: nb.add_user('Mark', 'password', '', force=True)
            sage: nb.user('Mark').password()
            'aajfMKNH1hTm2'
            sage: nb.change_password('Mark', 'different_password')
            sage: nb.user('Mark').password()
            'aaTlXok5npQME'
        """
        self.user(username).set_password(password)

    def del_user(self, username):
        """
        Delete the given user.

        INPUT:

        - ``username`` - a string

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(tmp_dir()+'.sagenb')
            sage: nb.add_user('Mark', 'password', '', force=True)
            sage: nb.user('Mark')
            Mark
            sage: nb.del_user('Mark')
            sage: nb.user('Mark')
            Traceback (most recent call last):
            KeyError: "no user 'Mark'"
        """
        us = self.users()
        if us.has_key(username):
            del us[username]

    def passwords(self):
        """
        Return a username:password dictionary.

        OUTPUT:

        - a string:string dictionary

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(tmp_dir()+'.sagenb')
            sage: nb.create_default_users('password')
            Creating default users.
            sage: nb.add_user('Mark', 'password', '', force=True)
            sage: list(sorted(nb.passwords().iteritems()))
            [('Mark', 'aajfMKNH1hTm2'), ('_sage_', 'aaQSqAReePlq6'), ('admin', 'aajfMKNH1hTm2'), ('guest', 'aaQSqAReePlq6'), ('pub', 'aaQSqAReePlq6')]
        """
        return dict([(user.username(), user.password()) for user in self.user_list()])

    def user_conf(self, username):
        """
        Return a user's configuration object.

        OUTPUT:

        - an instance of Configuration.

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(tmp_dir()+'.sagenb')
            sage: nb.create_default_users('password')
            Creating default users.
            sage: config = nb.user_conf('admin')
            sage: config['max_history_length']
            1000
            sage: config['default_system']
            'sage'
            sage: config['autosave_interval']
            3600
            sage: config['default_pretty_print']
            False
        """
        return self.users()[username].conf()

    ##########################################################
    # Publishing worksheets
    ##########################################################
    def _initialize_worksheet(self, src, W):
        r"""
        Initialize a new worksheet from a source worksheet.

        INPUT:

        - ``src`` - a Worksheet instance; the source

        - ``W`` - a new Worksheet instance; the target
        """
        # Copy over images and other files
        data = src.data_directory()
        if os.path.exists(data):
            target = os.path.join(W.directory(),'data')
            if os.path.exists(target):
                shutil.rmtree(target, ignore_errors=True)
            shutil.copytree(data, target, ignore=ignore_nonexistent_files)
        cells = src.cells_directory()
        if os.path.exists(cells):
            target = os.path.join(W.directory(),'cells')
            if os.path.exists(target):
                shutil.rmtree(target, ignore_errors=True)
            shutil.copytree(cells, target, ignore=ignore_nonexistent_files)
        W.edit_save(src.edit_text())
        W.save()

    def publish_worksheet(self, worksheet, username):
        r"""
        Publish a user's worksheet.  This creates a new worksheet in
        the 'pub' directory with the same contents as ``worksheet``.

        INPUT:

        - ``worksheet`` - an instance of Worksheet

        - ``username`` - a string

        OUTPUT:

        - a new or existing published instance of Worksheet

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.load_notebook(tmp_dir()+'.sagenb')
            sage: nb.add_user('Mark','password','',force=True)
            sage: W = nb.new_worksheet_with_title_from_text('First steps', owner='Mark')
            sage: nb.worksheet_names()
            ['Mark/0']
            sage: nb.publish_worksheet(nb.get_worksheet_with_filename('Mark/0'), 'Mark')
            pub/1: [Cell 1; in=, out=]
            sage: sorted(nb.worksheet_names())
            ['Mark/0', 'pub/1']
        """
        for X in self.__worksheets.itervalues():
            if X.is_published() and X.worksheet_that_was_published() == worksheet:
                # Update X based on worksheet instead of creating something new
                # 1. delete cells and data directories
                # 2. copy them over
                # 3. update worksheet text
                if os.path.exists(X.data_directory()):
                    shutil.rmtree(X.data_directory(), ignore_errors=True)
                if os.path.exists(X.cells_directory()):
                    shutil.rmtree(X.cells_directory(), ignore_errors=True)
                if os.path.exists(X.snapshot_directory()):
                    shutil.rmtree(X.snapshot_directory(), ignore_errors=True)
                self._initialize_worksheet(worksheet, X)
                X.set_worksheet_that_was_published(worksheet)
                X.move_to_archive(username)
                worksheet.set_published_version(X.filename())
                X.record_edit(username)
                X.set_name(worksheet.name())
                return X

        # Have to create a new worksheet
        W = self.create_new_worksheet(worksheet.name(), 'pub')
        self._initialize_worksheet(worksheet, W)
        W.set_worksheet_that_was_published(worksheet)
        W.move_to_archive(username)
        worksheet.set_published_version(W.filename())
        W.record_edit(username)
        return W

    ##########################################################
    # Moving, copying, creating, renaming, and listing worksheets
    ##########################################################

    def scratch_worksheet(self):
        try:
            return self.__scratch_worksheet
        except AttributeError:
            W = self.create_new_worksheet('scratch', '_sage_', add_to_list=False)
            self.__scratch_worksheet = W
            return W

    def create_new_worksheet(self, worksheet_name, username,
                             docbrowser=False, add_to_list=True):
        if username!='pub' and self.user_is_guest(username):
            raise ValueError, "guests cannot create new worksheets"

        W = self.worksheet(username)

        W.set_system(self.system(username))
        W.set_docbrowser(docbrowser)
        W.set_name(worksheet_name)

        if add_to_list:
            self.__worksheets[W.filename()] = W
        return W

    def copy_worksheet(self, ws, owner):
        W = self.create_new_worksheet('default', owner)
        self._initialize_worksheet(ws, W)
        name = "Copy of %s"%ws.name()
        W.set_name(name)
        return W

    def delete_worksheet(self, filename):
        """
        Delete the given worksheet and remove its name from the worksheet
        list.  Raise a KeyError, if it is missing.

        INPUT:

        - ``filename`` - a string
        """
        if not (filename in self.__worksheets.keys()):
            print self.__worksheets.keys()
            raise KeyError, "Attempt to delete missing worksheet '%s'"%filename
        W = self.__worksheets[filename]
        W.quit()
        shutil.rmtree(W.directory(), ignore_errors=True)
        self.deleted_worksheets()[filename] = W
        del self.__worksheets[filename]

    def deleted_worksheets(self):
        try:
            return self.__deleted_worksheets
        except AttributeError:
            self.__deleted_worksheets = {}
            return self.__deleted_worksheets

    def empty_trash(self, username):
        """
        Empty the trash for the given user.

        INPUT:

        -  ``username`` - a string

        This empties the trash for the given user and cleans up all files
        associated with the worksheets that are in the trash.

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(tmp_dir()+'.sagenb')
            sage: nb.add_user('sage','sage','sage@sagemath.org',force=True)
            sage: W = nb.new_worksheet_with_title_from_text('Sage', owner='sage')
            sage: W.move_to_trash('sage')
            sage: nb.worksheet_names()
            ['sage/0']
            sage: nb.empty_trash('sage')
            sage: nb.worksheet_names()
            []
        """
        X = self.get_worksheets_with_viewer(username)
        X = [W for W in X if W.is_trashed(username)]
        for W in X:
            W.delete_user(username)
            if W.owner() is None:
                self.delete_worksheet(W.filename())

    def worksheet_names(self):
        """
        Return a list of all the names of worksheets in this notebook.

        OUTPUT:

        - a list of strings.

        EXAMPLES:

        We make a new notebook with two users and two worksheets,
        then list their names::

            sage: nb = sagenb.notebook.notebook.Notebook(tmp_dir()+'.sagenb')
            sage: nb.add_user('sage','sage','sage@sagemath.org',force=True)
            sage: W = nb.new_worksheet_with_title_from_text('Sage', owner='sage')
            sage: nb.add_user('wstein','sage','wstein@sagemath.org',force=True)
            sage: W2 = nb.new_worksheet_with_title_from_text('Elliptic Curves', owner='wstein')
            sage: nb.worksheet_names()
            ['sage/0', 'wstein/1']
        """
        W = self.__worksheets.keys()
        W.sort()
        return W


    ##########################################################
    # Information about the pool of worksheet compute servers
    ##########################################################

    def server_pool(self):
        return self.conf()['server_pool']

    def set_server_pool(self, servers):
        self.conf()['server_pool'] = servers

    def get_ulimit(self):
        try:
            return self.__ulimit
        except AttributeError:
            self.__ulimit = ''
            return ''

    def set_ulimit(self, ulimit):
        self.__ulimit = ulimit

    def get_server(self):
        P = self.server_pool()
        if P is None or len(P) == 0:
            return None
        try:
            self.__server_number = (self.__server_number + 1)%len(P)
            i = self.__server_number
        except AttributeError:
            self.__server_number = 0
            i = 0
        return P[i]

    def new_worksheet_process(self):
        """
        Return a new worksheet process object with parameters determined by
        configuration of this notebook server.
        """
        from sagenb.interfaces import (WorksheetProcess_ExpectImplementation,
                                       WorksheetProcess_ReferenceImplementation,
                                       WorksheetProcess_RemoteExpectImplementation)

        if USE_REFERENCE_WORKSHEET_PROCESSES:
            return WorksheetProcess_ReferenceImplementation()

        ulimit = self.get_ulimit()
        from sagenb.interfaces import ProcessLimits
        # We have to parse the ulimit format to our ProcessLimits.
        # The typical format is.
        # '-u 400 -v 1000000 -t 3600'
        # Despite -t being cputime for ulimit, we map it to walltime,
        # since that is the only thing that really makes sense for a
        # notebook server.
        #    -u --> max_processes
        #    -v --> max_vmem (but we divide by 1000)
        #    -t -- > max_walltime

        max_vmem = max_cputime = max_walltime = None
        tbl = {'v':None, 'u':None, 't':None}
        for x in ulimit.split('-'):
            for k in tbl.keys():
                if x.startswith(k): tbl[k] = int(x.split()[1].strip())
        if tbl['v'] is not None:
            tbl['v'] = tbl['v']/1000.0


        process_limits = ProcessLimits(max_vmem=tbl['v'], max_walltime=tbl['t'],
                                       max_processes=tbl['u'])

        server_pool = self.server_pool()
        if not server_pool or len(server_pool) == 0:
            return WorksheetProcess_ExpectImplementation(process_limits=process_limits)
        else:
            import random
            user_at_host = random.choice(server_pool)
            python_command = os.path.join(os.environ['SAGE_ROOT'], 'sage -python')
            return WorksheetProcess_RemoteExpectImplementation(user_at_host=user_at_host,
                             process_limits=process_limits,
                             remote_python=python_command)


    def _python_command(self):
        """
        """
        try: return self.__python_command
        except AttributeError: pass



    ##########################################################
    # The default math software system for new worksheets for
    # a given user or the whole notebook (if username is None).
    ##########################################################

    def system(self, username=None):
        return self.user(username).conf()['default_system']

    ##########################################################
    # The default typeset setting for new worksheets for
    # a given user or the whole notebook (if username is None).
    ##########################################################

    # TODO -- only implemented for the notebook right now
    def pretty_print(self, username=None):
        return self.user(username).conf()['default_pretty_print']

    def set_pretty_print(self, pretty_print):
        self.__pretty_print = pretty_print

    ##########################################################
    # The default color scheme for the notebook.
    ##########################################################
    def color(self):
        try:
            return self.__color
        except AttributeError:
            self.__color = 'default'
            return self.__color

    def set_color(self,color):
        self.__color = color

    ##########################################################
    # The notebook history.
    ##########################################################
    def user_history(self, username):
        if not hasattr(self, '_user_history'):
            self._user_history = {}
        if self._user_history.has_key(username):
            return self._user_history[username]
        history = []
        for hunk in self.__storage.load_user_history(username):
            hunk = unicode_str(hunk)
            history.append(hunk)
        self._user_history[username] = history
        return history

    def create_new_worksheet_from_history(self, name, username, maxlen=None):
        W = self.create_new_worksheet(name, username)
        W.edit_save('Log Worksheet\n' + self.user_history_text(username, maxlen=None))
        return W

    def user_history_text(self, username, maxlen=None):
        history = self.user_history(username)
        if maxlen:
            history = history[-maxlen:]
        return '\n\n'.join([hunk.strip() for hunk in history])

    def add_to_user_history(self, entry, username):
        history = self.user_history(username)
        history.append(entry)
        maxlen = self.user_conf(username)['max_history_length']
        while len(history) > maxlen:
            del history[0]


    ##########################################################
    # Importing and exporting worksheets to files
    ##########################################################
    def export_worksheet(self, worksheet_filename, output_filename, title=None):
        """
        Export a worksheet, creating a sws file on the file system.

        INPUT:

            -  ``worksheet_filename`` - a string e.g., 'username/id_number'

            -  ``output_filename`` - a string, e.g., 'worksheet.sws'

            - ``title`` - title to use for the exported worksheet (if
               None, just use current title)
        """
        S = self.__storage
        W = self.get_worksheet_with_filename(worksheet_filename)
        S.save_worksheet(W)
        username = W.owner(); id_number = W.id_number()
        S.export_worksheet(username, id_number, output_filename, title=title)

    def worksheet(self, username, id_number=None):
        """
        Create a new worksheet with given id_number belonging to the
        user with given username, or return an already existing
        worksheet.  If id_number is None, creates a new worksheet
        using the next available new id_number for the given user.

        INPUT:

            - ``username`` -- string

            - ``id_number`` - nonnegative integer or None (default)
        """
        S = self.__storage
        if id_number is None:
            id_number = self.new_id_number(username)
        return S.load_worksheet(username, id_number)

    def new_id_number(self, username):
        """
        Find the next worksheet id for the given user.
        """
        u = self.user(username).conf()
        id_number = u['next_worksheet_id_number']
        if id_number == -1:  # need to initialize
            id_number = max([w.id_number() for w in self.worksheet_list_for_user(username)] + [-1]) + 1
        u['next_worksheet_id_number'] = id_number + 1
        return id_number

    def new_worksheet_with_title_from_text(self, text, owner):
        name, _ = worksheet.extract_name(text)
        W = self.create_new_worksheet(name, owner)
        return W

    def change_worksheet_key(self, old_key, new_key):
        ws = self.__worksheets
        W = ws[old_key]
        ws[new_key] = W
        del ws[old_key]

    def import_worksheet(self, filename, owner):
        r"""
        Import a worksheet with the given ``filename`` and set its
        ``owner``.  If the file extension is not txt or sws, raise a
        ValueError.

        INPUT:

        -  ``filename`` - a string

        -  ``owner`` - a string

        OUTPUT:

        -  ``worksheet`` - a newly created Worksheet instance

        EXAMPLES:

        We create a notebook and import a plain text worksheet
        into it.

        ::

            sage: nb = sagenb.notebook.notebook.Notebook(tmp_dir()+'.sagenb')
            sage: name = tmp_filename() + '.txt'
            sage: open(name,'w').write('foo\n{{{\n2+3\n}}}')
            sage: W = nb.import_worksheet(name, 'admin')

        W is our newly-created worksheet, with the 2+3 cell in it::

            sage: W.name()
            u'foo'
            sage: W.cell_list()
            [TextCell 0: foo, Cell 1; in=2+3, out=]
        """
        if not os.path.exists(filename):
            raise ValueError, "no file %s"%filename

        # Figure out the file extension
        ext = os.path.splitext(filename)[1]
        if ext.lower() == '.txt':
            # A plain text file with {{{'s that defines a worksheet (no graphics).
            W = self._import_worksheet_txt(filename, owner)
        elif ext.lower() == '.sws':
            # An sws file (really a tar.bz2) which defines a worksheet with graphics, etc.
            W = self._import_worksheet_sws(filename, owner)
        else:
            # We only support txt or sws files.
            raise ValueError, "unknown extension '%s'"%ext
        self.__worksheets[W.filename()] = W
        return W

    def _import_worksheet_txt(self, filename, owner):
        r"""
        Import a plain text file as a new worksheet.

        INPUT:

        -  ``filename`` - a string; a filename that ends in .txt

        -  ``owner`` - a string; the imported worksheet's owner

        OUTPUT:

        -  a new instance of Worksheet

        EXAMPLES:

        We write a plain text worksheet to a file and import it
        using this function.::

            sage: nb = sagenb.notebook.notebook.Notebook(tmp_dir()+'.sagenb')
            sage: name = tmp_filename() + '.txt'
            sage: open(name,'w').write('foo\n{{{\na = 10\n}}}')
            sage: W = nb._import_worksheet_txt(name, 'admin'); W
            admin/0: [TextCell 0: foo, Cell 1; in=a = 10, out=]
        """
        # Open the worksheet txt file and load it in.
        worksheet_txt = open(filename).read()
        # Create a new worksheet with the write title and owner.
        worksheet = self.new_worksheet_with_title_from_text(worksheet_txt, owner)
        # Set the new worksheet to have the contents specified by that file.
        worksheet.edit_save(worksheet_txt)
        return worksheet

    def _import_worksheet_sws(self, filename, username):
        r"""
        Import an sws format worksheet into this notebook as a new
        worksheet.

        INPUT:

        - ``filename`` - a string; a filename that ends in .sws;
           internally it must be a tar'd bz2'd file.

        - ``username`` - a string

        OUTPUT:

        - a new Worksheet instance

        EXAMPLES:

        We create a notebook, then make a worksheet from a plain text
        file first.::

            sage: nb = sagenb.notebook.notebook.load_notebook(tmp_dir()+'.sagenb')
            sage: name = tmp_filename() + '.txt'
            sage: open(name,'w').write('{{{id=0\n2+3\n}}}')
            sage: W = nb.import_worksheet(name, 'admin')
            sage: W.filename()
            'admin/0'

        We then export the worksheet to an sws file.::

            sage: sws = os.path.join(tmp_dir(), 'tmp.sws')
            sage: nb.export_worksheet(W.filename(), sws)

        Now we import the sws.::

            sage: W = nb._import_worksheet_sws(sws, 'admin')
            sage: nb._Notebook__worksheets[W.filename()] = W

        Yes, it's there now (as admin/2)::

            sage: nb.worksheet_names()
            ['admin/0', 'admin/1']
        """
        id_number = self.new_id_number(username)
        worksheet = self.__storage.import_worksheet(username, id_number, filename)

        # I'm not at all convinced this is a good idea, since we
        # support multiple worksheets with the same title very well
        # already.  So it's commented out.
        # self.change_worksheet_name_to_avoid_collision(worksheet)

        return worksheet

    def change_worksheet_name_to_avoid_collision(self, worksheet):
        """
        Change the display name of the worksheet if there is already a
        worksheet with the same name as this one.
        """
        name = worksheet.name()
        display_names = [w.name() for w in self.get_worksheets_with_owner(worksheet.owner())]
        if name in display_names:
            j = name.rfind('(')
            if j != -1:
                name = name[:j].rstrip()
            i = 2
            while name + " (%s)"%i in display_names:
                i += 1
            name = name + " (%s)"%i
            worksheet.set_name(name)


    ##########################################################
    # Server configuration
    ##########################################################
    def conf(self):
        try:
            return self.__conf
        except AttributeError:
            C = server_conf.ServerConfiguration()
            self.__conf = C
            return C

    ##########################################################
    # Computing control
    ##########################################################
    def set_not_computing(self):
        # unpickled, no worksheets will think they are
        # being computed, since they clearly aren't (since
        # the server just started).
        for W in self.__worksheets.values():
            W.set_not_computing()

    def quit(self):
        for W in self.__worksheets.itervalues():
            W.quit()

    def update_worksheet_processes(self):
        worksheet.update_worksheets()

    def quit_idle_worksheet_processes(self):
        timeout = self.conf()['idle_timeout']
        if timeout == 0:
            # Quit only the doc browser worksheets
            for W in self.__worksheets.itervalues():
                if W.docbrowser() and W.compute_process_has_been_started():
                    W.quit_if_idle(DOC_TIMEOUT)
            return

        for W in self.__worksheets.itervalues():
            if W.compute_process_has_been_started():
                W.quit_if_idle(timeout)


    ##########################################################
    # Worksheet HTML generation
    ##########################################################
    def worksheet_list_for_public(self, username, sort='last_edited', reverse=False, search=None):
        W = [x for x in self.__worksheets.itervalues() if x.is_published() and not x.is_trashed(user)]

        if search:
            W = [x for x in W if x.satisfies_search(search)]

        sort_worksheet_list(W, sort, reverse)  # changed W in place
        return W

    def worksheet_list_for_user(self, user, typ="active", sort='last_edited', reverse=False, search=None):
        X = self.get_worksheets_with_viewer(user)
        if typ == "trash":
            W = [x for x in X if x.is_trashed(user)]
        elif typ == "active":
            W = [x for x in X if x.is_active(user)]
        else: # typ must be archived
            W = [x for x in X if not (x.is_trashed(user) or x.is_active(user))]
        if search:
            W = [x for x in W if x.satisfies_search(search)]
        sort_worksheet_list(W, sort, reverse)  # changed W in place
        return W

    ##########################################################
    # Revision history for a worksheet
    ##########################################################
    def html_worksheet_revision_list(self, username, worksheet):
        r"""
        Return HTML for the revision list of a worksheet.

        INPUT:

        - ``username`` - a string

        - ``worksheet`` - an instance of Worksheet

        OUTPUT:

        - a string - the HTML for the revision list

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(tmp_dir()+'.sagenb')
            sage: W = nb.create_new_worksheet('Test', 'admin')
            sage: W.body()
            u'\n\n{{{id=1|\n\n///\n}}}'
            sage: W.save_snapshot('admin')
            sage: nb.html_worksheet_revision_list('admin', W)
            u'...Revision...Last Edited...ago...'
        """
        data = worksheet.snapshot_data()  # pairs ('how long ago', key)

        return template(os.path.join("html", "notebook", "worksheet_revision_list.html"),
                        data = data, worksheet = worksheet,
                        notebook = self,
                        username = username)


    def html_specific_revision(self, username, ws, rev):
        r"""
        Return the HTML for a specific revision of a worksheet.

        INPUT:

        - ``username`` - a string

        - ``ws`` - an instance of Worksheet

        - ``rev`` - a string containing the key of the revision

        OUTPUT:

        - a string - the revision rendered as HTML
        """
        t = time.time() - float(rev[:-4])
        time_ago = prettify_time_ago(t)

        filename = ws.get_snapshot_text_filename(rev)
        txt = bz2.decompress(open(filename).read())
        W = self.scratch_worksheet()
        W.delete_cells_directory()
        W.edit_save(txt)

        data = ws.snapshot_data()  # pairs ('how long ago', key)
        prev_rev = None
        next_rev = None
        for i in range(len(data)):
            if data[i][1] == rev:
                if i > 0:
                    prev_rev = data[i-1][1]
                if i < len(data)-1:
                    next_rev = data[i+1][1]
                break

        return template(os.path.join("html", "notebook", "specific_revision.html"),
                        worksheet = ws,
                        username = username, rev = rev, prev_rev = prev_rev,
                        next_rev = next_rev, time_ago = time_ago)

    def html_share(self, worksheet, username):
        r"""
        Return the HTML for the "share" page of a worksheet.

        INPUT:

        - ``username`` - a string

        - ``worksheet`` - an instance of Worksheet

        OUTPUT:

        - string - the share page's HTML representation

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(tmp_dir()+'.sagenb')
            sage: W = nb.create_new_worksheet('Test', 'admin')
            sage: nb.html_share(W, 'admin')
            u'...currently shared...add or remove collaborators...'
        """
        U = self.users()
        other_users = [x for x, u in U.iteritems() if not u.is_guest() and not u.username() in [username, 'pub', '_sage_']]
        other_users.sort(lambda x,y: cmp(x.lower(), y.lower()))

        return template(os.path.join("html", "notebook", "worksheet_share.html"),
                        worksheet = worksheet,
                        notebook = self,
                        username = username, other_users = other_users)
    
    def html_download_or_delete_datafile(self, ws, username, filename):
        r"""
        Return the HTML for the download or delete datafile page.

        INPUT:

        - ``username`` - a string

        - ``ws`` - an instance of Worksheet

        - ``filename`` - a string; the name of the file

        OUTPUT:

        - a string - the page rendered as HTML

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(tmp_dir()+'.sagenb')
            sage: W = nb.create_new_worksheet('Test', 'admin')
            sage: nb.html_download_or_delete_datafile(W, 'admin', 'bar')
            u'...Data file: bar...DATA is a special variable...uploaded...'
        """
        ext = os.path.splitext(filename)[1].lower()
        file_is_image, file_is_text = False, False
        text_file_content = ""

        if ext in ['.png', '.jpg', '.gif']:
            file_is_image = True
        if ext in ['.txt', '.tex', '.sage', '.spyx', '.py', '.f', '.f90', '.c']:
            file_is_text = True
            text_file_content = open(os.path.join(ws.data_directory(), filename)).read()

        return template(os.path.join("html", "notebook", "download_or_delete_datafile.html"),
                        worksheet = ws, notebook = self,
                        username = username,
                        filename_ = filename,
                        file_is_image = file_is_image,
                        file_is_text = file_is_text,
                        text_file_content = text_file_content)


    ##########################################################
    # Accessing all worksheets with certain properties.
    ##########################################################
    def active_worksheets_for(self, username):
        return [ws for ws in self.get_worksheets_with_viewer(username) if ws.is_active(username)]
    
    def get_all_worksheets(self):
        return [x for x in self.__worksheets.itervalues() if not x.owner() in ['_sage_', 'pub']]

    def get_worksheets_with_collaborator(self, user):
        if self.user_is_admin(user): return self.get_all_worksheets()
        return [w for w in self.__worksheets.itervalues() if w.is_collaborator(user)]

    def get_worksheet_names_with_collaborator(self, user):
        if self.user_is_admin(user): return [W.name() for W in self.get_all_worksheets()]
        return [W.name() for W in self.get_worksheets_with_collaborator(user)]

    def get_worksheets_with_viewer(self, user):
        if self.user_is_admin(user): return self.get_all_worksheets()
        return [w for w in self.__worksheets.itervalues() if w.is_viewer(user)]

    def get_worksheets_with_owner(self, owner):
        return [w for w in self.__worksheets.itervalues() if w.owner() == owner]

    def get_worksheets_with_owner_that_are_viewable_by_user(self, owner, user):
        return [w for w in self.get_worksheets_with_owner(owner) if w.is_viewer(user)]

    def get_worksheet_names_with_viewer(self, user):
        if self.user_is_admin(user): return [W.name() for W in self.get_all_worksheets()]
        return [W.name() for W in self.get_worksheets_with_viewer(user) if not W.docbrowser()]

    def get_worksheet_with_name(self, name):
        for W in self.__worksheets.itervalues():
            if W.name() == name:
                return W
        raise KeyError, "No worksheet with name '%s'"%name

    def get_worksheet_with_filename(self, filename):
        """
        Get the worksheet with the given filename.  If there is no
        such worksheet, raise a ``KeyError``.

        INPUT:

        - ``filename`` - a string

        OUTPUT:

        - a Worksheet instance
        """
        if self.__worksheets.has_key(filename):
            return self.__worksheets[filename]
        raise KeyError, "No worksheet with filename '%s'"%filename

    ###########################################################
    # Saving the whole notebook
    ###########################################################

    def save(self):
        """
        Save this notebook server to disk.
        """
        S = self.__storage
        S.save_users(self.users())
        S.save_server_conf(self.conf())
        # Save the non-doc-browser worksheets.
        for n, W in self.__worksheets.iteritems():
            if not n.startswith('doc_browser'):
                S.save_worksheet(W)
        if hasattr(self, '_user_history'):
            for username, H in self._user_history.iteritems():
                S.save_user_history(username, H)

    def save_worksheet(self, W, conf_only=False):
        self.__storage.save_worksheet(W, conf_only=conf_only)

    def delete_doc_browser_worksheets(self):
        names = self.worksheet_names()
        for n in self.__worksheets.keys():
            if n.startswith('doc_browser'):
                self.delete_worksheet(n)

    ###########################################################
    # HTML -- generate most html related to the whole notebook page
    ###########################################################
    def html_plain_text_window(self, worksheet, username):
        r"""
        Return HTML for the window that displays a plain text version
        of the worksheet.

        INPUT:

        -  ``worksheet`` - a Worksheet instance

        -  ``username`` - a string

        OUTPUT:

        - a string - the plain text window rendered as HTML

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(tmp_dir()+'.sagenb')
            sage: W = nb.create_new_worksheet('Test', 'admin')
            sage: nb.html_plain_text_window(W, 'admin')
            u'...pre class="plaintext"...cell_intext...textfield...'
        """
        plain_text = worksheet.plain_text(prompts=True, banner=False)
        plain_text = escape(plain_text).strip()

        return template(os.path.join("html", "notebook", "plain_text_window.html"),
                        worksheet = worksheet,
                        notebook = self,
                        username = username, plain_text = plain_text,
                        JSMATH = JSMATH, JEDITABLE_TINYMCE = JEDITABLE_TINYMCE)

    def html_edit_window(self, worksheet, username):
        r"""
        Return HTML for a window for editing ``worksheet``.

        INPUT:

        - ``username`` - a string containing the username

        - ``worksheet`` - a Worksheet instance

        OUTPUT:

        - a string - the editing window's HTML representation

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(tmp_dir()+'.sagenb')
            sage: W = nb.create_new_worksheet('Test', 'admin')
            sage: nb.html_edit_window(W, 'admin')
            u'...textarea class="plaintextedit"...{{{id=1|...//...}}}...'
        """

        return template(os.path.join("html", "notebook", "edit_window.html"),
                        worksheet = worksheet,
                        notebook = self,
                        username = username)

    def html_beforepublish_window(self, worksheet, username):
        r"""
        Return HTML for the warning and decision page displayed prior
        to publishing the given worksheet.

        INPUT:

        - ``worksheet`` - an instance of Worksheet

        - ``username`` - a string

        OUTPUT:

        - a string - the pre-publication page rendered as HTML

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(tmp_dir()+'.sagenb')
            sage: W = nb.create_new_worksheet('Test', 'admin')
            sage: nb.html_beforepublish_window(W, 'admin')
            u'...want to publish this worksheet?...re-publish when changes...'
        """
        msg = """You can publish your worksheet to the Internet, where anyone will be able to access and view it online.
        Your worksheet will be assigned a unique address (URL) that you can send to your friends and colleagues.<br/><br/>
        Do you want to publish this worksheet?<br/><br/>
        <form method="get" action=".">
        <input type="hidden" name="yes" value="" />
        <input type="submit" value="Yes" style="margin-left:10px" />
        <input type="button" value="No" style="margin-left:5px" onClick="parent.location=\'../'"><br/><br/>
        <input type="checkbox" name="auto" style="margin-left:13px" /> Automatically re-publish when changes are made
        </form>
        """
        return template(os.path.join("html", "notebook", "beforepublish_window.html"),
                        worksheet = worksheet,
                        notebook = self,
                        username = username)

    def html_afterpublish_window(self, worksheet, username, url, dtime):
        r"""
        Return HTML for a given worksheet's post-publication page.

        INPUT:

        - ``worksheet`` - an instance of Worksheet

        - ``username`` - a string

        - ``url`` - a string representing the URL of the published
          worksheet

        - ``dtime`` - an instance of time.struct_time representing the
          publishing time

        OUTPUT:

        - a string - the post-publication page rendered as HTML
        """
        from time import strftime
        time = strftime("%B %d, %Y %I:%M %p", dtime)

        return template(os.path.join("html", "notebook", "afterpublish_window.html"),
                        worksheet = worksheet,
                        notebook = self,
                        username = username, url = url, time = time)

    def html_upload_data_window(self, ws, username):
        r"""
        Return HTML for the "Upload Data" window.

        INPUT:

        - ``worksheet`` - an instance of Worksheet

        - ``username`` - a string

        OUTPUT:

        - a string - the HTML representation of the data upload window

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(tmp_dir()+'.sagenb')
            sage: W = nb.create_new_worksheet('Test', 'admin')
            sage: nb.html_upload_data_window(W, 'admin')
            u'...Upload or Create Data File...Browse...url...name of a new...'
        """
        return template(os.path.join("html", "notebook", "upload_data_window.html"),
                        worksheet = ws, username = username)

    def html(self, worksheet_filename=None, username='guest', show_debug=False,
             admin=False, do_print=False):
        r"""
        Return the HTML for a worksheet's index page.

        INPUT:

        - ``worksheet_filename`` - a string (default: None)

        - ``username`` - a string (default: 'guest')

        - ``show_debug`` - a bool (default: False)

        - ``admin`` - a bool (default: False)

        OUTPUT:

        - a string - the worksheet rendered as HTML

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(tmp_dir()+'.sagenb')
            sage: W = nb.create_new_worksheet('Test', 'admin')
            sage: nb.html(W.filename(), 'admin')
            u'...Test...cell_input...plainclick...state_number...'
        """
        if worksheet_filename is None or worksheet_filename == '':
            worksheet_filename = None
            W = None
        else:
            try:
                W = self.get_worksheet_with_filename(worksheet_filename)
            except KeyError:
                W = None

        template_page = os.path.join("html", "notebook", "worksheet_page.html")
        if W.docbrowser():
            template_page = os.path.join("html", "notebook", "doc_page.html")
        elif do_print:
            template_page = os.path.join('html', 'notebook', 'print_worksheet.html')
        elif W.is_published() or self.user_is_guest(username):
            template_page = os.path.join('html', 'notebook', 'guest_worksheet_page.html')

        return template(template_page, worksheet = W,
                        notebook = self, do_print=do_print,
                        username = username, show_debug = show_debug)

####################################################################

def load_notebook(dir, interface=None, port=None, secure=None):
    """
    Load and return a notebook from a given directory.  Create a new
    one in that directory, if one isn't already there.

    INPUT:

    -  ``dir`` - a string that defines a directory name

    -  ``interface`` - the address of the interface the server listens at

    -  ``port`` - the port the server listens on

    -  ``secure`` - whether the notebook is secure

    OUTPUT:

    - a Notebook instance
    """
    if not dir.endswith('.sagenb'):
        if not os.path.exists(dir + '.sagenb') and os.path.exists(os.path.join(dir, 'nb.sobj')):
            try:
                nb = migrate_old_notebook_v1(dir)
            except KeyboardInterrupt:
                raise KeyboardInterrupt, "Interrupted notebook migration.  Delete the directory '%s' and try again."%(os.path.abspath(dir+'.sagenb'))
            return nb
        dir += '.sagenb'

    dir = make_path_relative(dir)
    nb = Notebook(dir)
    nb.interface = interface
    nb.port = port
    nb.secure = secure

    # Install this copy of the notebook in twist.py as *the*
    # global notebook object used for computations.  This is
    # mainly to avoid circular references, etc.  This also means
    # only one notebook can actually be used at any point.
    import sagenb.notebook.twist
    sagenb.notebook.twist.notebook = nb

    return nb

def migrate_old_notebook_v1(dir):
    """
    Back up and migrates an old saved version of notebook to the new one (`sagenb`)
    """
    nb_sobj = os.path.join(dir, 'nb.sobj')
    old_nb = cPickle.loads(open(nb_sobj).read())

    ######################################################################
    # Tell user what is going on and make a backup
    ######################################################################

    print ""
    print "*"*80
    print "*"
    print "* The Sage notebook at"
    print "*"
    print "*      '%s'"%os.path.abspath(dir)
    print "*"
    print "* will be upgraded to a new format and stored in"
    print "*"
    print "*      '%s.sagenb'."%os.path.abspath(dir)
    print "*"
    print "* Your existing notebook will not be modified in any way."
    print "*"
    print "*"*80
    print ""
    ans = raw_input("Would like to continue? [YES or no] ").lower()
    if ans not in ['', 'y', 'yes']:
        raise RuntimeError, "User aborted upgrade."

    # Create new notebook
    new_nb = Notebook(dir+'.sagenb')

    # Define a function for transfering the attributes of one object to another.
    def transfer_attributes(old, new, attributes):
        for attr_old, attr_new in attributes:
            if hasattr(old, attr_old):
                setattr(new, attr_new,  getattr(old, attr_old))

    # Transfer all the notebook attributes to our new notebook object

    new_nb.conf().confs = old_nb.conf().confs
    for t in ['pretty_print', 'server_pool', 'ulimit', 'system']:
        if hasattr(old_nb, '_Notebook__' + t):
            new_nb.conf().confs[t] = getattr(old_nb, '_Notebook__' + t)

    # Now update the user data from the old notebook to the new one:
    print "Migrating %s user accounts..."%len(old_nb.users())
    users = new_nb.users()
    for username, old_user in old_nb.users().iteritems():
        new_user = user.User(old_user.username(), '',
                             old_user.get_email(), old_user.account_type())
        new_user.set_hashed_password(old_user.password())
        transfer_attributes(old_user, new_user,
                             [('_User__email_confirmed', '_email_confirmed'),
                             ('_User__temporary_password', '_temporary_password'),
                             ('_User__is_suspended', '_is_suspended')])
        # Fix the __conf field, which is also an instance of a class
        new_user.conf().confs = old_user.conf().confs
        users[new_user.username()] = new_user

    ######################################################################
    # Set the worksheets of the new notebook equal to the ones from
    # the old one.
    ######################################################################

    ######################################################################

    def migrate_old_worksheet(old_worksheet):
        """
        Migrates an old worksheet to the new format.
        """
        old_ws_dirname = old_ws._Worksheet__filename.partition(os.path.sep)[-1]
        new_ws = new_nb.worksheet(old_ws.owner(), old_ws_dirname)

        # some ugly creation of new attributes from what used to be stored
        tags = {}
        try:
            for user, val in old_ws._Worksheet__user_view.iteritems():
                if isinstance(user,str):
                    # There was a bug in the old notebook where sometimes the
                    # user was the *module* "user", so we don't include that
                    # invalid data.
                    tags[user] = [val]
        except AttributeError:
            pass
        import time
        last_change = (old_ws.last_to_edit(), old_ws.last_edited())
        try:
            published_id_number = int(os.path.split(old_ws._Worksheet__published_version)[1])
        except AttributeError:
            published_id_number = None

        ws_pub = old_ws.worksheet_that_was_published().filename().split('/')
        ws_pub = (ws_pub[0],int(ws_pub[1]))

        obj = {'name':old_ws.name(), 'system':old_ws.system(),
               'viewers':old_ws.viewers(), 'collaborators':old_ws.collaborators(),
               'pretty_print':old_ws.pretty_print(), 'ratings':old_ws.ratings(),
               'auto_publish':old_ws.is_auto_publish(), 'tags':tags,
               'last_change':last_change,
               'published_id_number':published_id_number,
               'worksheet_that_was_published':ws_pub
               }

        new_ws.reconstruct_from_basic(obj)

        base = os.path.join(dir, 'worksheets', old_ws.filename())
        worksheet_file = os.path.join(base, 'worksheet.txt')
        if os.path.exists(worksheet_file):
            text = open(worksheet_file).read()
            # delete first two lines -- we don't embed the title or
            # system in the worksheet text anymore.
            i = text.find('\n'); text=text[i+1:]
            i = text.find('\n'); text=text[i+1:]
            new_ws.edit_save(text)

        # copy over the DATA directory and cells directories
        try:
            dest = new_ws.data_directory()
            if os.path.exists(dest): shutil.rmtree(dest)
            shutil.copytree(old_ws.data_directory(), dest)
        except Exception, msg:
            print msg

        try:
            if os.path.exists(old_ws.cells_directory()):
                dest = new_ws.cells_directory()
                if os.path.exists(dest): shutil.rmtree(dest)
                shutil.copytree(old_ws.cells_directory(), dest)
        except Exception, msg:
            print msg


        return new_ws

    worksheets = {}
    num_worksheets = len(old_nb._Notebook__worksheets)
    print "Migrating (at most) %s worksheets..."%num_worksheets
    from sage.misc.misc import walltime
    tm = walltime()
    i = 0
    for ws_name, old_ws in old_nb._Notebook__worksheets.iteritems():
        if old_ws.is_doc_worksheet(): continue
        i += 1
        if i%25==0:
            percent = i/float(num_worksheets)
            # total_time * percent = time_so_far, so
            # remaining_time = total_time - time_so_far = time_so_far*(1/percent - 1)
            print "    Migrated %s (of %s) worksheets (about %.0f seconds remaining)"%(
                i, num_worksheets, walltime(tm)*(1/percent-1))
        new_ws = migrate_old_worksheet(old_ws)
        worksheets[new_ws.filename()] = new_ws
    new_nb._Notebook__worksheets = worksheets

    # Migrating history
    new_nb._user_history = {}
    for username in old_nb.users().keys():
        history_file = os.path.join(dir, 'worksheets', username, 'history.sobj')
        if os.path.exists(history_file):
            new_nb._user_history[username] = cPickle.loads(open(history_file).read())

    # Save our newly migrated notebook to disk
    new_nb.save()

    print "Worksheet migration completed."
    return new_nb

def make_path_relative(dir):
    r"""
    Replace an absolute path with a relative path, if possible.
    Otherwise, return the given path.

    INPUT:

    - ``dir`` - a string containing, e.g., a directory name

    OUTPUT:

    - a string
    """
    base, file = os.path.split(dir)
    if os.path.exists(file):
        return file
    return dir

##########################################################
# Misc
##########################################################


def sort_worksheet_list(v, sort, reverse):
    """
    Sort a given list on a given key, in a given order.

    INPUT:

    - ``sort`` - a string; 'last_edited', 'owner', 'rating', or 'name'

    - ``reverse`` - a bool; if True, reverse the order of the sort.

    OUTPUT:

    - the sorted list
    """
    f = None
    if sort == 'last_edited':
        def c(a, b):
            return -cmp(a.last_edited(), b.last_edited())
        f = c
    elif sort == 'name':
        def c(a,b):
            return cmp((a.name().lower(), -a.last_edited()), (b.name().lower(), -b.last_edited()))
        f = c
    elif sort == 'owner':
        def c(a,b):
            return cmp((a.owner().lower(), -a.last_edited()), (b.owner().lower(), -b.last_edited()))
        f = c
    elif sort == "rating":
        def c(a,b):
            return -cmp((a.rating(), -a.last_edited()), (b.rating(), -b.last_edited()))
        f = c
    else:
        raise ValueError, "invalid sort key '%s'"%sort
    v.sort(cmp = f, reverse=reverse)
