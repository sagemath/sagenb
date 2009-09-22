###################################################################
# A blocking reference implementation of worksheet processes
###################################################################

class WorksheetProcess:
    def __init__(self, server=None, ulimit=None):
        self._server = server
        self._ulimit = ulimit
        self._answer = ''
        self._globals = {}

    def __repr__(self):
        return "Worksheet process"

    def __getstate__(self):
        return {'_server':self._server, '_ulimit':self._ulimit}

    ###########################################################
    # Control the state of the subprocess
    ###########################################################
    def interrupt(self, tries=1, quit_on_fail=False):
        """
        Stop any computations running in this process. 
        """
        pass

    def quit(self):
        """
        Stop the subprocess.
        """
        pass

    def start(self):
        """
        Start this subprocess running.
        """
        pass

    ###########################################################
    # Query the state of the subprocess
    ###########################################################
    def is_computing(self):
        """
        Return True if a computation is currently running in this process.
        """
        return False

    def is_started(self):
        """
        Return true if this process has already been started.
        """
        return True

    ###########################################################
    # Sending a string to be executed in the subprocess
    ###########################################################
    def execute(self, string):
        """
        Start executing the given string in this subprocess.
        """
        string = displayhook_hack(string)
        print "Executing '''%s'''"%string

        import StringIO, sys
        s = StringIO.StringIO()
        saved_stream = sys.stdout
        sys.stdout = s
        try:
            exec string in self._globals
        except Exception, msg:
            s.write(str(msg))
        finally:
            sys.stdout = saved_stream
        s.seek(0)
        self._answer = str(s.read())
        print "output: ", self._answer

    ###########################################################
    # Getting the output so far from a subprocess
    ###########################################################
    def output_status(self):
        """
        Return output from the subprocess since this command was last
        called, along with cummulative output since execute was
        called.

        OUTPUT:

            - output (string)
            
            - new output (string)

            - done (bool) whether or not the computation is now done and
              we just returned the last output
        """
        status = OutputStatus(self._answer, [], True)
        self._answer = ''
        return status


class OutputStatus:
    def __init__(self, output, files, done):
        self.output = output
        self.files = files
        self.done = done

    def __repr__(self):
        return "output: %s\nfiles: %s\ndone: %s"%(
            self.output, self.files, self.done)




def displayhook_hack(input):
    # The following is all so the last line (or single lines)
    # will implicitly print as they should, unless they are
    # an assignment.   "display hook"  It's very complicated,
    # but it has to be...
    input = input.splitlines()
    i = len(input)-1
    if i >= 0:
        while len(input[i]) > 0 and input[i][0] in ' \t':
            i -= 1
        t = '\n'.join(input[i:])
        if not t.startswith('def '):
            try:
                compile(t+'\n', '', 'single')
                t = t.replace("'", "\\u0027").replace('\n','\\u000a')
                # IMPORTANT: If you change this line, also change
                # the function format_exception in cell.py
                input[i] = "exec compile(ur'%s' + '\\n', '', 'single')"%t
                input = input[:i+1]
            except SyntaxError, msg:
                pass
    return '\n'.join(input)


"""
NOTES:

Old code looked like this:

        input = self.synchronize(input)

        # This magic comment at the very start of the file allows utf8
        # characters in the file
        input = '# -*- coding: utf_8 -*-\n' + input

        open(tmp,'w').write(input)
        
        cmd = 'execfile("%s")\n'%os.path.abspath(tmp)
        # Signal an end (which would only be seen if there is an error.)
        cmd += 'print "\\x01r\\x01e%s"'%self.synchro()



Also, this wrapped things so it would print:

        input = input.split('\n')

        # The following is all so the last line (or single lines)
        # will implicitly print as they should, unless they are
        # an assignment.   "display hook"  It's very complicated,
        # but it has to be...
        i = len(input)-1
        if i >= 0:
            while len(input[i]) > 0 and input[i][0] in ' \t':
                i -= 1
            t = '\n'.join(input[i:])
            if not t.startswith('def '):
                try:
                    compile(t+'\n', '', 'single')
                    t = t.replace("'", "\\u0027").replace('\n','\\u000a')
                    # IMPORTANT: If you change this line, also change
                    # the function format_exception in cell.py
                    input[i] = "exec compile(ur'%s' + '\\n', '', 'single')"%t
                    input = input[:i+1]
                except SyntaxError, msg:
                    pass
        input = '\n'.join(input)
        return input



    def _process_output(self, s):
        s = re.sub('\x08.','',s)
        s = self._strip_synchro_from_start_of_output(s)
        if SAGE_ERROR in s:
            i = s.rfind('>>>')
            if i >= 0:
                return s[:i-1]
        # Remove any control codes that might have not got stripped out.
        return s.replace(SAGE_BEGIN,'').replace(SAGE_END,'').replace(SC,'')

        
"""
