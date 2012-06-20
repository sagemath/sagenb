class AuthMethod():
    """
    Abstract class for authmethods that are used by ExtAuthUserManager
    All auth methods must implement the following methods
    """

    def __init__(self, conf):
        self._conf = conf

    def user_lookup(self, search):
        raise NotImplementedError

    def check_user(self, username):
        raise NotImplementedError

    def check_password(self, username, password):
        raise NotImplementedError

    def get_attrib(self, username, attrib):
        raise NotImplementedError


class LdapAuth(AuthMethod):
    """
    Authentication via LDAP

    User authentication:
    1a. bind to LDAP with either
            - generic configured DN and password (simple bind)
            - GSSAPI (e.g. Kerberos)
    1b. find the ldap object matching username.
        (return None if more than 1 object is found)
    2. if 1 succeeds, try simple bind with the supplied user DN and password

    User lookup:
    wildcard-search all configured "user lookup attributes" for
    the given search string
    """
    def __init__(self, conf):
        AuthMethod.__init__(self, conf)

    def _ldap_search(self, query, attrlist=None):
        """
        runs any ldap query passed as arg
        """
        import ldap
        from ldap.sasl import gssapi
        conn = ldap.initialize(self._conf['ldap_uri'])
        try:
            if self._conf['ldap_gssapi']:
                token = gssapi()
                conn.sasl_interactive_bind_s("", token)
            else:
                conn.simple_bind_s(self._conf['ldap_binddn'], self._conf['ldap_bindpw'])

            result = conn.search_ext_s(self._conf['ldap_basedn'],
                                         ldap.SCOPE_SUBTREE,
                                         filterstr=query,
                                         attrlist=attrlist,
                                         timeout=self._conf['ldap_timeout'],
                                         sizelimit=self._conf['ldap_sizelimit'])
        except ldap.INVALID_CREDENTIALS:
            raise ValueError, "invalid LDAP credentials"
        except ldap.LDAPError, e:
            raise ValueError, e
        finally:
            conn.unbind_s()

        return result

    def _get_ldapuser(self, username, attrlist=None):
        from ldap.filter import filter_format
        try:
            result = self._ldap_search(filter_format("(%s=%s)", [self._conf['ldap_username_attrib'], username]), attrlist)
        except ValueError, e:
            print(e)
            return None
        # return None if more than 1 object found
        return result[0] if len(result) == 1 else None

    def user_lookup(self, search):
        from ldap.filter import filter_format
        from ldap import LDAPError

        # build ldap OR query
        q = "(|%s)" % ''.join([filter_format("(%s=*%s*)", [a, search]) for a in self._conf['ldap_lookup_attribs']])

        try:
            r = self._ldap_search(q, attrlist=[str(self._conf['ldap_username_attrib'])])
        except ValueError, e:
            print(e)
            return []
        except:
            return []
        # return a list of usernames
        return [x[1][self._conf['ldap_username_attrib']][0].lower() for x in r if x[1].has_key(self._conf['ldap_username_attrib'])]

    def check_user(self, username):
        # LDAP is NOT case sensitive while sage is, so only lowercase names are allowed
        if username != username.lower():
            return False
        return self._get_ldapuser(username) is not None

    def check_password(self, username, password):
        import ldap
        # retrieve username's DN
        try:
            u = self._get_ldapuser(username)
            #u[0] is DN, u[1] is a dict with all other attributes
            userdn = u[0]
        except ValueError:
            return False

        # try to bind with that DN
        conn = ldap.initialize(uri=self._conf['ldap_uri'])
        try:
            conn.simple_bind_s(userdn, password)
            return True
        except ldap.INVALID_CREDENTIALS:
            return False
        finally:
            conn.unbind_s()

    def get_attrib(self, username, attrib):
        # translate some common attribute names to their ldap equivalents, i.e. "email" is "mail
        attrib = 'mail' if attrib == 'email' else attrib

        u = self._get_ldapuser(username)
        if u is not None:
            a = u[1][attrib][0] #if u[1].has_key(attrib) else ''
            return a
