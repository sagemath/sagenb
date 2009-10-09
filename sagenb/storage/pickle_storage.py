"""
Pickle-based implementation of storage abstraction layer.

"""
import cPickle

from abstract_storage import Datastore, WorksheetHTML

class PickleDatastore(WorksheetHTML, Datastore):
    """
    This is a simple non-portable pickle datastore.  It is only for
    testing and reference purposes.  It would be a very bad idea to
    use in practice because it results in notebooks that can't be
    easily upgraded when code is refactored.
    """
    def __init__(self, path='pickle'):
        Datastore.__init__(self, path)

    def __repr__(self):
        return "Sage Notebook Non-portable Pickle Datastore at %s"%self.path()
    
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

    def worksheet_filename(self, username, id_number):
        return self.worksheet_filename_base(username,id_number)+'-conf.pickle'

    def _load_worksheet(self, username, id_number):
        """
        Save to a pickle the metadata for worksheet with given
        id_number owned by given user.

        INPUT:

            - ``username`` -- string

            - ``id_number`` -- integer

        OUTPUT:

            - empty worksheet with metadata set
        """
        W = self._load(self.worksheet_conf_filename(username, id_number))
        
    def _save_worksheet(self, worksheet):
        """
        Save metadata for worksheet.

        INPUT:

            - worksheet
        """
        username = worksheet.owner(); id_number = worksheet.id_number()
        self._save(self.worksheet_filename(username, id_number), worksheet)
    
