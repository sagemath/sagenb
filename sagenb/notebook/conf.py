# -*- coding: utf-8 -*
"""nodoctest
Configuration
"""

#############################################################################
#       Copyright (C) 2007 William Stein <wstein@gmail.com>
#  Distributed under the terms of the GNU General Public License (GPL)
#  The full text of the GPL is available at:
#                  http://www.gnu.org/licenses/
#############################################################################
from flaskext.babel import gettext, lazy_gettext

POS = 'pos'
DESC = 'desc'
GROUP = 'group'
TYPE = 'type'
CHOICES = 'choices'

T_BOOL = 0
T_INTEGER = 1
T_CHOICE = 2
T_REAL = 3
T_COLOR = 4
T_STRING = 5
T_LIST = 6
T_INFO = 7

POS_DEFAULT = 100

class Configuration(object):
    
    def __init__(self):
        self.confs = {}

    def __repr__(self):
        return 'Configuration: %s'%self.confs

    def __eq__(self, other):
        return self.__class__ is other.__class__ and self.confs == other.confs
        
    def __ne__(self, other):
        return not self.__eq__(other)

    def basic(self):
        return self.confs

    def defaults(self):
        raise NotImplementedError

    def defaults_descriptions(self):
        raise NotImplementedError

    def __getitem__(self, key):
        try:
            return self.confs[key]
        except KeyError:
            if self.defaults().has_key(key):
                A = self.defaults()[key]
                self.confs[key] = A
                return A
            else:
                raise KeyError("No key '%s' and no default for this key"%key)

    def __setitem__(self, key, value):
        self.confs[key] = value
    
    # TODO all of these HTML methods should really be put into 
    # the Jinja template instead of rendered in custom Python 
    # functions.
    def html_conf_form(self, action):
        D = self.defaults()
        C = self.confs
        K = list(set(self.confs.keys() + D.keys()))
        K.sort()
        options = ''
        for key in K:
            options += '<tr><td>%s</td><td><input type="text" name="%s" value="%s"></td></tr>\n'%(key, key, self[key])
        s = """
        <form method="post" action="%s" enctype="multipart/form-data">
        <input type="submit" value="Submit">
        <table border=0 cellpadding=5 cellspacing=2>
%s
        </table>
        </form>
        """%(action, options)
        return s

    def update_from_form(self, form):
        D = self.defaults()
        DS = self.defaults_descriptions()
        C = self.confs
        keys = list(set(C.keys() + D.keys()))

        updated = {}
        for key in keys:
            try:
                typ = DS[key][TYPE]
            except KeyError:
                # We skip this setting.  Perhaps defaults_descriptions
                # is not in sync with defaults, someone has tampered
                # with the request arguments, etc.
                continue
            val = form.get(key, '')

            if typ == T_BOOL:
                if val:
                    val = True
                else:
                    val = False

            elif typ == T_INTEGER:
                try:
                    val = int(val)
                except ValueError:
                    val = self[key]

            elif typ == T_REAL:
                try:
                    val = float(val)
                except ValueError:
                    val = self[key]

            elif typ == T_LIST:
                val = val.strip()
                if val == '' or val == 'None':
                    val = None
                else:
                    val = val.split(',')

            if typ != T_INFO and self[key] != val:
                self[key] = val
                updated[key] = ('updated', gettext('Updated'))

        return updated

    def html_table(self, updated = {}):
        from server_conf import G_LDAP

        # check if LDAP can be used
        try:
            from ldap import __version__ as ldap_version
        except ImportError:
            ldap_version = None

        # For now, we assume there's a description for each setting.
        D = self.defaults()
        DS = self.defaults_descriptions()
        C = self.confs
        K = set(C.keys() + D.keys())
        
        G = {}
        # Make groups
        for key in K:
            try:
                gp = DS[key][GROUP]
                # don't display LDAP settings if the check above failed
                if gp == G_LDAP and ldap_version is None:
                    continue
                DS[key][DESC]
                DS[key][TYPE]
            except KeyError:
                # We skip this setting.  It's obsolete and/or
                # defaults_descriptions is not up to date.  See
                # *_conf.py for details.
                continue
            try:
                G[gp].append(key)
            except KeyError:
                G[gp] = [key]

        s = u''
        color_picker = 0
        special_init = u''
        for group in G:
            s += u'<div class="section">\n  <h2>%s</h2>\n  <table>\n' % lazy_gettext(group)

            opts = G[group]
            def sortf(x, y):
                wx = DS[x].get(POS, POS_DEFAULT)
                wy = DS[y].get(POS, POS_DEFAULT)
                if wx == wy:
                    return cmp(x, y)
                else:
                    return cmp(wx, wy)
            opts.sort(sortf)
            for o in opts:
                s += u'    <tr>\n      <td>%s</td>\n      <td>\n' % lazy_gettext(DS[o][DESC])
                input_type = 'text'
                input_value = self[o]

                extra = ''
                if DS[o][TYPE] == T_BOOL:
                    input_type = 'checkbox'
                    if input_value:
                        extra = 'checked="checked"'

                if DS[o][TYPE] == T_LIST:
                    if input_value is not None:
                        input_value = ','.join(input_value)

                if DS[o][TYPE] == T_CHOICE:
                    s += u'        <select name="%s" id="%s">\n' % (o, o)
                    for c in DS[o][CHOICES]:
                        selected = ''
                        if c == input_value:
                            selected = u' selected="selected"'
                        s += u'          <option value="%s"%s>%s</option>\n' % (c, selected, lazy_gettext(c))
                    s += u'        </select>\n'

                elif DS[o][TYPE] == T_INFO:
                    s += u'        <span>%s</span>'%input_value

                else:
                    s += u'        <input type="%s" name="%s" id="%s" value="%s" %s>\n' % (input_type, o, o, input_value, extra)

                    if DS[o][TYPE] == T_COLOR:
                        s += u'        <div id="picker_%s"></div>\n' % color_picker
                        special_init += u'    $("#picker_%s").farbtastic("#%s");\n' % (color_picker, o)
                        color_picker += 1

                s += u'      </td>\n      <td class="%s">%s</td>\n    </tr>\n' % updated.get(o, ('', ''))

            s += u'  </table>\n</div>\n'

        s += u'<script type="text/javascript">\n$(document).ready(function() {\n' + special_init + '});\n</script>'

        lines = s.split(u'\n')
        lines = map(lambda x: u'  ' + x, lines)

        return u'\n'.join(lines)
