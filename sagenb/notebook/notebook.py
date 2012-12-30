# -*- coding: utf-8 -*
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
from . import worksheet    # individual worksheets (which make up a notebook)
from . import server_conf  # server configuration
from . import user_conf    # user configuration
from . import user         # users
from   template import template, prettify_time_ago
from flaskext.babel import gettext, lazy_gettext

try:
    # sage is installed
    import sage
    # [(string: name, bool: optional)]
    SYSTEMS = [('sage', False),
               ('gap', False),
               ('gp', False),
               ('html', False),
               ('latex', False),
               ('maxima', False),
               ('python', False),
               ('r', False),
               ('sh', False),
               ('singular', False),
               ('axiom', True),
               ('fricas', True),
               ('kash', True),
               ('macaulay2', True),
               ('magma', True),
               ('maple', True,),
               ('mathematica', True),
               ('matlab', True),
               ('mupad', True),
               ('octave', True),
               ('scilab', True)]
except ImportError:
    # sage is not installed
    SYSTEMS = [('sage', True)]    # but gracefully degenerated version of sage mode, e.g., preparsing is trivial


# We also record the system names without (optional) since they are
# used in some of the html menus, etc.
SYSTEM_NAMES = [v[0] for v in SYSTEMS]

MATHJAX = True

JEDITABLE_TINYMCE  = True

class WorksheetDict(dict):
    def __init__(self, notebook, *args, **kwds):
        self.notebook = notebook
        self.storage = notebook._Notebook__storage
        dict.__init__(self, *args, **kwds)

    def __getitem__(self, item):
        if item in self:
            return dict.__getitem__(self, item)

        try:
            if '/' not in item:
                raise KeyError, item
        except TypeError:
            raise KeyError, item

        username, id = item.split('/')
        try:
            id=int(id)
        except ValueError:
            raise KeyError, item
        try:
            worksheet = self.storage.load_worksheet(username, id)
        except ValueError:
            raise KeyError, item

        dict.__setitem__(self, item, worksheet)
        return worksheet
        
        
