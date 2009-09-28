import os, StringIO, sys, traceback, tempfile, random, shutil

from status import OutputStatus
from format import displayhook_hack
from worksheet_process import WorksheetProcess
from sagenb.misc.misc import (walltime,
                              set_restrictive_permissions, set_permissive_permissions)


import pexpect


###################################################################
# Expect-based implementation
###################################################################
class WorksheetProcess_ExpectImplementation(WorksheetProcess):
    """
    A controlled Python process that executes code using expect.

    INPUT:
        - ``process_limits`` -- None or a ProcessLimits objects as defined by
          the ``sagenb.interfaces.ProcessLimits`` object.
    """
    def __init__(self,
                 process_limits = None,
                 timeout = 0.05,
                 python = 'python'):
        """
        Initialize this worksheet process.
        """
        self._output_status = OutputStatus('', [], True)
        self._expect = None
        self._is_started = False
        self._is_computing = False
        self._timeout = timeout
        self._prompt = "__SAGE__"
        self._filename = ''
        self._all_tempdirs = []
        self._process_limits = process_limits
        self._max_walltime = None
        self._start_walltime = None
        self._data_dir = None
        self._python = python

        if process_limits:
            u = ''
            if process_limits.max_vmem is not None:
                u += ' -v %s'%(int(process_limits.max_vmem)*1000)
            if process_limits.max_cputime is not None:
                u += ' -t %s'%(int(process_limits.max_cputime))
            if process_limits.max_processes is not None:
                u += ' -u %s'%(int(process_limits.max_processes))            
            # prepend ulimit options
            if u == '':
                self._ulimit = u
            else:
                self._ulimit = 'ulimit %s'%u
        else:
            self._ulimit = ''

        if process_limits and process_limits.max_walltime:
            self._max_walltime = process_limits.max_walltime

    def command(self):
        return self._python
        # TODO: The following simply doesn't work -- this is not a valid way to run
        # ulimited.  Also we should check if ulimit is available before even
        # doing this.   
        return '&&'.join([x for x in [self._ulimit, self._python] if x])

    def __del__(self):
        try: self._cleanup_tempfiles()
        except: pass
        try: self._cleanup_data_dir()
        except: pass

    def _cleanup_data_dir(self):
        if self._data_dir is not None:
            set_restrictive_permissions(self._data_dir)

    def _cleanup_tempfiles(self):
        for X in self._all_tempdirs:
            try: shutil.rmtree(X, ignore_errors=True)
            except: pass

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
        try:
            self._expect.sendline(chr(3))
        except: pass

    def quit(self):
        """
        Quit this worksheet process.  
        """
        if self._expect is None: return
        try:
            self._expect.sendline(chr(3))  # send ctrl-c        
            self._expect.sendline('quit_sage()')
        except:
            pass
        try:
            os.killpg(self._expect.pid, 9)
            os.kill(self._expect.pid, 9)
        except OSError:
            pass
        self._expect = None
        self._is_started = False
        self._is_computing = False
        self._start_walltime = None
        self._cleanup_tempfiles()
        self._cleanup_data_dir()

    def start(self):
        """
        Start this worksheet process running.
        """
        print "Starting worksheet with command: '%s'"%self.command()
        self._expect = pexpect.spawn(self.command())
        self._is_started = True
        self._is_computing = False
        self._number = 0
        self._read()
        self._start_walltime = walltime()


    def update(self):
        """
        This should be called periodically by the server processes.
        It does things like checking for timeouts, etc.
        """
        self._check_for_walltimeout()

    def _check_for_walltimeout(self):
        """
        Check if the walltimeout has been reached, and if so, kill
        this worksheet process.
        """
        if (self._is_started and \
            self._max_walltime and self._start_walltime and \
            walltime() - self._start_walltime >  self._max_walltime):
            self.quit()

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
    def get_tmpdir(self):
        """
        Return two strings (local, remote), where local is the name
        of a pre-created temporary directory, and remote is the name
        of the same directory but on the machine on which the actual
        worksheet process is running.

        OUTPUT:

            - local directory

            - remote directory
        """
        # In this implementation the remote process is just running
        # as the same user on the local machine.
        s = tempfile.mkdtemp()
        return (s, s)
    
    def execute(self, string, data=None):
        """
        Start executing the given string in this subprocess.

        INPUT:

            - ``string`` -- a string containing code to be executed.

            - ``data`` -- a string or None; if given, must specify an
              absolute path on the server host filesystem.   This may
              be ignored by some worksheet process implementations.
        """
        if self._expect is None:
            self.start()
        self._number += 1

        local, remote = self.get_tmpdir()

        if data is not None:
            # make a symbolic link from the data directory into local tmp directory
            self._data = os.path.split(data)[1]
            self._data_dir = data
            set_permissive_permissions(data)
            os.symlink(data, os.path.join(local, self._data))
        else:
            self._data = ''
            
        self._tempdir = local
        sage_input = '_sage_input_%s.py'%self._number
        self._filename = os.path.join(self._tempdir, sage_input)
        self._so_far = ''
        self._is_computing = True

        self._all_tempdirs.append(self._tempdir)
        # The magic comment at the very start of the file allows utf8 characters.
        open(self._filename,'w').write(
            '# -*- coding: utf_8 -*-\nimport sys;sys.ps1="%s";print "START%s"\n'%(
            self._prompt, self._number) + displayhook_hack(string))
        try:
            self._expect.sendline('\nimport os;os.chdir("%s");\nexecfile("%s")'%(
                              remote, sage_input))
        except OSError, msg:
            self._is_computing = False
            self._so_far = str(msg)


    def _read(self):
        try:
            self._expect.expect(pexpect.EOF, self._timeout)
            # got EOF subprocess must have crashed; cleanup
            self.quit()
        except:
            pass

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
        if self._expect is None:
            self._is_computing = False
        else:
            self._so_far += self._expect.before
            
        import re
        v = re.findall('START%s.*%s'%(self._number,self._prompt), self._so_far, re.DOTALL)
        if len(v) > 0:
            self._is_computing = False
            s = v[0][len('START%s'%self._number):-len(self._prompt)]
        else:
            v = re.findall('START%s.*'%self._number, self._so_far, re.DOTALL)
            if len(v) > 0:
                s = v[0][len('START%s'%self._number):]
            else:
                s = ''
        s = s.strip().rstrip(self._prompt)

        files = []
        if not self._is_computing and os.path.exists(self._tempdir):
            files = [os.path.join(self._tempdir, x) for x in os.listdir(self._tempdir) if x != self._data]
            files = [x for x in files if x != self._filename]
            
        return OutputStatus(s, files, not self._is_computing)


