# -*- coding: utf-8 -*
"""
jsMath support for the notebook

Provides code to parse HTML, changing \$'s and \$\$'s to
<span class="math"> tags to allow jsMath to process them.

AUTHORS:

- William Stein (?) -- initial revision

- Tim Dumol (Oct 6, 2009) -- Added HTMLMathParser. Made `math_parser` skip <script> tags.

- Reverted HTMLMathParser
"""

########################################################################
#       Copyright (C) 2008, 2009 William Stein <wstein@gmail.com>
#  Distributed under the terms of the GNU General Public License (GPL)
#                  http://www.gnu.org/licenses/
########################################################################


def math_parse(s):
    r"""
    Turn the HTML-ish string s that can have $$ and $'s in it into
    pure HTML.  See below for a precise definition of what this means.
    
    INPUT:
        s -- a string
    OUTPUT:
        a string.
        
    Do the following:
    \begin{verbatim}
       * Replace all $ text $'s by
         <span class='math'> text </span>
       * Replace all $$ text $$'s by
         <div class='math'> text </div>
       * Replace all \$'s by $'s.  Note that in
         the above two cases nothing is done if the $
         is preceeded by a backslash.
       * Replace all \[ text \]'s by
         <div class='math'> text </div>
    \end{verbatim}

    EXAMPLES:
        sage: sage.misc.html.math_parse('This is $2+2$.')
        'This is <span class="math">2+2</span>.'
        sage: sage.misc.html.math_parse('This is $$2+2$$.')
        'This is <div class="math">2+2</div>.'
        sage: sage.misc.html.math_parse('This is \\[2+2\\].')
        'This is <div class="math">2+2</div>.'
        sage: sage.misc.html.math_parse(r'This is \[2+2\].')
        'This is <div class="math">2+2</div>.'

    TESTS:
        sage: sage.misc.html.math_parse(r'This \$\$is $2+2$.')
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
