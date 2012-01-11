# -*- coding: utf-8 -*
"""
MathJax support for the notebook

Provides code to parse HTML, changing \$'s and \$\$'s to
<script type="tex/math"> tags to allow MathJax to process them.

AUTHORS:

- William Stein (?) -- initial revision

- Tim Dumol (Oct 6, 2009) -- Added HTMLMathParser. Made `math_parser` skip <script> tags.

- Reverted HTMLMathParser

- Edited by John Palmieri, for Flask and MathJax cutover
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
         <script type="math/tex"> text </script>
       * Replace all $$ text $$'s by
         <script type="math/tex; mode=display"> text </script>
       * Replace all \$'s by $'s.  Note that in
         the above two cases nothing is done if the $
         is preceeded by a backslash.
       * Replace all \[ text \]'s by
         <script type="math/tex; mode=display"> text </script>
    \end{verbatim}

    EXAMPLES:
        sage: sage.misc.html.math_parse('This is $2+2$.')
        'This is <script type="math/tex">2+2</script>.'
        sage: sage.misc.html.math_parse('This is $$2+2$$.')
        'This is <script type="math/tex; mode=display">2+2</script>.'
        sage: sage.misc.html.math_parse('This is \\[2+2\\].')
        'This is <script type="math/tex; mode=display">2+2</script>.'
        sage: sage.misc.html.math_parse(r'This is \[2+2\].')
        'This is <script type="math/tex; mode=display">2+2</script>.'

    TESTS:
        sage: sage.misc.html.math_parse(r'This \$\$is $2+2$.')
        'This $$is <script type="math/tex">2+2</script>.'
    """
    # first replace \\[ and \\] by <div class="math"> and </div>, respectively.
    while True:
        i = s.find('\\[')
        if i == -1:
            break
        else:
            s = s[:i] + '<script type="math/tex; mode=display">' + s[i+2:]
            j = s.find('\\]')
            if j == -1:  # missing right-hand delimiter, so add one
                s = s + '</script>'
            else:
                s = s[:j] + '</script>' + s[j+2:]

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
            # Found a math environment. Double dollar sign so display mode.
            disp = '; mode=display'
        else:
            # Found math environment. Single dollar sign so default mode.
            disp = ''

        # Now find the matching $ sign and form the html string.

        if len(disp) > 0:
            j = s[i+2:].find('$$')
            if j == -1:
                j = len(s)
                s += '$$'
            else:
                j += i + 2
            txt = s[i+2:j]
        else:
            j = s[i+2:].find('$')
            if j == -1:
                j = len(s)
                s += '$'
            else:
                j += i + 2
            txt = s[i+1:j]

        t += s[:i] + '<script type="math/tex%s">%s</script>'%(disp,
                      ' '.join(txt.splitlines()))
        s = s[j+1:]
        if len(disp) > 0:
            s = s[1:]
    return t
