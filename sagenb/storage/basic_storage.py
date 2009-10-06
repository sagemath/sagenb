"""
Sage Notebook Storage Abstraction Layer

   - ``PickleDatastore`` --

   - ``JSONDatastore`` --

   - ``BasicPickleDatastore`` -- 

"""

from abstract_storage import Datastore
from pickle_storage import PickleDatastore

import json, cPickle

class AbstractBasicDatastore(Datastore):
    def basic_to_users(self, obj):
        from sagenb.notebook.user import User_from_basic
        return dict([(name, User_from_basic(basic)) for name, basic in obj])

    def users_to_basic(self, users):
        return [(name, U.basic()) for name, U in users.iteritems()]

    def basic_to_server(self, obj):
        from sagenb.notebook.server_conf import ServerConfiguration_from_basic
        return ServerConfiguration_from_basic(obj)

    def server_to_basic(self, server):
        return server.basic()

    def basic_to_worksheet(self, obj):
        """
        Given a basic Python object obj, return corresponding worksheet.
        """

    def worksheet_to_basic(self, worksheet):
        """
        Given a worksheet, create a corresponding basic Python object
        that completely defines that worksheet.
        """
        
        


class JSONDatastore(AbstractBasicDatastore):
    def __init__(self, path, indent=4):
        AbstractBasicDatastore.__init__(self, path)
        self._indent = indent

    def _load(self, file):
        return json.load(open(self.filename(file)))

    def _save(self, file, obj):
        json.dump(obj, open(self.filename(file),'w'), indent=self._indent)
        
    def load_user_data(self):
        """
        EXAMPLES::
        
            sage: from sagenb.notebook.user import User
            sage: users = {'admin':User('admin','abc','a@b.c','admin'), 'wstein':User('wstein','xyz','b@c.d','user')}
            sage: from sagenb.storage import JSONDatastore
            sage: ds = JSONDatastore(tmp_dir())
            sage: ds.save_user_data(users)
            sage: 'users.json' in os.listdir(ds.path())
            True
            sage: ds.load_user_data()
            {u'admin': admin, u'wstein': wstein}
        """
        return self.basic_to_users(self._load('users.json'))
    
    def save_user_data(self, users):
        """
        EXAMPLES::
        
            sage: from sagenb.notebook.user import User
            sage: users = {'admin':User('admin','abc','a@b.c','admin'), 'xyz':User('xyz','myalksjf','b@c.d','user')}
            sage: from sagenb.storage import JSONDatastore; ds = JSONDatastore(tmp_dir())
            sage: ds.save_user_data(users)
            sage: 'users.json' in os.listdir(ds.path())
            True
            sage: ds.load_user_data()
            {u'admin': admin, u'xyz': xyz}
        
        INPUT:

            - ``users`` -- dictionary mapping user names to users
        """
        self._save('users.json', self.users_to_basic(users))

    def load_server_data(self):
        return self.basic_to_server(self._load('server.json'))
    
    def save_server_data(self, server):
        """
        INPUT:

            - ``server`` --
        """
        self._save('server.json', self.server_to_basic(server))


class BasicPickleDatastore(PickleDatastore, AbstractBasicDatastore):
    """
    Store all data associated to a Sage notebook as basic Python data
    structures.
    """
    def load_user_data(self):
        return self.basic_to_users(self._load('users.pickle'))
    
    def save_user_data(self, users):
        """
        INPUT:

            - ``users`` -- dictionary mapping user names to users
        """
        self._save('users.pickle', self.users_to_basic(users))

    def load_server_data(self):
        return self.basic_to_server(self._load('server.pickle'))
    
    def save_server_data(self, server):
        """
        INPUT:

            - ``server`` -- ?
        """
        self._save('server.pickle', self.server_to_basic(server))
        
    
    
