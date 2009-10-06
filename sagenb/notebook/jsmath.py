"""
jsMath support for the notebook

Provides code to parse HTML, changing \$'s and \$\$'s to
<span class="math"> tags to allow jsMath to process them.

AUTHORS:

- William Stein (?) -- initial revision

- Tim Dumol (Oct 6, 2009) -- Added HTMLMathParser. Made `math_parser` skip <script> tags.
"""

########################################################################
#       Copyright (C) 2008, 2009 William Stein <wstein@gmail.com>
#  Distributed under the terms of the GNU General Public License (GPL)
#                  http://www.gnu.org/licenses/
########################################################################

from HTMLParser import HTMLParser

class HTMLMathParser(HTMLParser):
    """
    Parses HTML handed to this class by changing \$'s and \$\$'s to
    <span class="math"> tags, while leaving text in <script> tags untouched.
    See :meth: `sagenb.notebook.jsmath.math_parse` for a full description.

    EXAMPLES::

        sage: from sagenb.notebook.jsmath import HTMLMathParser
        sage: parser = HTMLMathParser()
        sage: parser.feed("<body>This is a test\n\
        ...   <script>\n\
        ...   $ Lorem ipsum $ dolor sit amet</script>\n\
        ...   <p> $$ consectetuer $$ </p>\n\
        ...   <p>adipiscing $ elit $. Integer\n\
        ...   <p> non semper ante.\n\
        ...   </body>")
        sage: print parser.text
        <body>This is a test
           <script>
           $ Lorem ipsum $ dolor sit amet</script>
           <p> <div class="math"> consectetuer </div> </p>
           <p>adipiscing <span class="math"> elit </span>. Integer
           <p> non semper ante.
           </body>
    """
    def __init__(self):
        HTMLParser.__init__(self)
        self.text = ''
        
    def handle_endtag(self, tag):
        r"""
        Adds end tags that are encountered.
        This is used internally by HTMLParser.

        EXAMPLES::

            sage: from sagenb.notebook.jsmath import HTMLMathParser
            sage: parser = HTMLMathParser()
            sage: parser.handle_endtag('script')
            sage: parser.text
            '</script>'
        """
        self.text += '</%s>' % tag
        
    def handle_starttag(self, tag, attrs):
        r"""
        Adds start tags that are encountered.
        This is used internally by HTMLParser.

        EXAMPLES::

            sage: from sagenb.notebook.jsmath import HTMLMathParser
            sage: parser = HTMLMathParser()
            sage: parser.handle_starttag('script', [('type','text/javascript')])
            sage: parser.text
            '<script type="text/javascript">'
        """
        if attrs:
            attr_string = ' ' + ' '.join(['%s="%s"' % (attr_name, attr_value) for attr_name, attr_value in attrs])
        else:
            attr_string = ''
        self.text += '<%s%s>' % (tag, attr_string)

    def handle_charref(self, name):
        r"""
        Adds character entities that are encountered.
        This is used internally by HTMLParser.
        
        EXAMPLES::

            sage: from sagenb.notebook.jsmath import HTMLMathParser
            sage: parser = HTMLMathParser()
            sage: parser.handle_charref('123')            
            sage: parser.text
            '&#123;'
        """
        self.text += '&#%s;' % name

    def handle_data(self, data):
        r"""
        Processes data (text between tags), but skips data in <script> tags.
        This is used internally by HTMLParser.

        EXAMPLES::

            sage: from sagenb.notebook.jsmath import HTMLMathParser
            sage: parser = HTMLMathParser()
            sage: parser.feed("<body>This is a test\n\
            ...   <script>\n\
            ...   $ Lorem ipsum $ dolor sit amet</script>\n\
            ...   <p> $$ consectetuer $$ </p>\n\
            ...   <p>adipiscing $ elit $. Integer\n\
            ...   <p> non semper ante.\n\
            ...   </body>")
            sage: print parser.text
            <body>This is a test
               <script>
               $ Lorem ipsum $ dolor sit amet</script>
               <p> <div class="math"> consectetuer </div> </p>
               <p>adipiscing <span class="math"> elit </span>. Integer
               <p> non semper ante.
               </body>
        """
        if self.lasttag != 'script':
            self.text += self.math_parse(data)
        else:
            self.text += data
    
    def handle_decl(self, decl):
        r"""
        Adds SGML declarations that are encountered.
        This is used internally by HTMLParser.
        
        EXAMPLES::

            sage: from sagenb.notebook.jsmath import HTMLMathParser
            sage: parser = HTMLMathParser()
            sage: parser.handle_decl('DOCTYPE html')
            sage: parser.text
            '<!DOCTYPE html>'
        """
        self.text += '<!%s>' % decl

    def handle_entityref(self, name):
        r"""
        Adds entity references that are encountered.
        This is used internally by HTMLParser.
        
        EXAMPLES::

            sage: from sagenb.notebook.jsmath import HTMLMathParser
            sage: parser = HTMLMathParser()
            sage: parser.handle_entityref('nbsp')
            sage: parser.text
            '&nbsp;'
        """
        self.text += '&%s;' % name

    def handle_pi(self, data):
        r"""
        Adds processing instructions that are encountered.
        This is used internally by HTMLParser.
        
        EXAMPLES::

            sage: from sagenb.notebook.jsmath import HTMLMathParser
            sage: parser = HTMLMathParser()
            sage: parser.handle_pi('xml version="1.0" encoding="utf-8"?')
            sage: parser.text
            '<?xml version="1.0" encoding="utf-8"?>'
        """
        self.text += '<?%s>' % data

    def math_parse(self, s):
        r"""
        Processes a string, changing \$ and \$\$ characters to
        <span class="math"> tags. See :meth: `sagenb.notebook.jsmath.math_parse`
        for a full description.

        EXAMPLES::

            sage: from sagenb.notebook.jsmath import HTMLMathParser
            sage: parser = HTMLMathParser()
            sage: parser.math_parse('This is $2+2$.')
            'This is <span class="math">2+2</span>.'
            sage: parser.math_parse('This is $$2+2$$.')
            'This is <div class="math">2+2</div>.'
            sage: parser.math_parse('This is \\[2+2\\].')
            'This is <div class="math">2+2</div>.'
            sage: parser.math_parse(r'This is \[2+2\].')
            'This is <div class="math">2+2</div>.'

        TESTS::
    
            sage: from sagenb.notebook.jsmath import math_parse
            sage: math_parse(r'This \$\$is $2+2$.')
            'This $$is <span class="math">2+2</span>.' 
        """
        # first replace \\[ and \\] by <div class="math"> and </div>, respectively.
        while True:
            i = s.find('\\[')
            if i == -1:
                break
            else:
                s = s[:i] + '<div class="math">' + s[i+2:]
                j = s.find('\\]')
                if j == -1:  # missing right-hand delimiter, so add one
                    s = s + '</div>'
                else:
                    s = s[:j] + '</div>' + s[j+2:]
    
        # Below t always has the "parsed so far" version of s, and s is
        # just the part of the original input s that hasn't been parsed.
        t = ''
        while True:
            i = s.find('$')
            if i == -1:
                # No dollar signs -- definitely done.
                return t + s
            elif i > 0 and s[i-1] == '\\':
                # A dollar sign with a backslash right before it, so
                # we ignore it by sticking it in the parsed string t
                # and skip to the next iteration.
                t += s[:i-1] + '$'
                s = s[i+1:]
                continue
            elif i+1 < len(s) and s[i+1] == '$':
                # Found a math environment. Double dollar sign so div mode.
                typ = 'div'
            else:
                # Found math environment. Single dollar sign so span mode.
                typ = 'span'

            # Now find the matching $ sign and form the span or div.
            j = s[i+2:].find('$')
            if j == -1:
                j = len(s)
                s += '$'
                if typ == 'div':
                    s += '$$'
            else:
                j += i + 2
            if typ == 'div':
                txt = s[i+2:j]
            else:
                txt = s[i+1:j]
            t += s[:i] + '<%s class="math">%s</%s>'%(typ,
                                                     ' '.join(txt.splitlines()), typ)
            s = s[j+1:]
            if typ == 'div':
                s = s[1:]
        return t


