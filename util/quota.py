"""
This script determines the users that are using more than a certain amount of disk space and makes them "readonly".
"""

from subprocess import check_output
import os
import sys
SERVERDIR = os.path.abspath(sys.argv[1])
HOMEDIR=os.path.join(SERVERDIR,'home','') # end in /
READONLY_FILE=os.path.join(SERVERDIR, 'readonly.txt')
LOG_FILE = os.path.join(SERVERDIR, 'log-size.txt')
MAX=250 # megabytes

s = check_output('du -Lm --max-depth 1 %r'%HOMEDIR, shell=True)
readonly={}
system_users = set(['_sage_','pub','__store__','','admin'])

for line in s.split('\n'):
    if len(line)<len(HOMEDIR):
        continue
    size,user_dir = line.split('\t',1)
    size=int(size)
    if len(line)>0 and size>MAX:
        user = user_dir[len(HOMEDIR):]
        if user not in system_users:
            readonly[user]=size

import logging
logging.basicConfig(format='%(asctime)s %(message)s',filename=LOG_FILE)
logging.warning(sorted(readonly.items(), key=lambda x: x[1], reverse=True))

if os.path.exists(READONLY_FILE):
    with open(READONLY_FILE) as f:
        oldnames=set(i.strip() for i in f.readlines())
else:
    oldnames=None

if set(readonly.keys())!=oldnames:
    logging.warning('writing %r'%READONLY_FILE)
    with open(READONLY_FILE,'w') as f:
        f.write('\n'.join(readonly.keys()))

# for all people over quota:
# - delete all output directories
# check size again.  If still over by 20%, delete DATA directories.
# check size again.
