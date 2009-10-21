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

import copy, cPickle, shutil, tarfile, tempfile

import os

from abstract_storage import Datastore
from sagenb.misc.misc import set_restrictive_permissions

def is_safe(a):
    """
    Used when importing contents of various directories from Sage
    worksheet files.  We define this function to avoid the possibility
    of a user crafting fake sws file such that extracting it creates
    files outside where we want, e.g., by including .. or / in the
    path of some file.
    """
    # NOTE: Windows port -- I'm worried about whether a.name will have / or \ on windows.
    # The code below assume \.
    return '..' not in a and not a.startswith('/')


class FilesystemDatastore(Datastore):
    def __init__(self, path):
        """
        INPUT:

           - ``path`` -- string, path to this datastore

        EXAMPLES::

            sage: from sagenb.storage.abstract_storage import Datastore
            sage: Datastore('/tmp/ds')
            Abstract Datastore
        """
        path = os.path.abspath(path)
        self._path = path
        self._makepath(os.path.join(self._path, 'home'))
        self._home_path = 'home'
        self._conf_filename = 'conf.pickle'
        self._users_filename = 'users.pickle'

    def __repr__(self):
        return "Filesystem Sage Notebook Datastore at %s"%self._path

    ##################################################################################
    # Paths
    ##################################################################################
    def _makepath(self, path):
        p = self._abspath(path)
        if not os.path.exists(p): os.makedirs(p)
        return path

    def _user_path(self, username):
        # There are weird cases, e.g., old notebook server migration
        # where username is None, and if we don't string it here,
        # saving can be broken (at a bad moment!).
        return self._makepath(os.path.join(self._home_path, str(username)))

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
        Return absolute path to filename got by joining self._path with the string file.

        OUTPUT:

            -- ``string``

        EXAMPLES::

            sage: from sagenb.storage.abstract_storage import Datastore
            sage: Datastore(tmp_dir())._abspath('foo.pickle')
            '...foo.pickle'
        """
        return os.path.join(self._path, file)
    
    ##################################################################################
    # Loading and saving basic Python objects to disk.
    # The input filename is always relative to self._path.
    ##################################################################################
    def _load(self, filename):
        return cPickle.load(open(self._abspath(filename)))

    def _save(self, obj, filename, ):
        s = cPickle.dumps(obj)
        open(self._abspath(filename), 'w').write(s)

    def _permissions(self, filename):
        f = self._abspath(filename)
        if os.path.exists(f):
            set_restrictive_permissions(f, allow_execute=False)

    ##################################################################################
    # Conversions to and from basic Python database (so that json storage will work).
    ##################################################################################
    def _basic_to_users(self, obj):
        from sagenb.notebook.user import User_from_basic
        return dict([(name, User_from_basic(basic)) for name, basic in obj])

    def _users_to_basic(self, users):
        return list(sorted([[name, U.basic()] for name, U in users.iteritems()]))

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

    ##################################################################################
    # Now we implement the API we're supposed to implement
    ##################################################################################
    
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

    def load_users(self):
        """
        OUTPUT:

            - dictionary of user info
        
        EXAMPLES::
        
            sage: from sagenb.notebook.user import User
            sage: users = {'admin':User('admin','abc','a@b.c','admin'), 'wstein':User('wstein','xyz','b@c.d','user')}
            sage: from sagenb.storage import JSONDatastore
            sage: ds = JSONDatastore(tmp_dir())
            sage: ds.save_user_data(users)
            sage: 'users.json' in os.listdir(ds._path)
            True
            sage: ds.load_user_data()
            {u'admin': admin, u'wstein': wstein}
        """
        return self._basic_to_users(self._load('users.pickle'))
    
    def save_users(self, users):
        """
        INPUT:

            - ``users`` -- dictionary mapping user names to users
        
        EXAMPLES::
        
            sage: from sagenb.notebook.user import User
            sage: users = {'admin':User('admin','abc','a@b.c','admin'), 'xyz':User('xyz','myalksjf','b@c.d','user')}
            sage: from sagenb.storage import JSONDatastore; ds = JSONDatastore(tmp_dir())
            sage: ds.save_user_data(users)
            sage: 'users.json' in os.listdir(ds._path)
            True
            sage: ds.load_user_data()
            {u'admin': admin, u'xyz': xyz}
        
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
            sage: W = Worksheet('test', 2, '', system='gap', owner='sageuser')
            sage: from sagenb.storage import FilesystemDatastore
            sage: DS = FilesystemDatastore(tmp_dir())
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
            open(self._abspath(filename),'w').write(worksheet.body())

    def load_worksheet(self, username, id_number):
        """
        Return worksheet with given id_number belonging to the given
        user.

        INPUT:

            - ``username`` -- string

            - ``id_number`` -- integer

        OUTPUT:

            - a worksheet
        """
        filename = self._worksheet_html_filename(username, id_number)
        html_file = self._abspath(filename)
        if not os.path.exists(html_file):
            # We create the worksheet
            W = self._basic_to_worksheet({'owner':username, 'id_number':id_number})
            W.clear()
            return W
        basic = self._load(self._worksheet_conf_filename(username, id_number))
        basic['owner'] = username
        basic['id_number'] = id_number
        W = self._basic_to_worksheet(basic)
        W._last_basic = basic   # cache
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

        # Remove metainformation that perhaps shouldn't be distributed
        for k in ['owner', 'ratings', 'worksheet_that_was_published', 'viewers', 'tags', 'published_id_number',
                  'collaborators', 'auto_publish']:
            if basic.has_key(k):
                del basic[k]
                
        self._save(basic, self._worksheet_conf_filename(username, id_number) + '2')
        tmp = self._abspath(self._worksheet_conf_filename(username, id_number) + '2')
        T.add(tmp, os.path.join('sage_worksheet','worksheet_conf.pickle'))
        os.unlink(tmp)

        worksheet_html = self._abspath(self._worksheet_html_filename(username, id_number))
        T.add(worksheet_html, os.path.join('sage_worksheet','worksheet.html'))

        # The following is purely for backwards compatibility with old notebook servers
        # prior to sage-4.1.2.
        worksheet_txt =  tempfile.mkstemp()[1]
        old_heading = "%s\nsystem:%s\n"%(basic['name'], basic['system'])
        open(worksheet_txt,'w').write(old_heading + open(worksheet_html).read())
        T.add(worksheet_txt,
              os.path.join('sage_worksheet','worksheet.txt'))
        os.unlink(worksheet_txt)
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
            raise RuntimeError, "unable to import worksheet"

        worksheet_txt = members[0].name
        W = self.load_worksheet(username, id_number)
        W.edit_save_old_format(T.extractfile(worksheet_txt).read())
        dir = worksheet_txt.split('/')[0]  # '/' is right, since old worksheets always unix
            
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
            open(self._abspath(self._worksheet_conf_filename(username, id_number)),'w').write(
                T.extractfile(os.path.join('sage_worksheet','worksheet_conf.pickle')).read())
        except KeyError:
            # Not a valid worksheet.  This might mean it is an old
            # worksheet from a previous version of Sage.
            return self._import_old_worksheet(username, id_number, filename)
            
        open(self._abspath(self._worksheet_html_filename(username, id_number)),'w').write(
            T.extractfile(os.path.join('sage_worksheet','worksheet.html')).read())

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
        
        return self.load_worksheet(username, id_number)
        
    def worksheets(self, username):
        """
        Return list of all the worksheets belonging to the user with
        given name.  If the given user does not exists, an empty list
        is returned.

        EXAMPLES::

        The load_user_data function must be defined in the derived class::
        
            sage: from sagenb.storage.abstract_storage import Datastore
            sage: Datastore('/tmp/ds').worksheets('foobar')
            []

            sage: from sagenb.notebook.worksheet import Worksheet
            sage: W = Worksheet('test', 2, '', system='gap', owner='sageuser')
            sage: from sagenb.storage import JSONDatastore
            sage: from sagenb.storage import FilesystemDatastore
            sage: DS = FilesystemDatastore(tmp_dir())
            sage: DS.save_worksheet(W)
            sage: DS.worksheets('sageuser')
            [sageuser/2: [Cell 0; in=, out=]]
        """
        path = self._abspath(self._user_path(username))
        if not os.path.exists(path): return []
        v = []
        for id_number in os.listdir(path):
            if id_number.isdigit():
                try:
                    v.append(self.load_worksheet(username, int(id_number)))
                except Exception, msg:
                    print "Warning: problem loading %s/%s: %s"%(username, id_number, msg)
        return v

    def delete(self):
        """
        Delete all files associated with this datastore.  Dangerous!
        This is only here because it is useful for doctesting.
        """
        import shutil
        shutil.rmtree(self._path, ignore_errors=True)



###################################################################################
# 
# Why not use JSON, YAML, or XML??
#
# I experimented with using these, but they are 10-100 times slower, and there is
# no real benefit.   More precisely, the time for dumping/loading a worksheet basic
# datastructure in each of the following is given below.  XML is also very bad
# compared to cPickle. 
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
###################################################################################
