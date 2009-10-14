"""nodoctest
Configuration
"""

#############################################################################
#       Copyright (C) 2007 William Stein <wstein@gmail.com>
#  Distributed under the terms of the GNU General Public License (GPL)
#  The full text of the GPL is available at:
#                  http://www.gnu.org/licenses/
#############################################################################

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

class Configuration(object):
    
    def __init__(self):
        self.confs = {}

    def __repr__(self):
        return 'Configuration: %s'%self.confs

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
                raise KeyError, "No key '%s' and no default for this key"%key

    def __setitem__(self, key, value):
        self.confs[key] = value
        
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

    def update_from_form(self, req_args):
        D = self.defaults()
        DS = self.defaults_descriptions()
        C = self.confs
        K = list(set(self.confs.keys() + D.keys()))

        updated = {}
        for key in K:
            typ = DS[key][TYPE]
            val = req_args.get(key, [None])[0]

            if typ == T_BOOL:
                if val:
                    val = True
                else:
                    val = False

            elif typ == T_INTEGER or typ == T_REAL:
                val = int(val)

            elif typ == T_LIST:
                val = val.strip()
                if val == '' or val == 'None':
                    val = None
                else:
                    val = val.split(',')

            if self[key] != val:
                self[key] = val
                updated[key] = ('updated', 'Updated')

        return updated

    def html_table(self, updated = {}):
        # For now, we assume there's a description for each setting.
        D = self.defaults()
        DS = self.defaults_descriptions()
        C = self.confs
        K = set(C.keys() + D.keys())
        
        G = {}
        # Make groups
        for key in K:
            try:
                G[DS[key][GROUP]].append(key)
            except KeyError:
                G[DS[key][GROUP]] = [key]

        s = ''
        color_picker = 0
        special_init = ''
        for group in G:
            s += '<div class="section">\n  <h2>%s</h2>\n  <table>\n' % group

            opts = G[group]
            opts.sort()
            for o in opts:
                s += '    <tr>\n      <td>%s</td>\n      <td>\n' % DS[o][DESC]
                input_type = 'text'
                input_value = self[o]

                extra = ''
                if DS[o][TYPE] == T_BOOL:
                    input_type = 'checkbox'
                    if input_value:
                        extra = ' checked="checked"'

                if DS[o][TYPE] == T_LIST:
                    if input_value is not None:
                        input_value = ','.join(input_value)

                if DS[o][TYPE] == T_CHOICE:
                    s += '        <select name="%s" id="%s">\n' % (o, o)

                    for c in DS[o][CHOICES]:
                        selected = ''
                        if c == input_value:
                            selected = ' selected="selected"'
                        s += '          <option value="%s"%s>%s</option>\n' % (c, selected, c)
                    s += '        </select>\n'

                else:
                    s += '        <input type="%s" name="%s" id="%s" value="%s"%s>\n' % (input_type, o, o, input_value, extra)

                    if DS[o][TYPE] == T_COLOR:
                        s += '        <div id="picker_%s"></div>\n' % color_picker
                        special_init += '    $("#picker_%s").farbtastic("#%s");\n' % (color_picker, o)
                        color_picker += 1

                s += '      </td>\n      <td class="%s">%s</td>\n    </tr>\n' % updated.get(o, ('', ''))

            s += '  </table>\n</div>\n'

        s += '<script type="text/javascript">\n$(document).ready(function() {\n' + special_init + '});\n</script>'

        lines = s.split('\n')
        lines = map(lambda x: '  ' + x, lines)

        return '\n'.join(lines)
