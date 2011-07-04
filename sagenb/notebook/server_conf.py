# -*- coding: utf-8 -*-
"""nodoctest
"""
#from   template import language
import copy

import conf
from conf import (POS, DESC, GROUP, TYPE, CHOICES, T_BOOL, T_INTEGER,
                  T_CHOICE, T_REAL, T_COLOR, T_STRING, T_LIST)
from sagenb.misc.misc import get_languages
from flaskext.babel import gettext, lazy_gettext

defaults = {'word_wrap_cols':72,
            'max_history_length':250,
            
            'idle_timeout':120,        # 2 minutes
            'idle_check_interval':360,
            
            'save_interval':360,        # seconds

            'doc_pool_size':128,
            'doc_timeout': 120,

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
            }

G_APPEARANCE = lazy_gettext('Appearance')
G_AUTH = lazy_gettext('Authentication')
G_SERVER = lazy_gettext('Server')

defaults_descriptions = {

    'word_wrap_cols': {
        DESC : lazy_gettext('Number of word-wrap columns'),
        GROUP : G_APPEARANCE,
        TYPE : T_INTEGER,
        },

    'max_history_length': {
        DESC : lazy_gettext('Maximum history length'),
        GROUP : G_SERVER,
        TYPE : T_INTEGER,
        },

    'idle_timeout': {
        DESC : lazy_gettext('Idle timeout (seconds)'),
        GROUP : G_SERVER,
        TYPE : T_INTEGER,
        },

    'idle_check_interval': {
        DESC : lazy_gettext('Idle check interval (seconds)'),
        GROUP : G_SERVER,
        TYPE : T_INTEGER,
        },

    'save_interval': {
        DESC : lazy_gettext('Save interval (seconds)'),
        GROUP : G_SERVER,
        TYPE : T_INTEGER,
        },

    'doc_pool_size': {
        DESC : lazy_gettext('Doc worksheet pool size'),
        GROUP : G_SERVER,
        TYPE : T_INTEGER,
        },

    'doc_timeout': {
        DESC : lazy_gettext('Doc worksheet idle timeout (seconds)'),
        GROUP : G_SERVER,
        TYPE : T_INTEGER,
        },

    'server_pool': {
        DESC : lazy_gettext('Worksheet process users (comma-separated list)'),
        GROUP : G_SERVER,
        TYPE : T_LIST,
        },

    'system': {
        DESC : lazy_gettext('Default system'),
        GROUP : G_SERVER,
        TYPE : T_STRING,
        },

    'pretty_print': {
        DESC : lazy_gettext('Pretty print (typeset) output'),
        GROUP : G_APPEARANCE,
        TYPE : T_BOOL,
        },

    'ulimit': {
        DESC : lazy_gettext('Worksheet process limits'),
        GROUP : G_SERVER,
        TYPE : T_STRING,
        },

    'email': {
        POS : 3,
        DESC : lazy_gettext('Require e-mail for account registration'),
        GROUP : G_AUTH,
        TYPE : T_BOOL,
        },

    'accounts': {
        POS : 2,
        DESC : lazy_gettext('Enable user registration'),
        GROUP : G_AUTH,
        TYPE : T_BOOL,
        },

    'openid': {
        POS: 1,
        DESC : lazy_gettext('Allow OpenID authentication (requires python ssl module)'),
        GROUP : G_AUTH,
        TYPE : T_BOOL,
        },

    'challenge': {
        POS : 4,
        DESC : lazy_gettext('Use a challenge for account registration'),
        GROUP : G_AUTH,
        TYPE : T_BOOL,
        },

    'challenge_type': {
        POS : 4,
        DESC : lazy_gettext('Type of challenge'),
        GROUP : G_AUTH,
        TYPE : T_CHOICE,
        CHOICES : ['simple', 'recaptcha'],
        },

    'recaptcha_public_key': {
        DESC : lazy_gettext('reCAPTCHA public key'),
        GROUP : G_AUTH,
        TYPE : T_STRING,
        },

    'recaptcha_private_key': {
        DESC : lazy_gettext('reCAPTCHA private key'),
        GROUP : G_AUTH,
        TYPE : T_STRING,
        },

    'default_language': {
        DESC : lazy_gettext('Default Language'),
        GROUP : G_APPEARANCE,
        TYPE : T_CHOICE,
        CHOICES : get_languages(),
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
