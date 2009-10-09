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

    def load_user_data(self):
        """
        Return dictionary of 'username':user pairs, where the keys are the
        usernames as strings, and the values are User objects.

        OUTPUT:

            -- ``dict``

        EXAMPLES::

        The load_user_data function must be defined in the derived class::
        
            sage: from sagenb.storage.abstract_storage import Datastore
            sage: Datastore('/tmp/ds').load_user_data()
            Traceback (most recent call last):
            ...
            NotImplementedError
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

    def load_user_history(self, username):
        """
        Return the history of input commands for the given username.

        INPUT:

            - ``username`` -- string
        """
        raise NotImplementedError
    
    def save_user_history(self, username, history):
        """
        Save the given history of input commands for the given username.

        INPUT:

            - ``username`` -- string

            - ``history`` -- ??? TODO ???
        """
        raise NotImplementedError

    def load_server_data(self):
        """
        Return the ServerConfiguration object that is stored in this
        datastore.

        OUTPUT:

            - ``ServerConfiguration``

        EXAMPLES::

        The load_server_data function must be defined in the derived class::
        
            sage: from sagenb.storage.abstract_storage import Datastore
            sage: Datastore('/tmp/ds').load_server_data()
            Traceback (most recent call last):
            ...
            NotImplementedError
        """
        raise NotImplementedError
    
    def save_server_data(self, server):
        """
        Given a ServerConfiguration object, store it in this datastore.

        INPUT:

            - ``server`` -- a ServerConfiguration object
        

        EXAMPLES::

        The save_server_data function must be defined in the derived class::
        
            sage: from sagenb.storage.abstract_storage import Datastore
            sage: Datastore('/tmp/ds').save_server_data()
            Traceback (most recent call last):
            ...
            NotImplementedError
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

        EXAMPLES::

        The load_worksheet function must be defined in the derived class::
        
            sage: from sagenb.storage.abstract_storage import Datastore
            sage: Datastore('/tmp/ds').load_worksheet()
            Traceback (most recent call last):
            ...
            NotImplementedError
        """
        raise NotImplementedError

    def save_worksheet(self, worksheet):
        """
        Given a worksheet, save it in this datastore.

        INPUT:

            - ``worksheet`` -- a Sage worksheet

        EXAMPLES::

        The save_worksheet function must be defined in the derived class::
        
            sage: from sagenb.storage.abstract_storage import Datastore
            sage: Datastore('/tmp/ds').save_worksheet()
            Traceback (most recent call last):
            ...
            NotImplementedError
        """
        raise NotImplementedError

    def worksheets(self, username):
        """
        Return list of the worksheets belonging to the user with given
        name.  If the given user does not exists, an empty list is
        returned.

        EXAMPLES::

        The load_user_data function must be defined in the derived class::
        
            sage: from sagenb.storage.abstract_storage import Datastore
            sage: Datastore('/tmp/ds').worksheets('foobar')
            []

            sage: from sagenb.notebook.worksheet import Worksheet
            sage: W = Worksheet('test', 2, '', system='gap', owner='sageuser')
            sage: from sagenb.storage import JSONDatastore
            sage: DS = JSONDatastore(tmp_dir())
            sage: DS.save_worksheet(W)
            sage: DS.worksheets('sageuser')
            [sageuser/2: [Cell 0; in=, out=]]
        """
        path = os.path.join(self.path(), self.worksheet_path(), username)
        if not os.path.exists(path):
            return []
        return [self.load_worksheet(username, int(id_number)) for
                id_number in os.listdir(path)]

class WorksheetHTML:
    """
    Abstract base class that implements functionality for storing the
    worksheet body (but not its metdata) as an html file.

    A Datastore that derives from this only has to implement the
    _load_worksheet and _save_worksheet methods, which save and
    load the metadata associated to a worksheet.
    """
    def _load_worksheet(self, username, id_number):
        """
        Save metadata for worksheet with given id_number owned by
        given user.

        INPUT:

            - ``username`` -- string

            - ``id_number`` -- integer

        OUTPUT:

            - empty worksheet with metadata set
        """
        raise NotImplementedError

    def _save_worksheet(self, worksheet):
        """
        Save metadata for worksheet.

        INPUT:

            - worksheet
        """
        raise NotImplementedError

    def worksheet_html_filename(self, username, id_number):
        return self.worksheet_filename_base(username,id_number)+'.html'

    def load_worksheet(self, username, id_number):
        W = self._load_worksheet(username, id_number)
        worksheet_html = self.filename(self.worksheet_html_filename(username, id_number))
        W.set_body(open(worksheet_html).read())
        return W
        
    def save_worksheet(self, worksheet):
        self._save_worksheet(worksheet)
        username = worksheet.owner(); id_number = worksheet.id_number()
        worksheet_html = self.filename(self.worksheet_html_filename(username, id_number))        
        open(worksheet_html,'w').write(worksheet.body())

