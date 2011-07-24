# -*- coding: utf-8 -*
"""nodoctest
"""
import os, copy

import server_conf
from conf import (Configuration, POS, DESC, GROUP, TYPE, CHOICES, T_BOOL,
                  T_INTEGER, T_CHOICE, T_REAL, T_COLOR, T_STRING, T_LIST)
from sagenb.misc.misc import SAGENB_ROOT, get_languages
from flaskext.babel import lazy_gettext

defaults = {'max_history_length':1000,
            'default_system':'sage',
            'autosave_interval':60*60,   # 1 hour in seconds
            'default_pretty_print': False,
            'next_worksheet_id_number': -1,  # not yet initialized
            'language': 'default'
            }

defaults_descriptions = {
    'language': {
        DESC : lazy_gettext('Language'),
        GROUP : lazy_gettext('Appearance'),
        TYPE : T_CHOICE,
        CHOICES : ['default'] + get_languages(),
        },
    }


def UserConfiguration_from_basic(basic):
    c = UserConfiguration()
    c.confs = copy.copy(basic)
    return c

class UserConfiguration(Configuration):
    def defaults(self):
        return defaults

    def defaults_descriptions(self):
        return defaults_descriptions