def math_parse(s):
    r"""
    Turn the HTML-ish string s that can have \$\$ and \$'s in it into
    pure HTML.  See below for a precise definition of what this means.
    This does not process anything inside <script> tags.
    
    INPUT:
    
    - s -- a string
    OUTPUT:
    
    -- a string.
    
    Does the following:
    
    \begin{verbatim}
    * Replaces all $ text $'s by
    <span class='math'> text </span>
    * Replaces all $$ text $$'s by
    <div class='math'> text </div>
    * Replaces all \$'s by $'s.  Note that in
    the above two cases nothing is done if the $
    is preceeded by a backslash.
    * Replaces all \[ text \]'s by
    <div class='math'> text </div>
    \end{verbatim}

    EXAMPLES::

        sage: from sagenb.notebook.jsmath import math_parse
        sage: math_parse('This is $2+2$.')
        'This is <span class="math">2+2</span>.'
        sage: math_parse('This is $$2+2$$.')
        'This is <div class="math">2+2</div>.'
        sage: math_parse('This is \\[2+2\\].')
        'This is <div class="math">2+2</div>.'
        sage: math_parse(r'This is \[2+2\].')
        'This is <div class="math">2+2</div>.'

    TESTS::
    
        sage: from sagenb.notebook.jsmath import math_parse
        sage: math_parse(r'This \$\$is $2+2$.')
        'This $$is <span class="math">2+2</span>.'
    """
    parser = HTMLMathParser()
    parser.feed(s)
    return parser.text
