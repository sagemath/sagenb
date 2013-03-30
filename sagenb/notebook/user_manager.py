import user
import crypt
import hashlib

SALT = 'aa'

class UserManager(object):
    def __init__(self, accounts=False):
        """
        EXAMPLES:
            sage: from sagenb.notebook.user_manager import SimpleUserManager
            sage: U = SimpleUserManager()
            sage: U == loads(dumps(U))
            True
        """
        self._users = {}
        self._accounts = accounts

    def __eq__(self, other):
        """
        EXAMPLES:
            sage: from sagenb.notebook.user_manager import SimpleUserManager
            sage: U1 = SimpleUserManager()
            sage: U2 = SimpleUserManager(accounts=False)
            sage: U1 == U2
            False
            sage: U2.set_accounts(True)
            sage: U1 == U2
            True
            sage: U1.create_default_users('password')
            sage: U1 == U2
            False
            sage: U2.create_default_users('password')
            sage: U1 == U2
            True
        """
        if other.__class__ is not self.__class__:
            return False
        if self._users != other._users:
            return False
        if self._accounts != other._accounts:
            return False
        return True

    def user_list(self):
        """
        Returns a sorted list of the users that have logged into the notebook.

        EXAMPLES:
            sage: from sagenb.notebook.user_manager import SimpleUserManager
            sage: U = SimpleUserManager()
            sage: U.create_default_users('password')
            sage: U.user_list()
            [_sage_, admin, guest, pub]
        """
        user_list = list(self.users().itervalues())
        user_list.sort(key=lambda x: str(x))
        return user_list

    def users(self):
        """
        Returns a dictionary whose keys are the usernames and whose values are the
        corresponding users.  

        Note that these are just the users that have logged into the notebook and are
        note necessarily all of the valid users.

        EXAMPLES:
            sage: from sagenb.notebook.user_manager import SimpleUserManager
            sage: U = SimpleUserManager()
            sage: U.create_default_users('password')
            sage: list(sorted(U.users().items()))
            [('_sage_', _sage_), ('admin', admin), ('guest', guest), ('pub', pub)]
        """
        return self._users

    def user(self, username):
        """
        Returns a user object for the user username.

        This first checks to see if a user with username has been seen before and is in
        the users dictionary.  If such a user is found, then that object is returned.  
        Otherwise, the underscore _user method is tried.  This is the method that subclasses
        should override to provide custom user functionality.

        EXAMPLES:
            sage: from sagenb.notebook.user_manager import SimpleUserManager
            sage: U = SimpleUserManager()
            sage: U.create_default_users('password')
            sage: U.user('pub')
            pub

        TESTS:
            sage: U.user('william')
            Traceback (most recent call last):
            ...
            KeyError: "no user 'william'"

            sage: U.user('hello/')
            Traceback (most recent call last):
            ...
            ValueError: no user 'hello/'
        """
        if not isinstance(username, (str, unicode)) or '/' in username:
            raise ValueError, "no user '%s'"%username
        if username in self.users():
            return self.users()[username]

        try:
            return self._user(username)
        except AttributeError:
            pass

        raise KeyError, "no user '%s'"%username

    def valid_login_names(self):
        """
        Return a list of users that can log in.
        """
        return [x for x in self.usernames() if not x in ['guest', '_sage_', 'pub']]

    def user_exists(self, username):
        """
        Returns True if and only if the user \emph{username} has signed in before.

        Note that this should not be used to check to see if a username is valid since 
        there are UserManager backends (such as LDAP) where we could have many valid usernames, but
        not all of them will have actually logged into the notebook.

        EXAMPLES:
            sage: from sagenb.notebook.user_manager import SimpleUserManager
            sage: U = SimpleUserManager()
            sage: U.create_default_users('password')
            sage: U.user_exists('admin')
            True
        """
        return username in self.users()

    def usernames(self):
        """
        EXAMPLES:
            sage: from sagenb.notebook.user_manager import SimpleUserManager
            sage: U = SimpleUserManager()
            sage: U.create_default_users('password')
            sage: u = U.usernames(); u.sort(); u
            ['_sage_', 'admin', 'guest', 'pub']
        """
        return self.users().keys()

    def user_is_admin(self, username):
        """
        Returns True if the user username is an admin user.

        EXAMPLES:
            sage: from sagenb.notebook.user_manager import SimpleUserManager
            sage: U = SimpleUserManager()
            sage: U.create_default_users('password')
            sage: U.user_is_admin('admin')
            True
            sage: U.user_is_admin('pub')
            False
        """
        try:
            return self.user(username).is_admin()
        except KeyError:
            return False

    def user_is_guest(self, username):
        """
        Returns True if the user username is an gues user.

        EXAMPLES:
            sage: from sagenb.notebook.user_manager import SimpleUserManager
            sage: U = SimpleUserManager()
            sage: U.create_default_users('password')
            sage: U.user_is_guest('guest')
            True
            sage: U.user_is_guest('admin')
            False
        """
        try:
            return self.user(username).is_guest()
        except KeyError:
            return False

    def create_default_users(self, passwd, verbose=False):
        """
        Creates the default users (pub, _sage_, guest, and admin) in the current
        notebook.

        EXAMPLES:
            sage: from sagenb.notebook.user_manager import SimpleUserManager
            sage: U = SimpleUserManager()
            sage: U.create_default_users('password')
            sage: U.user_list()
            [_sage_, admin, guest, pub]

        """
        if verbose:
            print "Creating default users."
        self.add_user('pub', '', '', account_type='user', force=True)
        self.add_user('_sage_', '', '', account_type='user', force=True)
        self.add_user('guest', '', '', account_type='guest', force=True)
        self.add_user('admin', passwd, '', account_type='admin', force=True)

    def delete_user(self, username):
        """
        Deletes the user username from the users dictionary.

        EXAMPLES:
            sage: from sagenb.notebook.user_manager import SimpleUserManager
            sage: U = SimpleUserManager()
            sage: U.create_default_users('password')
            sage: U.user_list()
            [_sage_, admin, guest, pub]
            sage: U.delete_user('pub')
            sage: U.user_list()
            [_sage_, admin, guest]
        """
        us = self.users()
        if username in us:
            del us[username]

    def user_conf(self, username):
        """        
        Returns the configuration dictionary for the user username.

        EXAMPLES:
            sage: from sagenb.notebook.user_manager import SimpleUserManager
            sage: U = SimpleUserManager()
            sage: U.create_default_users('password')
            sage: U.user('admin').conf()
            Configuration: {}

        """
        return self.user(username).conf()

    def set_accounts(self, value):
        """
        Set whether or not accounts can be created for this notebook.

        EXAMPLES:
            sage: from sagenb.notebook.user_manager import SimpleUserManager
            sage: U = SimpleUserManager()
            sage: U.create_default_users('password')
            sage: U.get_accounts()
            True 
            sage: U.set_accounts(False)
            sage: U.get_accounts()
            False 
        """
        if value not in [True, False]:
            raise ValueError, "accounts must be True or False"
        self._accounts = value

    def get_accounts(self):
        """
        Get whether or not accounts can be created for this notebook.

        EXAMPLES:
            sage: from sagenb.notebook.user_manager import SimpleUserManager
            sage: U = SimpleUserManager()
            sage: U.create_default_users('password')
            sage: U.get_accounts()
            True 
            sage: U.set_accounts(False)
            sage: U.get_accounts()
            False 
        """
        return self._accounts


    def add_user(self, username, password, email, account_type="user", external_auth=None, force=False):
        """
        Adds a new user to the user dictionary.

        INPUT:
            username -- the username
            password -- the password
            email -- the email address
            account_type -- one of 'user', 'admin', or 'guest'

        EXAMPLES:
            sage: from sagenb.notebook.user_manager import SimpleUserManager
            sage: U = SimpleUserManager()
            sage: U.add_user('william', 'password', 'email@address.com', account_type='admin')
            sage: U.set_accounts(True)
            sage: U.add_user('william', 'password', 'email@address.com', account_type='admin')
            WARNING: User 'william' already exists -- and is now being replaced.
            sage: U.user('william')
            william
        """
        if not self.get_accounts() and not force:
            raise ValueError, "creating new accounts disabled."

        us = self.users()
        if us.has_key(username):
            print "WARNING: User '%s' already exists -- and is now being replaced."%username
        U = user.User(username, password, email, account_type, external_auth)
        us[username] = U
        self.set_password(username, password)

    def add_user_object(self, user, force=False):
        """
        Adds a new user to the user dictionary.

        INPUT:
            user -- a User object 

        EXAMPLES:
            sage: from sagenb.notebook.user_manager import SimpleUserManager
            sage: from sagenb.notebook.user import User 
            sage: U = SimpleUserManager()
            sage: user = User('william', 'password', 'email@address.com', account_type='admin')
            sage: U.add_user_object(user)
            sage: U.set_accounts(True)
            sage: U.add_user_object(user)
            WARNING: User 'william' already exists -- and is now being replaced.
            sage: U.user('william')
            william
        """
        if not self.get_accounts() and not force:
            raise ValueError, "creating new accounts disabled."
        us = self.users()
        if us.has_key(user.username()):
            print "WARNING: User '%s' already exists -- and is now being replaced."%user.username()

        self._users[user.username()] = user 

