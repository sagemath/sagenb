#! /usr/bin/python

# Original script by Ondrej Certik: http://git.661346.n2.nabble.com/importing-mercurial-patch-td1484627.html

import os
import sys
import re
import tempfile

def run(cmd):
    print(cmd)
    execcode=os.system(cmd)
    if execcode != 0:
        raise RuntimeError

patch = sys.argv[1]
args = ' '.join(sys.argv[2:])
print('p {}'.format(patch))
print('args {}'.format(args))

with open(patch) as f:
    p = f.read()
author = re.search("# User (.+)", p).groups()[0]
p = p.split("\n")
while not p[0].startswith("# Parent"):
    del p[0]
i = 1
while not p[i].startswith("diff -r "):
    i += 1
commit_message = "\n".join(p[1:i])
_, filename = tempfile.mkstemp()
with open(filename, "w")  as f:
    f.write(commit_message)
print(commit_message)

run("patch %s < %s" %(args,patch))
run("git commit -a --author='%s' -F %s -s" % (author, filename) )
