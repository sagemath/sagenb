##########################################################
# The setup.py for the Sage Notebook
##########################################################

import os, sys, time
from distutils.core import setup

def all_files(dir, lstrip):
    """
    Return list of all filenames in the given directory, with lstrip
    stripped from the left of the filenames.
    """
    X = []
    for F in os.listdir(dir):
        ab = dir+'/'+F
        if os.path.isfile(ab):
            X.append((ab).lstrip(lstrip))
        elif os.path.isdir(ab):
            X.extend(all_files(ab, lstrip))
    return X
    

code = setup(name = 'sagenb',
      version     =  '0.1.8',
      description = 'The Sage Notebook',
      license     = 'GNU Public License (GPL) v2+',
      author      = 'William Stein et al.',
      author_email= 'http://groups.google.com/group/sage-support',
      url         = 'http://www.sagemath.org',
      packages    = ['sagenb',
                     'sagenb.interfaces',
                     'sagenb.misc',                                          
                     'sagenb.notebook',
                     'sagenb.notebook.compress',
                     'sagenb.simple'
                     ],
      package_data = {'sagenb':all_files('sagenb/data', 'sagenb/')}
      )



