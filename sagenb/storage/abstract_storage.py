"""
Sage Notebook Storage Abstraction Layer

"""

import os

class Datastore(object):
    """
    The Sage Notebook storage abstraction layer abstract base class.
    Each storage abstraction layer derives from this.
    """
    def __init__(self, path):
        self._path = path
        if not os.path.exists(path):
            os.makedirs(path)

    def path(self):
        """
        Return path where data for this datastore is located.

        OUTPUT:

            -- ``string``
        """
        return self._path

    def filename(self, file):
        """
        Return filename got by joining self.path() with the string file.

        OUTPUT:

            -- ``string``
        """
        return os.path.join(self._path, file)
    
    def load_user_data(self):
        """
        Return dictionary of 'username':user pairs, where the keys are the
        usernames as strings, and the values are User objects.

        OUTPUT:

            -- ``dict``
        """
        raise NotImplementedError

    def save_user_data(self, users):
        """
        Given a dictionary of 'username':user pairs, save this dictionary
        in the data store.

        INPUT:

            - ``users`` -- dictionary
        """
        raise NotImplementedError

    def load_server_data(self):
        """
        Return the ServerConfiguration object that is stored in this
        datastore.

        OUTPUT:

            - ``ServerConfiguration``
        """
        raise NotImplementedError
    
    def save_server_data(self, server):
        """
        Given a ServerConfiguration object, store it in this datastore.

        INPUT:

            - ``server`` -- a ServerConfiguration object
        
        """
        raise NotImplementedError

    def load_worksheet(self, username, id_number):
        """
        Given a username (as a string), and a number (a nonnegative
        integer), return the worksheet with that number belonging to
        that user.

        INPUT:

            - ``username`` -- string
            
            - ``id_number`` -- nonnegative integer
        """
        raise NotImplementedError

    def save_worksheet(self, worksheet):
        """
        Given a worksheet, save it in this datastore.

        INPUT:

            - ``worksheet`` -- a Sage worksheet
        """
        raise NotImplementedError

    def worksheets(self, username):
        """
        Return list of pairs (id_number, title) giving the id numbers
        and titles of all worksheets belonging to the user with given
        name.
        """
        raise NotImplementedError
