"""
Pickle-based implementation of storage abstraction layer.

"""
import cPickle

from abstract_storage import Datastore

class PickleDatastore(Datastore):
    def _save(self, file, obj):
        cPickle.dump(obj, open(self.filename(file),'w'), protocol=2)

    def _load(self, file):
        return cPickle.load(open(self.filename(file)))
              
    def load_user_data(self):
        return self._load('users.pickle')

    def save_user_data(self, users):
        self._save('users.pickle', users)
    
    def load_server_data(self):
        return self._load('server.pickle')        

    def save_server_data(self, server):
        self._save('server.pickle', server)

    def load_worksheet(self, username, number):
        raise NotImplementedError
        
    def save_worksheet(self, worksheet):
        raise NotImplementedError
    
