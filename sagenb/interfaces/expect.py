import os, StringIO, sys, traceback, tempfile, random

from status import OutputStatus
from format import displayhook_hack
from worksheet_process import WorksheetProcess

import pexpect

###################################################################
# Expect-based implementation
###################################################################
class WorksheetProcess_ExpectImplementation(WorksheetProcess):
    """
    A controlled Python process that executes code.  This is a
    reference implementation.
    """
    def __init__(self, timeout=0.05):
        """
        Initialize this worksheet process.
        """
        self._output_status = OutputStatus('',[],True,None)
        self._expect = None
        self._is_started = False
        self._is_computing = False
        self._timeout = timeout
        self._prompt = "__SAGE__"
        self._filename = ''
        self._tempfiles = []

    def __del__(self):
        import os
        for X in self._tempfiles:
            if os.path.exists(X):
                os.unlink(X)

    def __repr__(self):
        """
        Return string representation of this worksheet process. 
        """
        return "Pexpect implementation of worksheet process"

    ###########################################################
    # Control the state of the subprocess
    ###########################################################
    def interrupt(self):
        """
        Send an interrupt signal to the currently running computation
        in the controlled process.  This may or may not succeed.  Call
        ``self.is_computing()`` to find out if it did. 
        """
        if self._expect is None: return
        self._expect.sendline(chr(3))

    def quit(self):
        """
        Quit this worksheet process.  
        """
        if self._expect is None: return
        self._expect.sendline(chr(3))  # send ctrl-c        
        self._expect.sendline('quit_sage(verbose=%s)'%verbose)
        os.killpg(self._expect.pid, 9)
        os.kill(self._expect.pid, 9)
        self._expect = None
        self._is_started = False
        self._is_computing = False

    def start(self):
        """
        Start this worksheet process running.
        """
        self._expect = pexpect.spawn('python')
        self._is_started = True
        self._is_computing = False
        self._number = 0
        self._read()


    ###########################################################
    # Query the state of the subprocess
    ###########################################################
    def is_computing(self):
        """
        Return True if a computation is currently running in this worksheet subprocess.

        OUTPUT:

            - ``bool``
        """
        return self._is_computing

    def is_started(self):
        """
        Return true if this worksheet subprocess has already been started.

        OUTPUT:

            - ``bool``
        """
        return self._is_started

    ###########################################################
    # Sending a string to be executed in the subprocess
    ###########################################################
    def execute(self, string):
        """
        Start executing the given string in this subprocess.

        INPUT:

            ``string`` -- a string containing code to be executed.
        """
        if self._expect is None:
            self.start()
        self._number += 1
        _, self._filename = tempfile.mkstemp()
        self._tempfiles.append(self._filename)
        open(self._filename,'w').write('import sys;sys.ps1="%s";print "START%s"\n'%(
                                   self._prompt, self._number) +
                             displayhook_hack(string))
        self._expect.sendline('execfile("%s")'%\
                              os.path.abspath(self._filename))
        self._so_far = ''
        self._is_computing = True

    def _read(self):
        try:
            self._expect.expect(pexpect.EOF, self._timeout)
            return True
        except:
            return False

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
        self._read()
        self._so_far += self._expect.before
        import re
        v = re.findall('START%s.*%s'%(self._number,self._prompt), self._so_far, re.DOTALL)
        if len(v) > 0:
            self._is_computing = False
            if os.path.exists(self._filename):
                os.unlink(self._filename)
            s = v[0][len('START%s'%self._number):-len(self._prompt)]
        else:
            v = re.findall('START%s.*'%self._number, self._so_far, re.DOTALL)
            if len(v) > 0:
                s = v[0][len('START%s'%self._number):]
            else:
                s = ''
        s = s.strip().rstrip(self._prompt)
        #if not self._is_computing and os.path.exists(self._filename):
        #    os.unlink(self._filename)
        return OutputStatus(s, [], not self._is_computing)
