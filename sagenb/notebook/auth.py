class AuthMethod():
    """
    Abstract class for authmethods that are used by ExtAuthUserManager
    All auth methods must implement the following methods
    """

    def __init__(self, conf):
        self._conf = conf

    def check_user(self, username):
        raise NotImplementedError

    def check_password(self, username, password):
        raise NotImplementedError

    def get_attrib(self, username, attrib):
        raise NotImplementedError


class LdapAuth(AuthMethod):
    """
    Authentication via LDAP

    User authentication basically works like this:
    1.1) bind to LDAP with either
            - generic configured DN and password (simple bind)
            - GSSAPI (e.g. Kerberos)
    1.2) find the ldap object matching username.

    2) if 1 succeeds, try simple bind with the supplied user DN and password
    """

    def _require_ldap(default_return):
        """
        function decorator to
            - disable LDAP auth
            - return a "default" value (decorator argument)
        if importing ldap fails
        """
        def wrap(f):
            def wrapped_f(self, *args, **kwargs):
                try:
                    from ldap import __version__ as ldap_version
                except ImportError:
                    print "cannot 'import ldap', disabling LDAP auth"
                    self._conf['auth_ldap'] = False
                    return default_return
                else:
                    return f(self, *args, **kwargs)
            return wrapped_f
        return wrap

    def __init__(self, conf):
        AuthMethod.__init__(self, conf)

    def _ldap_search(self, query, attrlist=None, sizelimit=20):
        """
        runs any ldap query passed as arg
        """
        import ldap
        from ldap.sasl import gssapi
        conn = ldap.initialize(self._conf['ldap_uri'])

        try:
            if self._conf['ldap_gssapi']:
                token = gssapi()
                conn.sasl_interactive_bind_s('', token)
            else:
                conn.simple_bind_s(
                    self._conf['ldap_binddn'], self._conf['ldap_bindpw'])

            result = conn.search_ext_s(
                self._conf['ldap_basedn'],
                ldap.SCOPE_SUBTREE,
                filterstr=query,
                attrlist=attrlist,
                timeout=self._conf['ldap_timeout'],
                sizelimit=sizelimit)
        except ldap.LDAPError, e:
            print 'LDAP Error: %s' % str(e)
            return []
        finally:
            conn.unbind_s()

        return result

    def _get_ldapuser(self, username, attrlist=None):
        """
        Returns a tuple containing the DN and a dict of attributes of the given
        username, or (None, None) if the username is not found
        """
        from ldap.filter import filter_format

        query = filter_format(
            '(%s=%s)', (self._conf['ldap_username_attrib'], username))

        result = self._ldap_search(query, attrlist)

        # only allow one unique result
        # (len(result) will probably always be 0 or 1)
        return result[0] if len(result) == 1 else (None, None)

    @_require_ldap(False)
    def check_user(self, username):
        # LDAP is NOT case sensitive while sage is, so only allow lowercase
        if not username.islower():
            return False
        dn, attribs = self._get_ldapuser(username)
        return dn is not None

    @_require_ldap(False)
    def check_password(self, username, password):
        import ldap

        dn, attribs = self._get_ldapuser(username)
        if not dn:
            return False

        # try to bind with found DN
        conn = ldap.initialize(uri=self._conf['ldap_uri'])
        try:
            conn.simple_bind_s(dn, password)
            return True
        except ldap.INVALID_CREDENTIALS:
            return False
        except ldap.LDAPError, e:
            print 'LDAP Error: %s' % str(e)
            return False
        finally:
            conn.unbind_s()

    @_require_ldap('')
    def get_attrib(self, username, attrib):
        # 'translate' attribute names used in ExtAuthUserManager
        # to their ldap equivalents

        # "email" is "mail"
        if attrib == 'email':
            attrib = 'mail'

        dn, attribs = self._get_ldapuser(username, [attrib])
        if not attribs:
            return ''

        # return the first item or '' if the attribute is missing
        return attribs.get(attrib, [''])[0]