class SimpleUserManager(UserManager):
    def __init__(self, accounts=True, conf=None):
        """
        EXAMPLES:
            sage: from sagenb.notebook.user_manager import SimpleUserManager
            sage: U = SimpleUserManager()
            sage: U == loads(dumps(U))
            True

        """
        self._passwords = {}
        UserManager.__init__(self, accounts=accounts)
        self._conf = {'accounts': accounts} if conf is None else conf

    def copy_password(self, username, other_username):
        """
        Sets the password of user to be the password of other_user.

        EXAMPLES:
            sage: from sagenb.notebook.user_manager import SimpleUserManager
            sage: UM = SimpleUserManager(accounts=True)
            sage: UM.create_default_users('passpass')
            sage: UM.add_user('william', 'password', 'email@address.com')
            sage: UM.check_password('admin','passpass')
            True
            sage: UM.check_password('william','password')
            True
            sage: UM.copy_password('william', 'admin')
            sage: UM.check_password('william','passpass')
            True

        """
        O = self.user(other_username)
        passwd = O.password()
        self.set_password(username, passwd, encrypt=False)

    def _user(self, username):
        """
        Returns a User object with username username.
        
        This method is called by UserManager.user if it did not find a user
        with username username in the user dictionary.  This method will
        automatically create users for the usernames 'pub', '_sage_',
        'admin', and 'guest'.

        EXAMPLES:
            sage: from sagenb.notebook.user_manager import SimpleUserManager
            sage: U = SimpleUserManager()
            sage: U.user('guest')
            guest
            sage: U.user('pub')
            pub
            sage: U.user('admin')
            admin

        """
        if username in ['pub', '_sage_']:
            self.add_user(username, '', '', account_type='user', force=True)
            return self.users()[username]
        elif username == 'admin':
            self.add_user(username, '', '', account_type='admin', force=True)
            return self.users()[username]
        elif username == 'guest':
            self.add_user('guest', '', '', account_type='guest', force=True)
            return self.users()[username]
        raise KeyError("no user '{0}'".format(username))

        
    def set_password(self, username, new_password, encrypt = True):
        """
        EXAMPLES:
            sage: from sagenb.notebook.user_manager import SimpleUserManager
            sage: U = SimpleUserManager()
            sage: U.create_default_users('passpass')
            sage: U.check_password('admin','passpass')
            True
            sage: U.set_password('admin', 'password')
            sage: U.check_password('admin','password')
            True
            sage: U.set_password('admin', 'test'); U.check_password('admin','test')
            True
            sage: U.set_password('admin', 'test', encrypt=False); U.password('admin')
            'test'
        """
        if encrypt:
            salt = user.generate_salt()
            new_password = 'sha256${0}${1}'.format(salt,
                                                   hashlib.sha256(salt + new_password).hexdigest())
        self._passwords[username] = new_password
        # need to make sure password in the user object is synced
        # for compatibility only the user object data is stored in the 'users.pickle'
        self.user(username).set_password(new_password, encrypt = False)

    def passwords(self):
        """
        Return a dictionary whose keys are the usernames and whose values are
        the encrypted passwords associated to the user.

        EXAMPLES:
            sage: from sagenb.notebook.user_manager import SimpleUserManager
            sage: U = SimpleUserManager()
            sage: U.create_default_users('passpass')
            sage: list(sorted(U.passwords().items())) #random 
            [('_sage_', ''),
             ('admin', ''),
             ('guest', ''),
             ('pub', '')]
            sage: len(list(sorted(U.passwords().items())))
            4

        """
        return dict([(user.username(), self.password(user.username())) for user in self.user_list()])

    def password(self, username):
        """
        Return the stored password for username. Might be encrypted.
        EXAMPLES:
            sage: from sagenb.notebook.user_manager import SimpleUserManager
            sage: U = SimpleUserManager()
            sage: U.create_default_users('passpass')
            sage: U.check_password('admin','passpass')
            True
        """
        return self._passwords.get(username, None)
        
    def check_password(self, username, password):
        # the empty password is always false
        if username == "pub" or password == '':
            return False
        user_password = self.password(username)
        if user_password is None and not self.user(username).is_external():
            print "User %s has None password"%username
            return False
        if user_password.find('$') == -1:
            if user_password == crypt.crypt(password, user.SALT):
                self.set_password(username, password)
                return True
            else:
                return False
        else:
            salt, user_password = user_password.split('$')[1:]
            if hashlib.sha256(salt + password).hexdigest() == user_password:
                return True
        try:
            return self._check_password(username, password)
        except AttributeError:
            return False;

    def get_accounts(self):
        # need to use notebook's conf because those are already serialized
        # fix when user_manager is serialized
        return self._conf['accounts']

    def set_accounts(self, value):
        if value not in [True, False]:
            raise ValueError, "accounts must be True or False"
        self._accounts = value
        self._conf['accounts'] = value