class Notebook(object):
    HISTORY_MAX_OUTPUT = 92*5
    HISTORY_NCOLS = 90
    
    def __init__(self, dir, user_manager = None):

        if isinstance(dir, basestring) and len(dir) > 0 and dir[-1] == "/":
            dir = dir[:-1]

        if not dir.endswith('.sagenb'):
            raise ValueError("dir (=%s) must end with '.sagenb'" % dir)

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
            self.__worksheets = WorksheetDict(self)

        from user_manager import SimpleUserManager, OpenIDUserManager
        self._user_manager = OpenIDUserManager(conf=self.conf()) if user_manager is None else user_manager

        # Set the list of users
        try:
            S.load_users(self._user_manager)
        except IOError:
            pass

        # Set the list of worksheets
        W = WorksheetDict(self)
        self.__worksheets = W

        # datastore
        # Store / Refresh public worksheets
        for id_number in os.listdir(self.__storage._abspath(self.__storage._user_path("pub"))):
            if id_number.isdigit():
                a = "pub/" + str(id_number)
                if a not in self.__worksheets:
                    try:
                        self.__worksheets[a] = self.__storage.load_worksheet("pub", int(id_number))
                    except Exception:
                        import traceback
                        print "Warning: problem loading %s/%s: %s"%("pub", int(id_number), traceback.format_exc())

        # Set the openid-user dict
        try:
            self._user_manager.load(S)
        except IOError:
            pass

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

    def systems(self, username=None):
        systems = []
        for system in SYSTEMS:
            if system[1]:
                systems.append(system[0] + ' (' + lazy_gettext('optional') + ')')
            else:
                systems.append(system[0])
        return systems

    def system_names(self):
        return SYSTEM_NAMES

    def user_manager(self):
        """
        Returns self's UserManager object.

        EXAMPLES::

            sage: n = sagenb.notebook.notebook.Notebook(tmp_dir()+'.sagenb')
            sage: n.user_manager() 
            <sagenb.notebook.user_manager.OpenIDUserManager object at 0x...>
        """
        return self._user_manager
        
    ##########################################################
    # Users
    ##########################################################
    def create_default_users(self, passwd):
        """
        Create the default users for a notebook.

        INPUT:

        - ``passwd`` - a string

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(tmp_dir()+'.sagenb')
            sage: nb.create_default_users('password')
            sage: list(sorted(nb.user_manager().users().iteritems()))
            [('_sage_', _sage_), ('admin', admin), ('guest', guest), ('pub', pub)]
            sage: list(sorted(nb.user_manager().passwords().iteritems())) #random
            [('_sage_', ''), ('admin', ''), ('guest', ''), ('pub', '')]
            sage: nb.create_default_users('newpassword')
            WARNING: User 'pub' already exists -- and is now being replaced.
            WARNING: User '_sage_' already exists -- and is now being replaced.
            WARNING: User 'guest' already exists -- and is now being replaced.
            WARNING: User 'admin' already exists -- and is now being replaced.
            sage: list(sorted(nb.user_manager().passwords().iteritems())) #random
            [('_sage_', ''), ('admin', ''), ('guest', ''), ('pub', '')]
            sage: len(list(sorted(nb.user_manager().passwords().iteritems())))
            4
        """
        self.user_manager().create_default_users(passwd)

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
            sage: nb.user_manager().create_default_users('password')
            sage: nb.user('admin')
            admin
            sage: nb.user('admin').get_email()
            ''
            sage: nb.user('admin').password() #random
            '256$7998210096323979f76e9fedaf1f85bda1561c479ae732f9c1f1abab1291b0b9$373f16b9d5fab80b9a9012af26a6b2d52d92b6d4b64c1836562cbd4264a6e704'
        """
        # This should be a method of UserManager
        return self.user_manager().user(username)

    def valid_login_names(self):
        """
        Return a list of users that can log in.

        OUTPUT:

        - a list of strings

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(tmp_dir()+'.sagenb')
            sage: nb.create_default_users('password')
            sage: nb.valid_login_names()
            ['admin']
            sage: nb.user_manager().add_user('Mark', 'password', '', force=True)
            sage: nb.user_manager().add_user('Sarah', 'password', '', force=True)
            sage: nb.user_manager().add_user('David', 'password', '', force=True)
            sage: sorted(nb.valid_login_names())
            ['David', 'Mark', 'Sarah', 'admin']
        """
        return self.user_manager().valid_login_names()

    def readonly_user(self, username):
        """
        Returns True if the user is supposed to only be a read-only user.
        """
        # It seems as though this should be an instance method of the User
        # class
        return self.__storage.readonly_user(username)

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
        # Note: Each Worksheet method *_directory actually creates a
        # directory, if it doesn't already exist.

        # More compact, but significantly less efficient?
        #      shutil.rmtree(W.cells_directory(), ignore_errors=True)
        #      shutil.rmtree(W.data_directory(), ignore_errors=True)
        #      shutil.rmtree(W.snapshots_directory(), ignore_errors=True)
        #      shutil.copytree(src.cells_directory(), W.cells_directory())
        #      shutil.copytree(src.data_directory(), W.data_directory())

        # datastore
        for sub in ['cells', 'data', 'snapshots']:
            target_dir = os.path.join(W.directory(), sub)
            if os.path.exists(target_dir):
                shutil.rmtree(target_dir, ignore_errors=True)

        # Copy images, data files, etc.
        for sub in ['cells', 'data']:
            source_dir = os.path.join(src.directory(), sub)
            if os.path.exists(source_dir):
                target_dir = os.path.join(W.directory(), sub)
                shutil.copytree(source_dir, target_dir)

        W.edit_save(src.edit_text())
        W.save()

    # datastore
    def pub_worksheets(self):
        path = self.__storage._abspath(self.__storage._user_path("pub"))
        v = []
        for id_number in os.listdir(path):
            if id_number.isdigit():
                a = "pub/" + id_number
                if a in self.__worksheets:
                    v.append(self.__worksheets[a].worksheet_that_was_published())
                else:
                    try:
                        w = self.__storage.load_worksheet("pub", int(id_number)).worksheet_that_was_published()
                        v.append(w)
                        self.__worksheets[a] = w
                    except Exception:
                        import traceback
                        print "Warning: problem loading %s/%s: %s"%("pub", id_number, traceback.format_exc())
        return v

    def users_worksheets(self, username):
        r"""
        Returns all worksheets owned by `username`
        """

        if username == "pub":
            return self.pub_worksheets()

        worksheets = self.__storage.worksheets(username)
        # if a worksheet has already been loaded in self.__worksheets, return
        # that instead since worksheets that are already running should be
        # noted as such
        return [self.__worksheets[w.filename()] if w.filename() in self.__worksheets else w for w in worksheets]

    def users_worksheets_view(self, username):
        r"""
        Returns all worksheets viewable by `username`
        """
        # Should return worksheets from self.__worksheets if possible
        worksheets = self.users_worksheets(username)
        user=self.user_manager().user(username)
        viewable_worksheets=[self.__storage.load_worksheet(owner, id) for owner,id in user.viewable_worksheets()]
        # we double-check that we can actually view these worksheets
        # just in case someone forgets to update the map
        worksheets.extend([w for w in viewable_worksheets if w.is_viewer(username)])
        # if a worksheet has already been loaded in self.__worksheets, return that instead
        # since worksheets that are already running should be noted as such
        return [self.__worksheets[w.filename()] if w.filename() in self.__worksheets else w for w in worksheets]

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
            sage: nb.user_manager().add_user('Mark','password','',force=True)
            sage: W = nb.new_worksheet_with_title_from_text('First steps', owner='Mark')
            sage: nb.worksheet_names()
            ['Mark/0']
            sage: nb.publish_worksheet(nb.get_worksheet_with_filename('Mark/0'), 'Mark')
            pub/0: [Cell 1: in=, out=]
            sage: sorted(nb.worksheet_names())
            ['Mark/0', 'pub/0']
        """
        W = None

        # Reuse an existing published version
        for X in self.get_worksheets_with_owner('pub'):
            if (X.worksheet_that_was_published() == worksheet):
                W = X

        # Or create a new one.
        if W is None:
            W = self.create_new_worksheet(worksheet.name(), 'pub')

        # Copy cells, output, data, etc.
        self._initialize_worksheet(worksheet, W)

        # Update metadata.
        W.set_worksheet_that_was_published(worksheet)
        W.move_to_archive(username)
        worksheet.set_published_version(W.filename())
        W.record_edit(username)
        W.set_name(worksheet.name())
        self.__worksheets[W.filename()] = W
        W.save()
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

    def create_new_worksheet(self, worksheet_name, username, add_to_list=True):
        if username!='pub' and self.user_manager().user_is_guest(username):
            raise ValueError("guests cannot create new worksheets")

        W = self.worksheet(username)

        W.set_system(self.system(username))
        W.set_name(worksheet_name)
        self.save_worksheet(W)
        self.__worksheets[W.filename()] = W

        return W

    def copy_worksheet(self, ws, owner):
        W = self.create_new_worksheet('default', owner)
        self._initialize_worksheet(ws, W)
        name = "Copy of %s" % ws.name()
        W.set_name(name)
        return W

    def delete_worksheet(self, filename):
        """
        Delete the given worksheet and remove its name from the worksheet
        list.  Raise a KeyError, if it is missing.

        INPUT:

        - ``filename`` - a string
        """
        try:
            W = self.__worksheets[filename]
        except KeyError:
            raise KeyError, "Attempt to delete missing worksheet '%s'"%filename
        
        W.quit()
        shutil.rmtree(W.directory(), ignore_errors=False)
        self.deleted_worksheets()[filename] = W

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
            sage: nb.user_manager().add_user('sage','sage','sage@sagemath.org',force=True)
            sage: W = nb.new_worksheet_with_title_from_text('Sage', owner='sage')
            sage: W._notebook = nb
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
            sage: nb.user_manager().add_user('sage','sage','sage@sagemath.org',force=True)
            sage: W = nb.new_worksheet_with_title_from_text('Sage', owner='sage')
            sage: nb.user_manager().add_user('wstein','sage','wstein@sagemath.org',force=True)
            sage: W2 = nb.new_worksheet_with_title_from_text('Elliptic Curves', owner='wstein')
            sage: nb.worksheet_names()
            ['sage/0', 'wstein/0']
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
            self.__server_number = (self.__server_number + 1) % len(P)
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
        tbl = {'v': None, 'u': None, 't': None}
        for x in ulimit.split('-'):
            for k in tbl.keys():
                if x.startswith(k): 
                    tbl[k] = int(x.split()[1].strip())
        if tbl['v'] is not None:
            tbl['v'] = tbl['v'] / 1000.0


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
        try: 
            return self.__python_command
        except AttributeError: 
            pass



    ##########################################################
    # Configuration settings.
    ##########################################################
    def system(self, username=None):
        """
        The default math software system for new worksheets for a
        given user or the whole notebook (if username is None).
        """
        return self.user(username).conf()['default_system']

    def pretty_print(self, username=None):
        """
        The default typeset setting for new worksheets for
        a given user or the whole notebook (if username is None).

        TODO -- only implemented for the notebook right now
        """
        return self.user(username).conf()['default_pretty_print']

    def set_pretty_print(self, pretty_print):
        self.__pretty_print = pretty_print

    def color(self):
        """
        The default color scheme for the notebook.
        """
        try:
            return self.__color
        except AttributeError:
            self.__color = 'default'
            return self.__color

    def set_color(self, color):
        self.__color = color

    ##########################################################
    # The notebook history.
    ##########################################################
    def user_history(self, username):
        if not hasattr(self, '_user_history'):
            self._user_history = {}
        if username in self._user_history:
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
        maxlen = self.user_manager().user_conf(username)['max_history_length']
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
        username = W.owner()
        id_number = W.id_number()
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
        try:
            W = S.load_worksheet(username, id_number)
        except ValueError:
            W = S.create_worksheet(username, id_number)
        self.__worksheets[W.filename()] = W
        return W

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
        ``owner``.  If the file extension is not recognized, raise a
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
            [TextCell 0: foo, Cell 1: in=2+3, out=]
        """
        if not os.path.exists(filename):
            raise ValueError("no file %s" % filename)

        # Figure out the file extension
        ext = os.path.splitext(filename)[1]
        if ext.lower() == '.txt':
            # A plain text file with {{{'s that defines a worksheet (no graphics).
            W = self._import_worksheet_txt(filename, owner)
        elif ext.lower() == '.sws':
            # An sws file (really a tar.bz2) which defines a worksheet with graphics, etc.
            W = self._import_worksheet_sws(filename, owner)
        elif ext.lower() == '.html':
            # An html file, which should contain the static version of
            # a sage help page, as generated by Sphinx
            html = open(filename).read()

            cell_pattern = r"""{{{id=.*?///.*?}}}"""
            docutils_pattern = r"""<meta name="generator" content="Docutils \S+: http://docutils\.sourceforge\.net/" />"""
            sphinx_pattern = r"""Created using <a href="http://sphinx\.pocoo\.org/">Sphinx</a>"""

            if re.search(cell_pattern, html, re.DOTALL) is not None:
                W = self._import_worksheet_txt(filename, owner)
            elif re.search(docutils_pattern, html) is not None:
                W = self._import_worksheet_docutils_html(filename, owner)
            elif re.search(sphinx_pattern, html) is not None:
                W = self._import_worksheet_html(filename, owner)
            else:
                # Unrecognized html file
                # We do the default behavior, i.e. we import as if it was generated
                # by Sphinx web page
                W = self._import_worksheet_html(filename, owner)
        elif ext.lower() == '.rst':
            # A ReStructuredText file
            W = self._import_worksheet_rst(filename, owner)
        else:
            # We only support txt, sws, html and rst files
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
            admin/0: [TextCell 0: foo, Cell 1: in=a = 10, out=]
        """
        # Open the worksheet txt file and load it in.
        worksheet_txt = open(filename).read()
        # Create a new worksheet with the right title and owner.
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
            sage: sorted([w.filename() for w in nb.get_all_worksheets()])
            ['admin/0']

        We then export the worksheet to an sws file.::

            sage: sws = os.path.join(tmp_dir(), 'tmp.sws')
            sage: nb.export_worksheet(W.filename(), sws)

        Now we import the sws.::

            sage: W = nb._import_worksheet_sws(sws, 'admin')
            sage: nb._Notebook__worksheets[W.filename()] = W

        Yes, it's there now (as a new worksheet)::

            sage: sorted([w.filename() for w in nb.get_all_worksheets()])
            ['admin/0', 'admin/1']
        """
        id_number = self.new_id_number(username)
        worksheet = self.__storage.import_worksheet(username, id_number, filename)

        # I'm not at all convinced this is a good idea, since we
        # support multiple worksheets with the same title very well
        # already.  So it's commented out.
        # self.change_worksheet_name_to_avoid_collision(worksheet)

        return worksheet

    def _import_worksheet_html(self, filename, owner):
        r"""
        Import a static html help page generated by Sphinx as a new
        worksheet.

        INPUT:

        -  ``filename`` - a string; a filename that ends in .html

        -  ``owner`` - a string; the imported worksheet's owner

        OUTPUT:

        -  a new instance of Worksheet

        EXAMPLES:

        We write a plain text worksheet to a file and import it
        using this function.::

            sage: nb = sagenb.notebook.notebook.Notebook(tmp_dir()+'.sagenb')
            sage: name = tmp_filename() + '.html'
            sage: fd = open(name,'w')
            sage: fd.write(''.join([
            ... '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"\n',
            ... '  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">\n',
            ... '\n',
            ... '<html xmlns="http://www.w3.org/1999/xhtml">\n',
            ... '  <head>\n',
            ... '   <title>Test notebook &mdash; test</title>\n',
            ... ' </head>\n',
            ... '  <body>\n',
            ... '   <div class="document">\n',
            ... '      <div class="documentwrapper">\n',
            ... '        <div class="bodywrapper">\n',
            ... '          <div class="body">\n',
            ... '<p>Here are some computations:</p>\n',
            ... '\n',
            ... '<div class="highlight-python"><div class="highlight"><pre>\n',
            ... '<span class="gp">sage',
            ... ': </span><span class="mi">1</span><span class="o">+</span><span class="mi">1</span>\n',
            ... '<span class="go">2</span>\n',
            ... '</pre></div></div>\n',
            ... '\n',
            ... '</div></div></div></div>\n',
            ... '</body></html>']))
            sage: fd.close()
            sage: W = nb._import_worksheet_html(name, 'admin')
            sage: W.name()
            u'Test notebook -- test'
            sage: W.owner()
            'admin'
            sage: W.cell_list()
            [TextCell 1: <div class="document">
                  <div class="documentwrapper">
                    <div class="bodywrapper">
                      <div class="body">
            <p>Here are some computations:</p>
            <BLANKLINE>
            <div class="highlight-python">, Cell 0: in=1+1, out=
            2, TextCell 2: </div>
            <BLANKLINE>
            </div></div></div></div>]
            sage: cell = W.cell_list()[1]
            sage: cell.input_text()
            u'1+1'
            sage: cell.output_text()
            u'<pre class="shrunk">2</pre>'
        """
        # Inspired from sagenb.notebook.twist.WorksheetFile.render
        doc_page_html = open(filename).read()
        from docHTMLProcessor import SphinxHTMLProcessor
        # FIXME: does SphinxHTMLProcessor raise an appropriate message
        # if the html file does not contain a Sphinx HTML page?
        doc_page = SphinxHTMLProcessor().process_doc_html(doc_page_html)

        from misc import extract_title
        title = extract_title(doc_page_html).replace('&mdash;','--')

        worksheet = self.create_new_worksheet(title, owner)
        worksheet.edit_save(doc_page)

        # FIXME: An extra compute cell is always added to the end.
        # Pop it off.
        cells = worksheet.cell_list()
        cells.pop()

        return worksheet

    def _import_worksheet_rst(self, filename, owner):
        r"""
        Import a ReStructuredText file as a new worksheet.

        INPUT:

        -  ``filename`` - a string; a filename that ends in .rst

        -  ``owner`` - a string; the imported worksheet's owner

        OUTPUT:

        -  a new instance of Worksheet

        EXAMPLES:

            sage: sprompt = 'sage' + ':'
            sage: rst = '\n'.join(['=============',
            ...       'Test Notebook',
            ...       '=============',
            ...       '',
            ...       'Let\'s do some computations::',
            ...       '',
            ...       '    %s 2+2' % sprompt,
            ...       '    4',
            ...       '',
            ...       '::',
            ...       '',
            ...       '    %s x^2' % sprompt,
            ...       '    x^2'])
            sage: name = tmp_filename() + '.rst'
            sage: fd = open(name,'w')
            sage: fd.write(rst)
            sage: fd.close()
            sage: nb = sagenb.notebook.notebook.Notebook(tmp_dir()+'.sagenb')
            sage: W = nb._import_worksheet_rst(name, 'admin')
            sage: W.name()
            u'Test Notebook'
            sage: W.owner()
            'admin'
            sage: W.cell_list()
            [TextCell 2: <h1 class="title">Test Notebook</h1>
            <BLANKLINE>
            <p>Let's do some computations:</p>, Cell 0: in=2+2, out=
            4, Cell 1: in=x^2, out=
            x^2]
            sage: cell = W.cell_list()[1]
            sage: cell.input_text()
            u'2+2'
            sage: cell.output_text()
            u'<pre class="shrunk">4</pre>'

        """
        rst = open(filename).read()

        # docutils removes the backslashes if they are not escaped This is
        # not practical because backslashes are almost never escaped in
        # Sage docstrings written in ReST.  So if the user wants the
        # backslashes to be escaped automatically, he adds the comment 
        # ".. escape-backslashes" in the input file
        if re.search(r'^\.\.[ \t]+escape-backslashes', rst, re.MULTILINE) is not None:
            rst = rst.replace('\\','\\\\')

        # Do the translation rst -> html (using docutils)
        from docutils.core import publish_parts
        D = publish_parts(rst, writer_name='html')
        title = D['title']
        html = D['whole']

        # Do the translation html -> txt
        from docHTMLProcessor import docutilsHTMLProcessor
        translator = docutilsHTMLProcessor()
        worksheet_txt = translator.process_doc_html(html)

        # Create worksheet
        worksheet = self.create_new_worksheet(title, owner)
        worksheet.edit_save(worksheet_txt)

        return worksheet

    def _import_worksheet_docutils_html(self, filename, owner):
        r"""
        Import a static html help page generated by docutils as a new
        worksheet.

        INPUT:

        -  ``filename`` - a string; a filename that ends in .html

        -  ``owner`` - a string; the imported worksheet's owner

        OUTPUT:

        -  a new instance of Worksheet

        EXAMPLES:

            sage: sprompt = 'sage' + ':'
            sage: rst = '\n'.join(['=============',
            ...       'Test Notebook',
            ...       '=============',
            ...       '',
            ...       'Let\'s do some computations::',
            ...       '',
            ...       '    %s 2+2' % sprompt,
            ...       '    4',
            ...       '',
            ...       '::',
            ...       '',
            ...       '    %s x^2' % sprompt,
            ...       '    x^2'])
            sage: from docutils.core import publish_string
            sage: html = publish_string(rst, writer_name='html')
            sage: name = tmp_filename() + '.html'
            sage: fd = open(name,'w')
            sage: fd.write(html)
            sage: fd.close()
            sage: nb = sagenb.notebook.notebook.Notebook(tmp_dir()+'.sagenb')
            sage: W = nb._import_worksheet_docutils_html(name, 'admin')
            sage: W.name()
            u'Test Notebook'
            sage: W.owner()
            'admin'
            sage: W.cell_list()
            [TextCell 2: <h1 class="title">Test Notebook</h1>
            <BLANKLINE>
            <p>Let's do some computations:</p>, Cell 0: in=2+2, out=
            4, Cell 1: in=x^2, out=
            x^2]
            sage: cell = W.cell_list()[1]
            sage: cell.input_text()
            u'2+2'
            sage: cell.output_text()
            u'<pre class="shrunk">4</pre>'

        """
        html = open(filename).read()

        # Do the translation html -> txt
        from docHTMLProcessor import docutilsHTMLProcessor
        translator = docutilsHTMLProcessor()
        worksheet_txt = translator.process_doc_html(html)

        # Extract title
        from worksheet import extract_name
        title, _ = extract_name(worksheet_txt)
        if title.startswith('<h1 class="title">'):
            title = title[18:]
        if title.endswith('</h1>'):
            title = title[:-5]

        # Create worksheet
        worksheet = self.create_new_worksheet(title, owner)
        worksheet.edit_save(worksheet_txt)

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
            while name + " (%s)" % i in display_names:
                i += 1
            name = name + " (%s)" % i
            worksheet.set_name(name)


    ##########################################################
    # Server configuration
    ##########################################################
    def conf(self):
        try:
            return self.__conf
        except AttributeError:
            C = server_conf.ServerConfiguration()
            # if we are newly creating a notebook, then we want to 
            # have a default model version of 1, currently
            # we can't just set the default value in server_conf.py 
            # to 1 since it would then be 1 for notebooks without the
            # model_version property
            # TODO: distinguish between a new server config default values
            #  and default values for missing properties
            C['model_version'] = 1
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
        for W in self.__worksheets.values():
            W.quit()

    def update_worksheet_processes(self):
        worksheet.update_worksheets()

    def quit_idle_worksheet_processes(self):
        timeout = self.conf()['idle_timeout']
        if timeout == 0:
            # Quit only the doc browser worksheets
            for W in self.__worksheets.values():
                if W.docbrowser() and W.compute_process_has_been_started():
                    W.quit_if_idle(self.conf()['idle_timeout'])
            return

        for W in self.__worksheets.values():
            if W.compute_process_has_been_started():
                W.quit_if_idle(timeout)

    def quit_worksheet(self, W):
        try:
            del self.__worksheets[W.filename()]
        except KeyError:
            pass

    ##########################################################
    # Worksheet listing
    ##########################################################
    def worksheet_list_for_public(self, username, sort='last_edited', reverse=False, search=None):
        W = self.pub_worksheets()

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
    # Accessing all worksheets with certain properties.
    ##########################################################
    def active_worksheets_for(self, username):
        # TODO: check if the worksheets are active
        #return [ws for ws in self.get_worksheets_with_viewer(username) if ws.is_active(username)]
        return self.users_worksheets_view(username)
    
    def get_all_worksheets(self):
        """
        We should only call this if the user is admin!
        """
        all_worksheets = []
        for username in self._user_manager.users():
            if username in ['_sage_', 'pub']:
                continue
            for w in self.users_worksheets(username):
                all_worksheets.append(w)
        return all_worksheets

    def get_worksheets_with_viewer(self, username):
        if self._user_manager.user_is_admin(username): return self.get_all_worksheets()
        return self.users_worksheets_view(username)

    def get_worksheets_with_owner(self, owner):
        return self.users_worksheets(owner)

    def get_worksheet_with_filename(self, filename):
        """
        Get the worksheet with the given filename.  If there is no
        such worksheet, raise a ``KeyError``.

        INPUT:

        - ``filename`` - a string

        OUTPUT:

        - a Worksheet instance
        """
        try:
            return self.__worksheets[filename]
        except KeyError:
            raise KeyError, "No worksheet with filename '%s'"%filename

    ###########################################################
    # Saving the whole notebook
    ###########################################################
    def save(self):
        """
        Save this notebook server to disk.
        """
        S = self.__storage
        S.save_users(self.user_manager().users())
        S.save_server_conf(self.conf())
        self._user_manager.save(S)
        # Save the non-doc-browser worksheets.
        for n, W in self.__worksheets.items():
            if not n.startswith('doc_browser'):
                S.save_worksheet(W)
        if hasattr(self, '_user_history'):
            for username, H in self._user_history.iteritems():
                S.save_user_history(username, H)

    def save_worksheet(self, W, conf_only=False):
        self.__storage.save_worksheet(W, conf_only=conf_only)

    def logout(self, username):
        if username is None:
            return
        for filename, W in self.__worksheets.items():
            if filename.startswith(username + "/"):
                W.quit()

    def delete_doc_browser_worksheets(self):
        for w in self.users_worksheets('_sage_'):
            if w.name().startswith('doc_browser'):
                self.delete_worksheet(w.filename())

    def upgrade_model(self):
        """
        Upgrade the model, if needed.

        - Version 0 (or non-existent model version, which defaults to 0): Original flask notebook
        - Version 1: shared worksheet data cached in the User object
        """
        model_version=self.conf()['model_version']
        if model_version is None or model_version<1:
            print "Upgrading model version to version 1"
            # this uses code from get_all_worksheets()
            user_manager = self.user_manager()
            num_users=0
            for username in self._user_manager.users():
                num_users+=1
                if num_users%1000==0:
                    print 'Upgraded %d users'%num_users
                if username in ['_sage_', 'pub']:
                    continue
                try:
                    for w in self.users_worksheets(username):
                        owner = w.owner()
                        id_number = w.id_number()
                        collaborators = w.collaborators()
                        for u in collaborators:
                            try:
                                user_manager.user(u).viewable_worksheets().add((owner, id_number))
                            except KeyError:
                                # user doesn't exist
                                pass
                except (UnicodeEncodeError,OSError):
                    # Catch UnicodeEncodeError because sometimes a username has a non-ascii character
                    # Catch OSError since sometimes when moving user directories (which happens
                    #   automatically when getting user's worksheets), OSError: [Errno 39] Directory not empty
                    #   is thrown (we should be using shutil.move instead, probably)
                    # users with these problems won't have their sharing cached, but they will probably have
                    # problems logging in anyway, so they probably won't notice not having shared worksheets
                    import sys
                    import traceback
                    print >> sys.stderr, 'Error on username %s'%username.encode('utf8')
                    print >> sys.stderr, traceback.format_exc()
                    pass
            print 'Done upgrading to model version 1'
            self.conf()['model_version'] = 1
        
####################################################################

# TODO
def load_notebook(dir, interface=None, port=None, secure=None, user_manager=None):
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
                raise KeyboardInterrupt("Interrupted notebook migration.  Delete the directory '%s' and try again." % (os.path.abspath(dir+'.sagenb')))
            return nb
        dir += '.sagenb'

    dir = make_path_relative(dir)
    nb = Notebook(dir)
    nb.interface = interface
    nb.port = port
    nb.secure = secure


    # Install this copy of the notebook in misc.py as *the*
    # global notebook object used for computations.  This is
    # mainly to avoid circular references, etc.  This also means
    # only one notebook can actually be used at any point.
    import sagenb.notebook.misc
    sagenb.notebook.misc.notebook = nb

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
    print "*" * 80
    print "*"
    print "* The Sage notebook at"
    print "*"
    print "*      '%s'" % os.path.abspath(dir)
    print "*"
    print "* will be upgraded to a new format and stored in"
    print "*"
    print "*      '%s.sagenb'." % os.path.abspath(dir)
    print "*"
    print "* Your existing notebook will not be modified in any way."
    print "*"
    print "*" * 80
    print ""
    ans = raw_input("Would like to continue? [YES or no] ").lower()
    if ans not in ['', 'y', 'yes']:
        raise RuntimeError("User aborted upgrade.")

    # Create new notebook
    new_nb = Notebook(dir + '.sagenb')

    # Define a function for transfering the attributes of one object to another.
    def transfer_attributes(old, new, attributes):
        for attr_old, attr_new in attributes:
            if hasattr(old, attr_old):
                setattr(new, attr_new, getattr(old, attr_old))

    # Transfer all the notebook attributes to our new notebook object

    new_nb.conf().confs = old_nb.conf().confs
    for t in ['pretty_print', 'server_pool', 'ulimit', 'system']:
        if hasattr(old_nb, '_Notebook__' + t):
            new_nb.conf().confs[t] = getattr(old_nb, '_Notebook__' + t)

    # Now update the user data from the old notebook to the new one:
    print "Migrating %s user accounts..." % len(old_nb.user_manager().users())
    users = new_nb.user_manager().users()
    for username, old_user in old_nb.user_manager().users().iteritems():
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
                if isinstance(user, str):
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
        ws_pub = (ws_pub[0], int(ws_pub[1]))

        obj = {'name': old_ws.name(), 'system': old_ws.system(),
               'viewers': old_ws.viewers(), 
               'collaborators' :old_ws.collaborators(),
               'pretty_print': old_ws.pretty_print(), 
               'ratings': old_ws.ratings(),
               'auto_publish': old_ws.is_auto_publish(), 'tags': tags,
               'last_change': last_change,
               'published_id_number': published_id_number,
               'worksheet_that_was_published': ws_pub
               }

        new_ws.reconstruct_from_basic(obj)

        base = os.path.join(dir, 'worksheets', old_ws.filename())
        worksheet_file = os.path.join(base, 'worksheet.txt')
        if os.path.exists(worksheet_file):
            text = open(worksheet_file).read()
            # delete first two lines -- we don't embed the title or
            # system in the worksheet text anymore.
            i = text.find('\n')
            text=text[i+1:]
            i = text.find('\n')
            text=text[i+1:]
            new_ws.edit_save(text)

        # copy over the DATA directory and cells directories
        try:
            dest = new_ws.data_directory()
            if os.path.exists(dest): 
                shutil.rmtree(dest)
            shutil.copytree(old_ws.data_directory(), dest)
        except Exception, msg:
            print msg

        try:
            if os.path.exists(old_ws.cells_directory()):
                dest = new_ws.cells_directory()
                if os.path.exists(dest): 
                    shutil.rmtree(dest)
                shutil.copytree(old_ws.cells_directory(), dest)
        except Exception, msg:
            print msg


        return new_ws

    worksheets = WorksheetDict(new_nb)
    num_worksheets = len(old_nb._Notebook__worksheets)
    print "Migrating (at most) %s worksheets..." % num_worksheets
    from sage.misc.misc import walltime
    tm = walltime()
    i = 0
    for ws_name, old_ws in old_nb._Notebook__worksheets.iteritems():
        if old_ws.docbrowser(): continue
        i += 1
        if i % 25==0:
            percent = i / float(num_worksheets)
            # total_time * percent = time_so_far, so
            # remaining_time = total_time - time_so_far = time_so_far*(1/percent - 1)
            print "    Migrated %s (of %s) worksheets (about %.0f seconds remaining)" % (
                i, num_worksheets, walltime(tm) * (1 / percent - 1))
        new_ws = migrate_old_worksheet(old_ws)
        worksheets[new_ws.filename()] = new_ws
    new_nb._Notebook__worksheets = worksheets

    # Migrating history
    new_nb._user_history = {}
    for username in old_nb.user_manager().users().keys():
        history_file = os.path.join(dir, 'worksheets', username, 'history.sobj')
        if os.path.exists(history_file):
            new_nb._user_history[username] = cPickle.loads(open(history_file).read())

    # Save our newly migrated notebook to disk
    new_nb.save()

    print "Worksheet migration completed."
    return new_nb

# TODO
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
        def c(a, b):
            return cmp((a.name().lower(), -a.last_edited()), (b.name().lower(), -b.last_edited()))
        f = c
    elif sort == 'owner':
        def c(a, b):
            return cmp((a.owner().lower(), -a.last_edited()), (b.owner().lower(), -b.last_edited()))
        f = c
    elif sort == "rating":
        def c(a, b):
            return -cmp((a.rating(), -a.last_edited()), (b.rating(), -b.last_edited()))
        f = c
    else:
        raise ValueError("invalid sort key '%s'" % sort)
    v.sort(cmp = f, reverse=reverse)
