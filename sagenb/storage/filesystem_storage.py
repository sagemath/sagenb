# -*- coding: utf-8 -*
"""
A Filesystem-based Sage Notebook Datastore

Here is the filesystem layout for this datastore.  Note that the all
of the pickles are pickles of basic Python objects, so can be
unpickled in any version of Python with or without Sage or the Sage
notebook installed.  They are also not compressed, so are reasonably
easy to read ASCII.

The filesystem layout is as follows.  It mirrors the URL's used by the
Sage notebook server::

    sage_notebook.sagenb
         conf.pickle
         users.pickle
         openid.pickle (optional)
         readonly.txt (optional)
         home/
             username0/
                history.pickle
                id_number0/
                    worksheet.html
                    worksheet_conf.pickle
                    cells/
                    data/
                    snapshots/
                id_number1/
                    worksheet.html
                    worksheet_conf.pickle
                    cells/
                    data/
                    snapshots/
                ...
             username1/
             ...
             
"""

import copy
import shutil
import tarfile
import tempfile
import os
try:
   import cPickle as pickle
except ImportError:
   import pickle
from six import iteritems

from .abstract_storage import Datastore
from sagenb.misc.misc import set_restrictive_permissions, encoded_str

from sage.misc.temporary_file import atomic_write

def is_safe(a):
    """
    Used when importing contents of various directories from Sage
    worksheet files.  We define this function to avoid the possibility
    of a user crafting fake sws file such that extracting it creates
    files outside where we want, e.g., by including .. or / in the
    path of some file.
    """
    # NOTE: Windows port -- I'm worried about whether a.name will have
    # / or \ on windows.  The code below assume \.
    return '..' not in a and not a.startswith('/')


