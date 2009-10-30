#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Running SageNB Tests

Functions for running SageNB tests. This can also be used a script.

NOTE:

Selenium tests assume a Selenium server is running on port 4444. The
Selenium server can be downloaded from the Selenium `download page
<http://seleniumhq.org/download/>`_ as part of the Selenium RC package
and can be run with `java -jar selenium-server.jar`.

TODO:

- Add extra functionality to this script

- Include a proxy to this script in the Sage scripts repo.
"""
# Developer note:
# The Selenium server cannot be included in the package because
# of the possibility of incompatible libraries and binaries with
# those of the user's browser (e.g., Python, etc.)

from subprocess import Popen
import unittest, os

from tests import test_accounts, test_worksheet, test_worksheet_list

all_tests = unittest.TestSuite((test_accounts.suite,
                               test_worksheet.suite,
                               test_worksheet_list.suite))

def run_tests():
    """
    Runs all SageNB tests. This assumes that a Selenium server is running on port 4444.
    """
    unittest.TextTestRunner(verbosity=2).run(all_tests)

def run_test(suite):
    """
    Runs a test suite. This assumes that a Selenium server is running on port 4444.
    """
    unittest.TextTestRunner(verbosity=2).run(suite)
    
if __name__ == '__main__':
    run_tests()






