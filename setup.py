##########################################################
# The setup.py for the Sage Notebook
##########################################################

import os, sys, time
from setuptools import setup

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
      version     = '0.7.3',  # the spkg-dist script assumes single quotes here
      description = 'The Sage Notebook',
      license     = 'GNU Public License (GPL) v2+',
      author      = 'William Stein et al.',
      author_email= 'http://groups.google.com/group/sage-support',
      url         = 'http://www.sagemath.org',
      install_requires = ['twisted>=8.2', 'zope.testbrowser>=3.7.0a1'],
      test_suite = 'sagenb.testing.run_tests.all_tests',
      packages    = ['sagenb',
                     'sagenb.interfaces',
                     'sagenb.misc',                                 
                     'sagenb.notebook',
                     'sagenb.notebook.compress',
                     'sagenb.simple',
                     'sagenb.storage',
                     'sagenb.testing',
                     'sagenb.testing.tests',
                     'sagenb.testing.selenium'
                     ],
      scripts      = ['sagenb/data/jmol/jmol',
                      'sagenb/data/sage3d/sage3d',
                     ],
      package_data = {'sagenb':
                          all_files('sagenb/data', 'sagenb/')
                      },
      )
