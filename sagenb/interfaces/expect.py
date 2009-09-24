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
    def __init__(self):
        """
        Initialize this worksheet process.
        """
        self._output_status = OutputStatus('',[],True,None)
        self._expect = None
        self._is_started = False
        self._is_computing = False

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
        self._expect = pexpect.spawn('python -u')
        self._is_started = True
        self._is_computing = False
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
            
        #n = random.randrange(2**256)
        #self._start_marker = str(n-2)
        #self._done_marker = str(n)
#        self._so_far = ''
        #string = 
##         cmd = """
## sys.stdout=open('output','w')        
## try:
##     exec r'''%s'''
## except Exception, msg:
##     traceback.print_exc(file=sys.stdout)
## """%string        
##         #string = "%s\n%s\n%s+1"%(n-2, string, n-1)
##         print cmd

        fd, name = tempfile.mkstemp()
        open(name,'w').write(string)
        self._so_far = ''
        self._expect.sendline('execfile("%s")'%name)
        self._is_computing = True

    def _read(self):
        try:
            self._expect.expect('>>>', 0.1)
            return True
        except:
            print "read timeout"
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
        if self._expect is None or not self._is_computing:
            return OutputStatus('',[],True)
        
        if self._read():
            self._is_computing = False

        self._so_far += self._expect.before
        i = self._so_far.find('\n')
        if i != -1:
            s = self._so_far[i:].lstrip()
            if not self._is_computing:
                j = s.rfind('\n')
                if j != -1:
                    s = s[:j-2]
        else:
            s = ''
        
        return OutputStatus(s, [], not self._is_computing)