class ExtAuthUserManager(SimpleUserManager):
    def __init__(self, accounts=None, conf=None):
        SimpleUserManager.__init__(self, accounts=accounts, conf=conf)

        from auth import LdapAuth

        # keys must match to a T_BOOL option in server_config.py
        # so we can turn this auth method on/off
        self._auth_methods = {
            'auth_ldap': LdapAuth(self._conf),
        }

    def _user(self, username):
        """
        Check all auth methods that are enabled in the notebook's config.
        If a valid username is found, a new User object will be created.
        """
        for a in self._auth_methods:
            if self._conf[a]:
                u = self._auth_methods[a].check_user(username)
                if u:
                    try:
                        email = self._auth_methods[a].get_attrib(username, 'email')
                    except KeyError:
                        email = None

                    self.add_user(username, password='', email=email, account_type='user', external_auth=a, force=True)
                    return self.users()[username]

        raise KeyError, "no user '%s'"%username

    def _check_password(self, username, password):
        """
        Find auth method for user 'username' and
        use that auth method to check username/password combination.
        """
        u = self.users()[username]
        if u.is_external():
            a = u.external_auth()
        else:
            return False

        if self._conf[a]:
            return self._auth_methods[a].check_password(username, password)

        return False

class OpenIDUserManager(ExtAuthUserManager):
    def __init__(self, accounts=True, conf=None):
        """
        Creates an user_manager that supports OpenID identities
        EXAMPLES:
            sage: from sagenb.notebook.user_manager import OpenIDUserManager 
            sage: UM = OpenIDUserManager()
            sage: UM.create_default_users('passpass')
            sage: UM.check_password('admin','passpass')
            True
        """
        ExtAuthUserManager.__init__(self, accounts=accounts, conf=conf)
        self._openid = {} 

    def load(self, datastore):
        """
        Loads required data from a given datastore.
        """
        self._openid = datastore.load_openid()

    def save(self, datastore):
        """
        Saves persistent data to a given datastore.
        """
        datastore.save_openid(self._openid)

    def get_username_from_openid(self, identity_url):
        """
        Return the username corresponding ot a given identity_url
        EXAMPLES:
            sage: from sagenb.notebook.user_manager import OpenIDUserManager
            sage: UM = OpenIDUserManager()
            sage: UM.create_default_users('passpass')
            sage: UM.create_new_openid('https://www.google.com/accounts/o8/id?id=AItdaWgzjV1HJTa552549o1csTDdfeH6_bPxF14', 'thedude')
            sage: UM.get_username_from_openid('https://www.google.com/accounts/o8/id?id=AItdaWgzjV1HJTa552549o1csTDdfeH6_bPxF14')
            'thedude' 
        """
        if not self._conf['openid']:
            raise RuntimeError

        try:
            return self._openid[identity_url]
        except KeyError:
            raise KeyError, "no openID identity '%s'" % identity_url

    def create_new_openid(self, identity_url, username):
        """
        Create a new identity_url -- username pairing
        EXAMPLES:
            sage: from sagenb.notebook.user_manager import OpenIDUserManager
            sage: UM = OpenIDUserManager()
            sage: UM.create_default_users('passpass')
            sage: UM.create_new_openid('https://www.google.com/accounts/o8/id?id=AItdaWgzjV1HJTa552549o1csTDdfeH6_bPxF14', 'thedude')
            sage: UM.get_username_from_openid('https://www.google.com/accounts/o8/id?id=AItdaWgzjV1HJTa552549o1csTDdfeH6_bPxF14')
            'thedude'
        """
        if not self._conf['openid']:
            raise RuntimeError
        self._openid[identity_url] = username

    def get_user_from_openid(self, identity_url):
        """
        Return the user object corresponding ot a given identity_url
        """
        if not self._conf['openid']:
            raise RuntimeError
        return self.user(self.get_username_from_openid(identity_url)) 