class FilesystemDatastore(Datastore):
    def __init__(self, path):
        """
        INPUT:

           - ``path`` -- string, path to this datastore

        EXAMPLES::

            sage: from sagenb.storage import FilesystemDatastore
            sage: FilesystemDatastore(tmp_dir())
            Filesystem Sage Notebook Datastore at ...
        """
        path = os.path.abspath(path)
        self._path = path
        self._makepath(os.path.join(self._path, 'home'))
        self._home_path = 'home'
        self._conf_filename = 'conf.pickle'
        self._users_filename = 'users.pickle'
        self._readonly_filename = 'readonly.txt'
        self._readonly_mtime = 0
        self._readonly = None

    def __repr__(self):
        return "Filesystem Sage Notebook Datastore at %s"%self._path

    #########################################################################
    # Paths
    #########################################################################
    def _makepath(self, path):
        p = self._abspath(path)
        if not os.path.exists(p): os.makedirs(p)
        return path
    
    def _deep_user_path(self, username):
        from hashlib import md5
        h = md5(username).hexdigest()
        base = ['__store__', h[:1], h[:2], h[:3], h[:4]]
        path = os.path.join(*base)
        self._makepath(self._abspath(os.path.join(self._home_path, path)))
        return os.path.join(path, username)

    def _user_path(self, username):
        # There are weird cases, e.g., old notebook server migration
        # where username is None, and if we don't string it here,
        # saving can be broken (at a bad moment!).
        
        # There are also some cases where the username could have unicode in it.
        username = str(username)
        path = self._abspath(os.path.join(self._home_path, username))
        if not os.path.islink(path):
            if not os.path.exists(path):
                self._makepath(path)

            old_dir = os.getcwd()
            os.chdir(self._abspath(self._home_path))
            new_path = self._deep_user_path(username)

            #Move the directory to the __store__ directory
            os.rename(path, new_path)

            #new_path now points to the actual directory
            os.symlink(new_path, username)
            os.chdir(old_dir)

        return path
    
    def _worksheet_pathname(self, username, id_number):
        return os.path.join(self._user_path(username), str(id_number))
    
    def _worksheet_path(self, username, id_number=None):
        if id_number is None:
            return self._makepath(self._user_path(username))
        return self._makepath(self._worksheet_pathname(username, id_number))

    def _worksheet_conf_filename(self, username, id_number):
        return os.path.join(self._worksheet_path(username, id_number), 'worksheet_conf.pickle')

    def _worksheet_html_filename(self, username, id_number):
        return os.path.join(self._worksheet_path(username, id_number), 'worksheet.html')

    def _history_filename(self, username):
        return os.path.join(self._user_path(username), 'history.pickle')

    def _abspath(self, file):
        """
        Return absolute path to filename got by joining self._path
        with the string file.

        OUTPUT:

            -- ``string``

        EXAMPLES::

            sage: from sagenb.storage import FilesystemDatastore
            sage: FilesystemDatastore(tmp_dir())._abspath('foo.pickle')
            '...foo.pickle'
        """
        return os.path.join(self._path, file)
    
    #########################################################################
    # Loading and saving basic Python objects to disk.
    # The input filename is always relative to self._path.
    #########################################################################
    def _load(self, filename):
        with open(self._abspath(filename)) as f:
            result = pickle.load(f)
        return result

    def _save(self, obj, filename):
        """
        TESTS:

        Check that interrupting ``_save`` is safe::

            sage: from sagenb.storage.filesystem_storage import FilesystemDatastore
            sage: D = FilesystemDatastore("")
            sage: fn = tmp_filename()
            sage: s = "X" * 100000
            sage: D._save(s, fn)
            sage: try:  # long time
            ....:     alarm(1)
            ....:     while True:
            ....:         D._save(s, fn)
            ....: except (AlarmInterrupt, OSError):
            ....:     # OSError could happen due to a double close() in
            ....:     # Python's tempfile module.
            ....:     pass
            sage: len(D._load(fn))
            100000
        """
        s = pickle.dumps(obj)
        if len(s) == 0:
            raise ValueError("Invalid Pickle")
        with atomic_write(self._abspath(filename)) as f:
            f.write(s)

    def _permissions(self, filename):
        f = self._abspath(filename)
        if os.path.exists(f):
            set_restrictive_permissions(f, allow_execute=False)

    #########################################################################
    # Conversions to and from basic Python database (so that json
    # storage will work).
    #########################################################################
    def _basic_to_users(self, obj):
        from sagenb.notebook.user import User_from_basic
        return dict([(name, User_from_basic(basic)) for name, basic in obj])

    def _users_to_basic(self, users):
        new = sorted([[name, U.basic()] for name, U in iteritems(users)])
        return new

    def _basic_to_server_conf(self, obj):
        from sagenb.notebook.server_conf import ServerConfiguration_from_basic
        return ServerConfiguration_from_basic(obj)

    def _server_conf_to_basic(self, server):
        return server.basic()

    def _basic_to_worksheet(self, obj):
        """
        Given a basic Python object obj, return corresponding worksheet.
        """
        from sagenb.notebook.worksheet import Worksheet_from_basic
        path = self._abspath(self._worksheet_path(obj['owner']))
        return Worksheet_from_basic(obj, path)

    def _worksheet_to_basic(self, worksheet):
        """
        Given a worksheet, create a corresponding basic Python object
        that completely defines that worksheet.
        """
        return worksheet.basic()

    #########################################################################
    # Now we implement the API we're supposed to implement
    #########################################################################
    
    def load_server_conf(self):
        return self._basic_to_server_conf(self._load('conf.pickle'))
    
    def save_server_conf(self, server_conf):
        """
        INPUT:

            - ``server`` --
        """
        basic = self._server_conf_to_basic(server_conf)
        self._save(basic, 'conf.pickle')
        self._permissions('conf.pickle')

    def load_openid(self):
        """
        Loads an open_id dict read from the disk.
        """
        return self._load('openid.pickle')

    def save_openid(self, openid_dict):
        """
        Saves an open_id dict to the disk.
        """
        self._save(openid_dict, 'openid.pickle')
        self._permissions('openid.pickle')

    def load_users(self, user_manager):
        """
        OUTPUT:

            - dictionary of user info
        
        EXAMPLES::
        
            sage: from sagenb.notebook.user import User
            sage: from sagenb.notebook.user_manager import SimpleUserManager
            sage: U = SimpleUserManager()
            sage: users = {'admin':User('admin','abc','a@b.c','admin'), 'wstein':User('wstein','xyz','b@c.d','user')}
            sage: from sagenb.storage import FilesystemDatastore
            sage: ds = FilesystemDatastore(tmp_dir())
            sage: ds.save_users(users)
            sage: 'users.pickle' in os.listdir(ds._path)
            True
            sage: users = ds.load_users(U)
            sage: U.users()
            {'admin': admin, 'wstein': wstein}
        """
        for user in self._basic_to_users(self._load('users.pickle')).itervalues():
            user_manager.add_user_object(user, force=True) 
            user_manager.set_password(user.username(), user.password(), encrypt = False)
        return user_manager
    
    def save_users(self, users):
        """
        INPUT:

            - ``users`` -- dictionary mapping user names to users
        
        EXAMPLES::
        
            sage: from sagenb.notebook.user import User
            sage: from sagenb.notebook.user_manager import SimpleUserManager
            sage: U = SimpleUserManager()
            sage: users = {'admin':User('admin','abc','a@b.c','admin'), 'wstein':User('wstein','xyz','b@c.d','user')}
            sage: from sagenb.storage import FilesystemDatastore
            sage: ds = FilesystemDatastore(tmp_dir())
            sage: ds.save_users(users)
            sage: 'users.pickle' in os.listdir(ds._path)
            True
            sage: users = ds.load_users(U)
            sage: U.users()
            {'admin': admin, 'wstein': wstein}
        """
        self._save(self._users_to_basic(users), 'users.pickle')
        self._permissions('users.pickle')
        
    def load_user_history(self, username):
        """
        Return the history log for the given user.

        INPUT:

            - ``username`` -- string

        OUTPUT:

            - list of strings
        """
        filename = self._history_filename(username)
        if not os.path.exists(self._abspath(filename)):
            return []
        return self._load(filename)

    def save_user_history(self, username, history):
        """
        Save the history log (a list of strings) for the given user.

        INPUT:

            - ``username`` -- string

            - ``history`` -- list of strings
        """
        filename = self._history_filename(username)
        self._save(history, filename)
        self._permissions(filename)
        
    def save_worksheet(self, worksheet, conf_only=False):
        """
        INPUT:

            - ``worksheet`` -- a Sage worksheet

            - ``conf_only`` -- default: False; if True, only save
              the config file, not the actual body of the worksheet      

        EXAMPLES::
        
            sage: from sagenb.notebook.worksheet import Worksheet
            sage: tmp = tmp_dir()
            sage: W = Worksheet('test', 2, tmp, system='gap', owner='sageuser')
            sage: from sagenb.storage import FilesystemDatastore
            sage: DS = FilesystemDatastore(tmp)
            sage: DS.save_worksheet(W)
        """
        username = worksheet.owner(); id_number = worksheet.id_number()
        basic = self._worksheet_to_basic(worksheet)
        if not hasattr(worksheet, '_last_basic') or worksheet._last_basic != basic:
            # only save if changed
            self._save(basic, self._worksheet_conf_filename(username, id_number))
            worksheet._last_basic = basic
        if not conf_only and worksheet.body_is_loaded():
            # only save if loaded
            # todo -- add check if changed
            filename = self._worksheet_html_filename(username, id_number)
            with atomic_write(self._abspath(filename)) as f:
                f.write(worksheet.body().encode('utf-8', 'ignore'))

    def create_worksheet(self, username, id_number):
        """
        Create worksheet with given id_number belonging to the given user.

        If the worksheet already exists, return ValueError.

        INPUT:

            - ``username`` -- string

            - ``id_number`` -- integer

        OUTPUT:

            - a worksheet
        """
        filename = self._worksheet_html_filename(username, id_number)
        html_file = self._abspath(filename)
        if os.path.exists(html_file):
            raise ValueError("Worksheet %s/%s already exists"%(username, id_number))

        # We create the worksheet
        W = self._basic_to_worksheet({'owner':username, 'id_number':id_number})
        W.clear()
        return W

    def load_worksheet(self, username, id_number):
        """
        Return worksheet with given id_number belonging to the given
        user.

        If the worksheet does not exist, return ValueError.

        INPUT:

            - ``username`` -- string

            - ``id_number`` -- integer

        OUTPUT:

            - a worksheet
        """
        # Prevent arbitrary directories from being created by
        # self.__worksheet_html_filename
        dirname = self._worksheet_pathname(username, id_number)
        if not os.path.exists(dirname):
            raise ValueError("Worksheet %s/%s does not exist"%(username, id_number))
        
        filename = self._worksheet_html_filename(username, id_number)
        html_file = self._abspath(filename)
        if not os.path.exists(html_file):
            raise ValueError("Worksheet %s/%s does not exist"%(username, id_number))

        try:
            basic = self._load(self._worksheet_conf_filename(username, id_number))
            basic['owner'] = username
            basic['id_number'] = id_number
            W = self._basic_to_worksheet(basic)
            W._last_basic = basic   # cache
        except Exception:
            #the worksheet conf loading didn't work, so we make up one
            import traceback
            print("Warning: problem loading config for %s/%s; using default config: %s" % (username, id_number, traceback.format_exc()))
            W = self._basic_to_worksheet({'owner':username, 'id_number': id_number})
            if username=='_sage_':
                # save the default configuration, since this may be loaded by a random other user
                # since *anyone* looking at docs will load all _sage_ worksheets
                print("Saving default configuration (overwriting corrupt configuration) for %s/%s" % (username, id_number))
                self.save_worksheet(W, conf_only=True)
        return W


    def export_worksheet(self, username, id_number, filename, title):
        """
        Export the worksheet with given username and id_number to the
        given filename (e.g., 'worksheet.sws').

        INPUT:
    
            - ``title`` - title to use for the exported worksheet (if
               None, just use current title)
        """
        T = tarfile.open(filename, 'w:bz2')
        worksheet = self.load_worksheet(username, id_number)
        basic = copy.deepcopy(self._worksheet_to_basic(worksheet))
        if title:
            # change the title
            basic['name'] = title
        basic['name'] = encoded_str(basic['name'])
        # Remove metainformation that perhaps shouldn't be distributed
        for k in ['owner', 'ratings', 'worksheet_that_was_published', 'viewers', 'tags', 'published_id_number',
                  'collaborators', 'auto_publish']:
            if k in basic:
                del basic[k]
                
        self._save(basic, self._worksheet_conf_filename(username, id_number) + '2')
        tmp = self._abspath(self._worksheet_conf_filename(username, id_number) + '2')
        T.add(tmp, os.path.join('sage_worksheet','worksheet_conf.pickle'))
        os.unlink(tmp)

        worksheet_html = self._abspath(self._worksheet_html_filename(username, id_number))
        T.add(worksheet_html, os.path.join('sage_worksheet','worksheet.html'))

        # The following is purely for backwards compatibility with old
        # notebook servers prior to sage-4.1.2.
        fd, worksheet_txt =  tempfile.mkstemp()
        old_heading = "%s\nsystem:%s\n"%(basic['name'], basic['system'])
        with open(worksheet_txt,'w') as f:
            with open(worksheet_html) as g:
                f.write(old_heading + g.read())
        T.add(worksheet_txt,
              os.path.join('sage_worksheet','worksheet.txt'))
        os.unlink(worksheet_txt)
        # important, so we don't leave an open file handle!
        os.close(fd)
        # end backwards compat block.


        # Add the contents of the DATA directory
        path = self._abspath(self._worksheet_pathname(username, id_number))
        data = os.path.join(path, 'data')
        if os.path.exists(data):
            for X in os.listdir(data):
                T.add(os.path.join(data, X), os.path.join('sage_worksheet','data',X))
                    
        # Add the contents of each of the cell directories.
        cells = os.path.join(path, 'cells')
        if os.path.exists(cells):
            for X in os.listdir(cells):
                T.add(os.path.join(cells, X), os.path.join('sage_worksheet','cells',X))

        # NOTE: We do not export the snapshot/undo data.  People
        # frequently *complain* about Sage exporting a record of their
        # mistakes anyways.
        T.close()


    def _import_old_worksheet(self, username, id_number, filename):
        """
        Import a worksheet from an old version of Sage. 
        """
        T = tarfile.open(filename, 'r:bz2')
        members = [a for a in T.getmembers() if 'worksheet.txt' in a.name and is_safe(a.name)]
        if len(members) == 0:
            raise RuntimeError("unable to import worksheet")

        worksheet_txt = members[0].name
        W = self.load_worksheet(username, id_number)
        W.edit_save_old_format(T.extractfile(worksheet_txt).read().decode('utf-8', 'ignore'))
        # '/' is right, since old worksheets always unix
        dir = worksheet_txt.split('/')[0]
            
        path = self._abspath(self._worksheet_pathname(username, id_number))

        base = os.path.join(dir,'data')
        members = [a for a in T.getmembers() if a.name.startswith(base) and is_safe(a.name)]
        if len(members) > 0:
            T.extractall(path, members)
            dest = os.path.join(path, 'data')
            if os.path.exists(dest): shutil.rmtree(dest)
            shutil.move(os.path.join(path,base), path)
        
        base = os.path.join(dir,'cells')
        members = [a for a in T.getmembers() if a.name.startswith(base) and is_safe(a.name)]
        if len(members) > 0:
            T.extractall(path, members)
            dest = os.path.join(path, 'cells')
            if os.path.exists(dest): shutil.rmtree(dest)
            shutil.move(os.path.join(path, base), path)
            
        tmp = os.path.join(path, dir)
        if os.path.exists(tmp):
            shutil.rmtree(tmp)

        T.close()

        return W
            

    def import_worksheet(self, username, id_number, filename):
        """
        Import the worksheet username/id_number from the file with
        given filename.
        """
        path = self._abspath(self._worksheet_pathname(username, id_number))
        if os.path.exists(path):
            shutil.rmtree(path, ignore_errors=True)
        os.makedirs(path)
        T = tarfile.open(filename, 'r:bz2')
        try:
            with open(self._abspath(self._worksheet_conf_filename(username, id_number)),'w') as f:
                f.write(T.extractfile(os.path.join('sage_worksheet','worksheet_conf.pickle')).read())
        except KeyError:
            # Not a valid worksheet.  This might mean it is an old
            # worksheet from a previous version of Sage.
            return self._import_old_worksheet(username, id_number, filename)

        with open(self._abspath(self._worksheet_html_filename(username, id_number)),'w') as f:
            f.write(T.extractfile(os.path.join('sage_worksheet','worksheet.html')).read())

        base = os.path.join('sage_worksheet','data')
        members = [a for a in T.getmembers() if a.name.startswith(base) and is_safe(a.name)]
        if len(members) > 0:
            T.extractall(path, members)
            shutil.move(os.path.join(path,base), path)
        
        base = os.path.join('sage_worksheet','cells')
        members = [a for a in T.getmembers() if a.name.startswith(base) and is_safe(a.name)]
        if len(members) > 0:
            T.extractall(path, members)
            shutil.move(os.path.join(path, base), path)

        tmp = os.path.join(path, 'sage_worksheet')
        if os.path.exists(tmp):
            shutil.rmtree(tmp)
        
        T.close()
        
        return self.load_worksheet(username, id_number)
        
    def worksheets(self, username):
        """
        Return list of all the worksheets belonging to the user with
        given name.  If the given user does not exists, an empty list
        is returned.

        EXAMPLES: The load_user_data function must be defined in the
        derived class::
        
            sage: from sagenb.storage import FilesystemDatastore
            sage: tmp = tmp_dir()
            sage: FilesystemDatastore(tmp).worksheets('foobar')
            []
            sage: from sagenb.notebook.worksheet import Worksheet
            sage: W = Worksheet('test', 2, tmp, system='gap', owner='sageuser')
            sage: from sagenb.storage import FilesystemDatastore
            sage: DS = FilesystemDatastore(tmp)
            sage: DS.save_worksheet(W)
            sage: DS.worksheets('sageuser')
            [sageuser/2: [Cell 0: in=, out=]]
        """
        path = self._abspath(self._user_path(username))
        if not os.path.exists(path): return []
        v = []
        for id_number in os.listdir(path):
            if id_number.isdigit():
                try:
                    v.append(self.load_worksheet(username, int(id_number)))
                except Exception:
                    import traceback
                    print("Warning: problem loading %s/%s: %s" % (username, id_number, traceback.format_exc()))
        return v

    def readonly_user(self, username):
        """
        Each line of the readonly file has a username.
        """
        filename = os.path.join(self._path, self._readonly_filename)
        if not os.path.exists(filename):
            return False
        mtime = os.path.getmtime(filename)
        if mtime > self._readonly_mtime:
            with open(filename) as f:
                self._readonly = set(line for line in (l.strip() for l in f) if len(line)>0)
            self._readonly_mtime = mtime
        return username in self._readonly

    def delete(self):
        """
        Delete all files associated with this datastore.  Dangerous!
        This is only here because it is useful for doctesting.
        """
        shutil.rmtree(self._path, ignore_errors=True)



