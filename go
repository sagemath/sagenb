#!/usr/bin/env pynb
import os
os.system('python setup.py install')

import sagenb.notebook.notebook_object as n
n.notebook('sage_notebook', server_pool=[])

