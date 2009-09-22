def displayhook_hack(string):
    """
    Modified version of string so that exec'ing it results in
    displayhook possibly being called.
    
    STRING:

        - ``string`` - a string

    OUTPUT:

        - string formated so that when exec'd last line is printed if
          it is an expression
    """
    # This function is all so the last line (or single lines) will
    # implicitly print as they should, unless they are an assignment.
    # If anybody knows a better way to do this, please tell me!
    string = string.splitlines()
    i = len(string)-1
    if i >= 0:
        while len(string[i]) > 0 and string[i][0] in ' \t':
            i -= 1
        t = '\n'.join(string[i:])
        if not t.startswith('def '):
            try:
                compile(t+'\n', '', 'single')
                t = t.replace("'", "\\u0027").replace('\n','\\u000a')
                string[i] = "exec compile(ur'%s' + '\\n', '', 'single')"%t
                string = string[:i+1]
            except SyntaxError, msg:
                pass
    return '\n'.join(string)

