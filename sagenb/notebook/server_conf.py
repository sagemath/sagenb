# -*- coding: utf-8 -*-
"""nodoctest
"""
#from   template import language
import copy

import conf
from conf import (POS, DESC, GROUP, TYPE, CHOICES, T_BOOL, T_INTEGER,
                  T_CHOICE, T_REAL, T_COLOR, T_STRING, T_LIST, T_INFO)
from sagenb.misc.misc import get_languages
from flaskext.babel import gettext, lazy_gettext
_ = lazy_gettext

defaults = {'word_wrap_cols':72,
            'max_history_length':250,
            
            'idle_timeout':120,        # 2 minutes
            'idle_check_interval':360,
            
            'save_interval':360,        # seconds

            'doc_pool_size':128,
            'doc_timeout': 120,

            'pub_interact':False,

            'server_pool':[],

            'system':'sage',

            'pretty_print':False,

            'ulimit':'',

            'email':False,

            'accounts':False,

            'openid':False,

            'challenge':False,
            'challenge_type':'simple',
            'recaptcha_public_key':'',
            'recaptcha_private_key':'',
            'default_language': 'en_US',
            'model_version': 0,

            'auth_ldap':False,
            'ldap_uri':'ldap://example.net:389/',
            'ldap_basedn':'ou=users,dc=example,dc=net',
            'ldap_binddn':'cn=manager,dc=example,dc=net',
            'ldap_bindpw': 'secret',
            'ldap_gssapi': False,
            'ldap_username_attrib': 'cn',
            'ldap_timeout': 5,
            }

G_APPEARANCE = _('Appearance')
G_AUTH = _('Authentication')
G_SERVER = _('Server')
G_LDAP = _('LDAP')

defaults_descriptions = {

    'word_wrap_cols': {
        DESC : _('Number of word-wrap columns'),
        GROUP : G_APPEARANCE,
        TYPE : T_INTEGER,
        },

    'max_history_length': {
        DESC : _('Maximum history length'),
        GROUP : G_SERVER,
        TYPE : T_INTEGER,
        },

    'idle_timeout': {
        DESC : _('Idle timeout (seconds)'),
        GROUP : G_SERVER,
        TYPE : T_INTEGER,
        },

    'idle_check_interval': {
        DESC : _('Idle check interval (seconds)'),
        GROUP : G_SERVER,
        TYPE : T_INTEGER,
        },

    'save_interval': {
        DESC : _('Save interval (seconds)'),
        GROUP : G_SERVER,
        TYPE : T_INTEGER,
        },

    'doc_pool_size': {
        DESC : _('Doc worksheet pool size'),
        GROUP : G_SERVER,
        TYPE : T_INTEGER,
        },

    'doc_timeout': {
        DESC : _('Doc worksheet idle timeout (seconds)'),
        GROUP : G_SERVER,
        TYPE : T_INTEGER,
        },

    'pub_interact': {
        DESC : _('Enable published interacts (EXPERIMENTAL; USE AT YOUR OWN RISK)'),
        GROUP : G_SERVER,
        TYPE : T_BOOL,
        },

    'server_pool': {
        DESC : _('Worksheet process users (comma-separated list)'),
        GROUP : G_SERVER,
        TYPE : T_LIST,
        },

    'system': {
        DESC : _('Default system'),
        GROUP : G_SERVER,
        TYPE : T_STRING,
        },

    'pretty_print': {
        DESC : _('Pretty print (typeset) output'),
        GROUP : G_APPEARANCE,
        TYPE : T_BOOL,
        },

    'ulimit': {
        DESC : _('Worksheet process limits'),
        GROUP : G_SERVER,
        TYPE : T_STRING,
        },

    'email': {
        POS : 3,
        DESC : _('Require e-mail for account registration'),
        GROUP : G_AUTH,
        TYPE : T_BOOL,
        },

    'accounts': {
        POS : 2,
        DESC : _('Enable user registration'),
        GROUP : G_AUTH,
        TYPE : T_BOOL,
        },

    'openid': {
        POS: 1,
        DESC : _('Allow OpenID authentication (requires python ssl module)'),
        GROUP : G_AUTH,
        TYPE : T_BOOL,
        },

    'challenge': {
        POS : 4,
        DESC : _('Use a challenge for account registration'),
        GROUP : G_AUTH,
        TYPE : T_BOOL,
        },

    'challenge_type': {
        POS : 4,
        DESC : _('Type of challenge'),
        GROUP : G_AUTH,
        TYPE : T_CHOICE,
        CHOICES : ['simple', 'recaptcha'],
        },

    'recaptcha_public_key': {
        DESC : _('reCAPTCHA public key'),
        GROUP : G_AUTH,
        TYPE : T_STRING,
        },

    'recaptcha_private_key': {
        DESC : _('reCAPTCHA private key'),
        GROUP : G_AUTH,
        TYPE : T_STRING,
        },

    'default_language': {
        DESC : _('Default Language'),
        GROUP : G_APPEARANCE,
        TYPE : T_CHOICE,
        CHOICES : get_languages(),
        },
    'model_version': {
        DESC : _('Model Version'),
        GROUP : G_SERVER,
        TYPE : T_INFO,
        },

    'auth_ldap': {
        POS : 1,
        DESC : _('Enable LDAP Authentication'),
        GROUP : G_LDAP,
        TYPE : T_BOOL,
        },
    'ldap_uri': {
        POS : 2,
        DESC : _('LDAP URI'),
        GROUP : G_LDAP,
        TYPE : T_STRING,
        },
    'ldap_binddn': {
        POS : 3,
        DESC : _('Bind DN'),
        GROUP : G_LDAP,
        TYPE : T_STRING,
        },
    'ldap_bindpw': {
        POS : 4,
        DESC : _('Bind Password'),
        GROUP : G_LDAP,
        TYPE : T_STRING,
        },
    'ldap_gssapi': {
        POS : 5,
        DESC : _('Use GSSAPI instead of Bind DN/Password'),
        GROUP : G_LDAP,
        TYPE : T_BOOL,
        },
    'ldap_basedn': {
        POS : 6,
        DESC : _('Base DN'),
        GROUP : G_LDAP,
        TYPE : T_STRING,
        },
    'ldap_username_attrib': {
        POS : 7,
        DESC: _('Username Attribute (i.e. cn, uid or userPrincipalName)'),
        GROUP : G_LDAP,
        TYPE : T_STRING,
        },
    'ldap_timeout': {
        POS : 8,
        DESC: _('Query timeout (seconds)'),
        GROUP : G_LDAP,
        TYPE : T_INTEGER,
        },
}


def ServerConfiguration_from_basic(basic):
    c = ServerConfiguration()
    c.confs = copy.copy(basic)
    return c

class ServerConfiguration(conf.Configuration):
    def defaults(self):
        return defaults

    def defaults_descriptions(self):
        return defaults_descriptions