##############################################################################
# 
# Why not use JSON, YAML, or XML??
#
# I experimented with using these, but they are 10-100 times slower,
# and there is no real benefit.  More precisely, the time for
# dumping/loading a worksheet basic datastructure in each of the
# following is given below.  XML is also very bad compared to cPickle.
#
#     cPickle, 
#     pickle
#     json
#     yaml
#     yaml + C
#
# This is all on OS X 10.6 64-bit.  Here b = w.basic() for any worksheet w.
#
# sage: import cPickle
# sage: timeit('cPickle.loads(cPickle.dumps(b))')
# 625 loops, best of 3: 51.9 us (microseconds) per loop
# sage: import pickle
# sage: timeit('pickle.loads(pickle.dumps(b))')
# 625 loops, best of 3: 464 us  (microseconds) per loop
# sage: import json
# sage: timeit('json.loads(json.dumps(b))')
# 625 loops, best of 3: 449 us  (microseconds) per loop
# sage: timeit('json.loads(json.dumps(b,indent=4))')
# 625 loops, best of 3: 625 us  (microseconds) per loop
# sage: import yaml
# sage: timeit('yaml.load(yaml.dump(b))')
# 25 loops, best of 3: 13.5 ms per loop
# sage: from yaml import load, dump
# sage: from yaml import CLoader as Loader
# sage: from yaml import CDumper as Dumper
# sage: timeit('yaml.load(yaml.dump(b,Dumper=Dumper),Loader=Loader)')   # c++ yaml
# 125 loops, best of 3: 1.77 ms per loop
#
# Other problems: json.load(json.dump(b)) != b, because of unicode and
# all kinds of weirdness
# Yaml C library is hard to install; and yaml itself is not included in python (json is).
# Anyway, the difference between 2-13ms and 52 microseconds is significant.
# At 2ms, 100,000 worksheets takes 200 seconds, versus only 5 seconds
# at 52 microseconds.  cPickle just can't be beat.
#
# NOTE!  Actually simplejson does just as well at cPickle for this benchmark.
#        Thanks to Mitesh Patel for pointing this out. 
#
#############################################################################
