"""
Sage Notebook Storage Abstraction Layer
"""

import os

class Datastore(object):
    """
    The Sage Notebook storage abstraction layer abstract base class.
    Each storage abstraction layer derives from this.
    """
    def __repr__(self):
        """
        String representation of this abstract datastore.

        EXAMPLES::

            sage: from sagenb.storage.abstract_storage import Datastore
            sage: Datastore('/tmp/ds').__repr__()
            'Abstract Datastore'        
        """
        return "Abstract Datastore"

    def load_server_conf(self):
        raise NotImplementedError
    
    def save_server_conf(self, server_conf):
        raise NotImplementedError

    def load_users(self):
        """
        OUTPUT:

            - dictionary of user info
        """
        raise NotImplementedError

    
    def save_users(self, users):
        """
        INPUT:

            - ``users`` -- dictionary mapping user names to users
        """
        raise NotImplementedError

    def load_user_history(self, username):
        """
        Return the history log for the given user.

        INPUT:

            - ``username`` -- string

        OUTPUT:

            - list of strings
        """
        raise NotImplementedError
    
    def save_user_history(self, username, history):
        """
        Save the history log (a list of strings) for the given user.

        INPUT:

            - ``username`` -- string

            - ``history`` -- list of strings
        """
        raise NotImplementedError        
        
    def save_worksheet(self, worksheet, conf_only=False):
        """
        INPUT:

            - ``worksheet`` -- a Sage worksheet

            - ``conf_only`` -- default: False; if True, only save
              the config file, not the actual body of the worksheet      
        """
        raise NotImplementedError        

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
        raise NotImplementedError        


    def export_worksheet(self, username, id_number, filename, title):
        """
        Export the worksheet with given username and id_number to the
        given filename (e.g., 'worksheet.sws').

        INPUT:
    
            - ``title`` - title to use for the exported worksheet (if
               None, just use current title)
        """
        raise NotImplementedError        

    def import_worksheet(self, username, id_number, filename):
        """
        Input the worksheet username/id_number from the file with
        given filename.
        """
        raise NotImplementedError        
        
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
        raise NotImplementedError        

        
    def delete(self):
        """
        Delete all files associated with this datastore.  Dangerous!
        This is only here because it is useful for doctesting.
        """
        raise NotImplementedError        
