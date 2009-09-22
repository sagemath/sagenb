"""
Worksheet process

AUTHORS:

  - William Stein
"""

#############################################################################
#
#       Copyright (C) 2009 William Stein <wstein@gmail.com>
#  Distributed under the terms of the GNU General Public License (GPL)
#  The full text of the GPL is available at:
#                  http://www.gnu.org/licenses/
#
#############################################################################

class OutputStatus:
    """
    Object that records current status of output from executing some
    code in a worksheet process.  An OutputStatus object has three
    attributes:

            - ``output`` - a string, the output so far
            
            - ``filenames`` -- list of names of files created by this execution

            - ``done`` -- bool; whether or not the computation is now done
    
    """
    def __init__(self, output, filenames, done):
        """
        INPUT:

           - ``output`` -- a string

           - ``filenames`` -- a list of filenames

           - ``done`` -- bool, if True then computation is done, so ``output``
             is complete.
        """
        self.output = output
        self.filenames = filenames
        self.done = done

    def __repr__(self):
        """
        Return string representation of this output status.
        """
        return "Output Status:\n\toutput: %s\n\tfilenames: %s\n\tdone: %s"%(
            self.output, self.filenames, self.done)


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


###################################################################
# Reference implementation
###################################################################
class WorksheetProcess:
    """
    A controlled Python process that executes code.  This is a
    reference implementation.
    """
    def __init__(self):
        """
        Initialize this worksheet process.
        """
        self._output_status = OutputStatus('',[],True)
        self._state = {}

    def __repr__(self):
        """
        Return string representation of this worksheet process. 
        """
        return "Worksheet process"

    def __getstate__(self):
        """
        Used for pickling.  We return an empty state otherwise
        this could not be pickled.
        """
        return {}

    ###########################################################
    # Control the state of the subprocess
    ###########################################################
    def interrupt(self):
        """
        Send an interrupt signal to the currently running computation
        in the controlled process.  This may or may not succeed.  Call
        ``self.is_computing()`` to find out if it did. 
        """
        pass

    def quit(self):
        """
        Quit this worksheet process.  
        """
        pass

    def start(self):
        """
        Start this worksheet process running.
        """
        pass

    ###########################################################
    # Query the state of the subprocess
    ###########################################################
    def is_computing(self):
        """
        Return True if a computation is currently running in this worksheet subprocess.

        OUTPUT:

            - ``bool``
        """
        return False

    def is_started(self):
        """
        Return true if this worksheet subprocess has already been started.

        OUTPUT:

            - ``bool``
        """
        return True

    ###########################################################
    # Sending a string to be executed in the subprocess
    ###########################################################
    def execute(self, string):
        """
        Start executing the given string in this subprocess.

        INPUT:

            ``string`` -- a string containing code to be executed.
        """
        string = displayhook_hack(string)
        import StringIO, sys
        s = StringIO.StringIO()
        saved_stream = sys.stdout
        sys.stdout = s
        try:
            exec string in self._state
        except Exception, msg:
            s.write(str(msg))
        finally:
            sys.stdout = saved_stream
        s.seek(0)
        out = str(s.read())
        self._output_status = OutputStatus(out, [], True)

    ###########################################################
    # Getting the output so far from a subprocess
    ###########################################################
    def output_status(self):
        """
        Return OutputStatus object, which includes output from the
        subprocess from the last executed command up until now,
        information about files that were created, and whether
        computing is now done.

        OUTPUT:

            - ``OutputStatus`` object.
        """
        O = self._output_status
        self._output_status = OutputStatus('',[],True)
        return O

