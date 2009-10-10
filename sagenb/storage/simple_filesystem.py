"""
A Simple Filesystem-based Sage Notebook Datastore

Here is the filesystem layout for this datastore. 

::

    sage_notebook.sagenb
         conf.txt
         users.txt
         home/
             username0/
                history.txt
                id_number0/
                    worksheet.html
                    worksheet_conf.txt
                    cells/
                    data/
                    snapshots/
                id_number1/
                    worksheet.html
                    worksheet_conf.txt
                    cells/
                    data/
                    snapshots/
                ...
             username1/
             ...
             
"""

import json, os

from abstract_storage import Datastore

class SimpleFileDatastore(object):
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
        self._conf_filename = 'conf.txt'
        self._users_filename = 'users.txt'

    def __repr__(self):
        return "Simple Filesystem-based Sage Notebook Datastore at %s"%self._path

    ##################################################################################
    # Paths
    ##################################################################################
    def _makepath(self, path):
        p = self._abspath(path)
        if not os.path.exists(p): os.makedirs(p)
        return path

    def _user_path(self, username):
        return self._makepath(os.path.join(self._home_path, username))

    def _worksheet_path(self, username, id_number=None):
        if id_number is None:
            return self._makepath(self._user_path(username))
        return self._makepath(os.path.join(self._user_path(username), str(id_number)))

    def _worksheet_conf_filename(self, username, id_number):
        return os.path.join(self._worksheet_path(username, id_number), 'worksheet_conf.txt')

    def _worksheet_html_filename(self, username, id_number):
        return os.path.join(self._worksheet_path(username, id_number), 'worksheet.html')

    def _history_filename(self, username):
        return os.path.join(self._user_path(username), 'history.txt')

    def _abspath(self, file):
        """
        Return absolute path to filename got by joining self._path with the string file.

        OUTPUT:

            -- ``string``

        EXAMPLES::

            sage: from sagenb.storage.abstract_storage import Datastore
            sage: Datastore(tmp_dir())._abspath('foo.txt')
            '...foo.txt'
        """
        return os.path.join(self._path, file)
    
    ##################################################################################
    # Loading and saving basic Python objects to disk.
    # The input filename is always relative to self._path.
    ##################################################################################
    def _load(self, filename):
        return json.load(open(self._abspath(filename)))

    def _save(self, obj, filename):
        json.dump(obj, open(self._abspath(filename),'w'), indent=4)

    ##################################################################################
    # Conversions to and from basic Python database (so that json storage will work).
    ##################################################################################
    def _basic_to_users(self, obj):
        from sagenb.notebook.user import User_from_basic
        return dict([(name, User_from_basic(basic)) for name, basic in obj])

    def _users_to_basic(self, users):
        return list(sorted([(name, U.basic()) for name, U in users.iteritems()]))

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
        return self._basic_to_server_conf(self._load('conf.txt'))
    
    def save_server_conf(self, server_conf):
        """
        INPUT:

            - ``server`` --
        """
        self._save(self._server_conf_to_basic(server_conf), 'conf.txt')

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
        return self._basic_to_users(self._load('users.txt'))
    
    def save_users(self, users):
        """
        INPUT:

            - ``users`` -- user dictionary object
        
        EXAMPLES::
        
            sage: from sagenb.notebook.user import User
            sage: users = {'admin':User('admin','abc','a@b.c','admin'), 'xyz':User('xyz','myalksjf','b@c.d','user')}
            sage: from sagenb.storage import JSONDatastore; ds = JSONDatastore(tmp_dir())
            sage: ds.save_user_data(users)
            sage: 'users.json' in os.listdir(ds._path)
            True
            sage: ds.load_user_data()
            {u'admin': admin, u'xyz': xyz}
        
        INPUT:

            - ``users`` -- dictionary mapping user names to users
        """
        self._save(self._users_to_basic(users), 'users.txt')

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
        self._save(history, self._history_filename(username))
        
    def save_worksheet(self, worksheet):
        """
        INPUT:

            - ``worksheet`` -- a Sage worksheet

        EXAMPLES::
        
            sage: from sagenb.notebook.worksheet import Worksheet
            sage: W = Worksheet('test', 2, '', system='gap', owner='sageuser')
            sage: from sagenb.storage import SimpleFileDatastore
            sage: DS = SimpleFileDatastore(tmp_dir())
            sage: DS.save_worksheet(W)
        """
        username = worksheet.owner(); id_number = worksheet.id_number()
        self._save(self._worksheet_to_basic(worksheet),
                   self._worksheet_conf_filename(username, id_number))
        if worksheet.body_is_loaded():
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

        EXAMPLES::
        """
        filename = self._worksheet_html_filename(username, id_number)
        html_file = self._abspath(filename)
        if not os.path.exists(html_file):
            # We create the worksheet
            W = self._basic_to_worksheet({'owner':username, 'id_number':id_number})
            W.clear()
            return W
        return self._basic_to_worksheet(self._load(self._worksheet_conf_filename(username, id_number)))

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
            sage: from sagenb.storage import SimpleFileDatastore
            sage: DS = SimpleFileDatastore(tmp_dir())
            sage: DS.save_worksheet(W)
            sage: DS.worksheets('sageuser')
            [sageuser/2: [Cell 0; in=, out=]]
        """
        path = self._abspath(self._user_path(username))
        if not os.path.exists(path): return []
        return [self.load_worksheet(username, int(id_number)) for id_number
                in os.listdir(path) if id_number.isdigit()]

    def delete(self):
        """
        Delete all files associated with this datastore.  Dangerous!
        """
        import shutil
        shutil.rmtree(self._path, ignore_errors=True)
