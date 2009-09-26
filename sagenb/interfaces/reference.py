import os, StringIO, sys, traceback, tempfile

from status import OutputStatus
from format import displayhook_hack
from worksheet_process import WorksheetProcess

###################################################################
# Reference implementation
###################################################################
class WorksheetProcess_ReferenceImplementation(WorksheetProcess):
    """
    A controlled Python process that executes code.  This is a
    reference implementation.
    """
    def __init__(self):
        """
        Initialize this worksheet process.
        """
        self._output_status = OutputStatus('',[],True,None)
        self._state = {}

    def __repr__(self):
        """
        Return string representation of this worksheet process. 
        """
        return "Reference implementation of worksheet process"

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
        self._state ={}

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
        out, files, tempdir = execute_code(string, self._state)
        self._output_status = OutputStatus(out, files, True, tempdir)

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
        OS = self._output_status
        self._output_status = OutputStatus('',[],True)
        return OS




def execute_code(string, state):
    # print "execute: '''%s'''"%string
    string = displayhook_hack(string)

    # Now execute the code capturing the output and files that are
    # generated.
    back = os.path.abspath('.')
    tempdir = tempfile.mkdtemp()
    s = StringIO.StringIO()
    saved_stream = sys.stdout
    sys.stdout = s
    try:
        os.chdir(tempdir)
        exec string in state
    except Exception, msg:
        traceback.print_exc(file=s)
    finally:
        sys.stdout = saved_stream
        os.chdir(back)
    s.seek(0)
    out = str(s.read())
    files = [os.path.join(tempdir, x) for x in os.listdir(tempdir)]
    return out, files, tempdir
