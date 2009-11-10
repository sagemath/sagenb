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

from sagenb.misc.misc import browser

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
    
def run_and_report(suite=all_tests, verbosity=2, report_filename='report.html',
                   title='Sage Notebook Tests',
                   description='Selenium test results',
                   open_viewer=True):
    """
    Runs a test suite and generates a HTML report with the outcome
    (pass, fail, or error) and output, including any tracebacks, for
    each test, plus overall statistics.  This assumes that a Selenium
    server is running on port 4444.

    INPUT:

    - ``suite`` - a TestSuite instance (default: all_tests); the test
      suite to run

    - ``verbosity`` - an integer (default: 2); how verbosely to report
      instantaneous test results

    - ``report_filename`` - a string (default: 'report.html'); the
      report's filename

    - ``title`` - a string (default: 'Sage Notebook Tests'); the
      report's title

    - ``description`` - a string (default: 'Selenium test results'); a
      description included near the beginning of the report

    - ``open_viewer`` - a boolean (default: True); whether to open
      the report in a web browser
    """
    from HTMLTestRunner import HTMLTestRunner

    report_fd = open(report_filename, 'w')
    runner = HTMLTestRunner(verbosity = verbosity, stream = report_fd,
                            title = title, description = description)
    runner.run(suite)

    if open_viewer:
        Popen(browser() + ' ' + os.path.abspath(report_filename), shell=True)


if __name__ == '__main__':
    run_tests()






