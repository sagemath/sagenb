# -*- coding: utf-8 -*
import os, shutil

class OutputStatus:
    """
    Object that records current status of output from executing some
    code in a worksheet process.  An OutputStatus object has three
    attributes:

            - ``output`` - a string, the output so far
            
            - ``filenames`` -- list of names of files created by this execution

            - ``done`` -- bool; whether or not the computation is now done
    
    """
    def __init__(self, output, filenames, done, tempdir=None):
        """
        INPUT:

           - ``output`` -- a string

           - ``filenames`` -- a list of filenames

           - ``done`` -- bool, if True then computation is done, so ``output``
             is complete.

           - ``tempdir`` -- (default: None) a filename of a directory; after
             computation is done, the caller is responsible for
             deleting this directory.
        """
        self.output = output
        self.filenames = filenames
        self.done = done
        self.tempdir = tempdir

    def __repr__(self):
        """
        Return string representation of this output status.
        """
        return "Output Status:\n\toutput: '%s'\n\tfilenames: %s\n\tdone: %s"%(
            self.output, self.filenames, self.done)