class WorksheetProcess_RemoteExpectImplementation(WorksheetProcess_ExpectImplementation):
    """
    This worksheet process class implements computation of worksheet
    code as another user possibly on another machine, with the
    following requirements:

       1. ssh keys are setup for passwordless login from the server to the
          remote user account, and

       2. there is a shared filesystem that both users can write to,
          which need not be mounted in the same location.

    VULNERABILITIES: It is possible for a malicious user to see code
    input by other notebook users whose processes are currently
    running.  However, the moment any calculation finishes, the file
    results are moved back to the the notebook server in a protected
    placed, and everything but the input file is deleted, so the
    damage that can be done is limited.  In particular, users can't
    simply browse much from other users.

    INPUT:

        - ``user_at_host`` -- a string of the form 'username@host'
          such that 'ssh user@host' does not require a password, e.g.,
          setup by typing ``ssh-keygen`` as the notebook server and
          worksheet users, then putting ~/.ssh/id_rsa.pub as the file
          .ssh/authorized_keys.  You must make the permissions of
          files and directories right.
          
        - ``local_directory`` -- name of a directory on the local
          computer that the notebook server can write to, which the
          remote computer also has read/write access to, e.g., /tmp/

        - ``remote_directory`` -- (default: None) if the local_directory is
          mounted on the remote machine as a different directory name,
          this string is that directory name. 

        - ``process_limits`` -- None or a ProcessLimits objects as defined by
          the ``sagenb.interfaces.ProcessLimits`` object.
    """
    def __init__(self,
                 user_at_host,
                 remote_python,
                 local_directory = os.path.sep + 'tmp',
                 remote_directory = None,
                 process_limits = None,
                 timeout = 0.05):
        WorksheetProcess_ExpectImplementation.__init__(self, process_limits, timeout=timeout)
        self._user_at_host = user_at_host
        self._local_directory = local_directory
        if remote_directory is None:
            remote_directory = local_directory
        self._remote_directory = remote_directory
        self._remote_python = remote_python

    def command(self):
        if self._ulimit == '':
            c = self._remote_python
        else:
            c = '&&'.join([x for x in [self._ulimit, self._remote_python] if x])
        return 'ssh -t %s "%s"'%(self._user_at_host, c)
        
    def get_tmpdir(self):
        """
        Return two strings (local, remote), where local is the name
        of a pre-created temporary directory, and remote is the name
        of the same directory but on the machine on which the actual
        worksheet process is running.
        """
        # In this implementation the remote process is just running
        # as the same user on the local machine.
        local = tempfile.mkdtemp(dir=self._local_directory)
        remote = os.path.join(self._remote_directory, local[len(self._local_directory):].lstrip(os.path.sep))
        # Make it so local is world read/writable -- so that the remote worksheet
        # process can write to it.
        set_permissive_permissions(local)
        return (local, remote)


