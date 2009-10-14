"""nodoctest
"""

import copy

import conf
from conf import (DESC, GROUP, TYPE, CHOICES, T_BOOL, T_INTEGER,
                  T_CHOICE, T_REAL, T_COLOR, T_STRING, T_LIST)

defaults = {'cell_input_color':'#000000',
            'cell_output_color':'#0000EE',
            'word_wrap_cols':72,
            'max_history_length':250,
            'number_of_backups':3,
            
            'idle_timeout':120,        # 2 minutes
            'idle_check_interval':360,
            
            'save_interval':360,        # seconds

            'doc_pool_size':128,

            'server_pool':[],

            'system':'sage',

            'pretty_print':False,

            'ulimit':'',

            'email':False,

            'accounts':False,

            'challenge':False,
            'challenge_type':'simple',
            'recaptcha_public_key':'',
            'recaptcha_private_key':'',
            }

G_APPEARANCE = 'Appearance'
G_AUTH = 'Authentication'
G_SERVER = 'Server'

defaults_descriptions = {
    'cell_input_color': {
        DESC : 'Input cell color',
        GROUP : G_APPEARANCE,
        TYPE : T_COLOR,
        },

    'cell_output_color': {
        DESC : 'Output cell color',
        GROUP : G_APPEARANCE,
        TYPE : T_COLOR,
        },

    'word_wrap_cols': {
        DESC : 'Number of word-wrap columns',
        GROUP : G_APPEARANCE,
        TYPE : T_INTEGER,
        },

    'max_history_length': {
        DESC : 'Maximum history length',
        GROUP : G_SERVER,
        TYPE : T_INTEGER,
        },

    'number_of_backups': {
        DESC : 'Number of backups',
        GROUP : G_SERVER,
        TYPE : T_INTEGER,
        },

    'idle_timeout': {
        DESC : 'Idle timeout (seconds)',
        GROUP : G_SERVER,
        TYPE : T_INTEGER,
        },

    'idle_check_interval': {
        DESC : 'Idle check interval (seconds)',
        GROUP : G_SERVER,
        TYPE : T_INTEGER,
        },

    'save_interval': {
        DESC : 'Save interval (seconds)',
        GROUP : G_SERVER,
        TYPE : T_INTEGER,
        },

    'doc_pool_size': {
        DESC : 'Doc pool size',
        GROUP : G_SERVER,
        TYPE : T_INTEGER,
        },

    'server_pool': {
        DESC : 'Worksheet process users (comma-separated list)',
        GROUP : G_SERVER,
        TYPE : T_LIST,
        },

    'system': {
        DESC : 'Default system',
        GROUP : G_SERVER,
        TYPE : T_STRING,
        },

    'pretty_print': {
        DESC : 'Pretty print (typeset) output',
        GROUP : G_APPEARANCE,
        TYPE : T_BOOL,
        },

    'ulimit': {
        DESC : 'Worksheet process limits',
        GROUP : G_SERVER,
        TYPE : T_STRING,
        },

    'email': {
        DESC : 'Require e-mail for account registration',
        GROUP : G_AUTH,
        TYPE : T_BOOL,
        },

    'accounts': {
        DESC : 'Enable user registration',
        GROUP : G_AUTH,
        TYPE : T_BOOL,
        },

    'challenge': {
        DESC : 'Use a challenge for account registration',
        GROUP : G_AUTH,
        TYPE : T_BOOL,
        },

    'challenge_type': {
        DESC : 'Type of challenge',
        GROUP : G_AUTH,
        TYPE : T_CHOICE,
        CHOICES : ['simple', 'recaptcha'],
        },

    'recaptcha_public_key': {
        DESC : 'reCAPTCHA public key',
        GROUP : G_AUTH,
        TYPE : T_STRING,
        },

    'recaptcha_private_key': {
        DESC : 'reCAPTCHA private key',
        GROUP : G_AUTH,
        TYPE : T_STRING,
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
