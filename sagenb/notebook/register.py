# -*- coding: utf-8 -*
"""nodoctest
"""

#############################################################################
#       Copyright (C) 2007 William Stein <wstein@gmail.com>
#  Distributed under the terms of the GNU General Public License (GPL)
#  The full text of the GPL is available at:
#                  http://www.gnu.org/licenses/
#############################################################################

"""
Helper functions dealing with the verification of user  
"""
from flask_babel import gettext as _

def build_msg(key, username, addr, port, secure):
    url_prefix = "https" if secure else "http"
    s  = _("Hi %(username)s!\n\n", username=username)
    s += _('Thank you for registering for the Sage notebook. To complete your registration, copy and paste'
           ' the following link into your browser:\n\n'
           '%(url_prefix)s://%(addr)s:%(port)s/confirm?key=%(key)s\n\n'
           'You will be taken to a page which will confirm that you have indeed registered.',
           url_prefix=url_prefix, addr=addr, port=port, key=key)
    return s.encode('utf-8')

def build_password_msg(key, username, addr, port, secure):
    url_prefix = "https" if secure else "http"
    s  = _("Hi %(username)s!\n\n", username=username)
    s += _('Your new password is %(key)s\n\n'
           'Sign in at %(url_prefix)s://%(addr)s:%(port)s/\n\n'
           'Make sure to reset your password by going to Settings in the upper right bar.',
           key=key, url_prefix=url_prefix, addr=addr, port=port)
    return s.encode('utf-8')

def make_key():
    from random import randint
    key = randint(0,2**128-1)
    return key
