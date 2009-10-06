"""nodoctest
"""
import copy

import conf

defaults = {'max_history_length':1000,
            'default_system':'sage',
            'autosave_interval':60*60,   # 1 hour in seconds
            'default_pretty_print': False
            }

def UserConfiguration_from_basic(basic):
    c = UserConfiguration()
    c.confs = copy.copy(basic)
    return c

class UserConfiguration(conf.Configuration):
    def defaults(self):
        return defaults
