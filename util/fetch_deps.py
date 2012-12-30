#!/usr/bin/env python
"""
Downloads certain (sub)dependencies of sagenb into the given directory
and returns a list of their names. This script is run from dist.sh, and
need not be run independently.
"""
# These are linearly ordered such that no package depends on something
# lower than it in the list (or not in the list).
#
# TODO: Automatically generate this (using distribute internals ?)
required_packages = [ 'zope.interface'
                    , 'twisted>=11.0.0'
                    , 'pytz>=2011n'
                    , 'Babel>=0.9.6'
                    , 'Werkzeug>=0.8.2'
                    , 'speaklater>=1.2'
                    , 'python-openid>=2.2.5'
                    , 'Flask>=0.8'
                    , 'Flask-Silk>=0.1.1'
                    , 'Flask-AutoIndex>=0.4.0'
                    , 'Flask-Babel>=0.8'
                    , 'Flask-OpenID>=1.0.1'
                    , 'webassets>=0.7.1'
                    ]

import os, shutil, sys
from pkg_resources import Requirement
from setuptools.package_index import PackageIndex

def die(message):
    sys.stderr.write(message)
    sys.exit(1)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "Please supply a destination directory for the fetched packages!"
        sys.exit(1)
    dest_dir = os.path.abspath(sys.argv[1])

    print "Fetching packages:"
    pkg_index = PackageIndex()
    with open(os.path.join(dest_dir, 'install_order'), 'w') as fd:
        for pkg in required_packages:
            print "(---  Processing requirement '{0}'".format(pkg)
            dist = pkg_index.fetch_distribution(Requirement.parse(pkg),
                                                dest_dir, True, True)
            if dist is None:
                die("Couldn't find package satisfying '{0}'!".format(pkg))
            print " ---) Fetched {0} {1}".format(dist.project_name,
                    dist.version)
            fd.write(os.path.basename(dist.location) + '\n')
