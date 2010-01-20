# -*- coding: utf-8 -*
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Running SageNB Tests

Functions for running SageNB tests. This can also be used a script.

NOTE:

The SageNB tests tests assume a Selenium server or Grid hub is running
with the options given in :mod:`sagenb.testing.notebook_test_case` or
set by :func:`setup_tests`.


Selenium server can be downloaded from the Selenium `download page
<http://seleniumhq.org/download/>`_ as part of the Selenium RC package
and can be run with `java -jar selenium-server.jar`.  To set up
Selenium Grid, please visit its `home page
<http://selenium-grid.seleniumhq.org/>`_ for instructions.

TODO:

- Add extra functionality to this script

- Include a proxy to this script in the Sage scripts repo.
"""
# Developer note:
# The Selenium server cannot be included in the package because
# of the possibility of incompatible libraries and binaries with
# those of the user's browser (e.g., Python, etc.)

import unittest

import notebook_test_case
from sagenb.misc.misc import browser
from tests import test_accounts, test_worksheet, test_worksheet_list

CASES = {
    'TestAccounts': test_accounts,
    'TestWorksheet': test_worksheet,
    'TestWorksheetList': test_worksheet_list
    }

all_tests = unittest.TestSuite((test_accounts.suite,
                               test_worksheet.suite,
                               test_worksheet_list.suite))


def setup_tests(address='localhost', secure=False,
                environment='*firefox3 /usr/bin/firefox'):
    """
    Sets selected options for SageNB Selenium tests.

    INPUT:

    - ``address`` - a string (default: 'localhost'); address of the
      network interface at which the notebook server listens.  Do not
      leave this empty; see :mod:`sagenb.testing.notebook_test_case`
      for details.

    - ``secure`` - a boolean (default: False); whether to launch a
      secure notebook server.  Note: Browser security warnings will
      yield failed tests.  To work around these in Firefox, close all
      windows, create a new profile (e.g., `firefox -P selenium`),
      browse to a secure notebook server, accept the certificate, and
      quit.  Then launch the Selenium server with, e.g.,

        java -jar selenium-server -firefoxProfileTemplate $HOME/selenium/firefox

      and run the tests.  A minimal profile template directory can
      contain just the files `cert8.db` and `cert_override.txt`.

    - ``environment`` - a string (default: '*firefox3
      /usr/bin/firefox'); the browser environment in which to run the
      tests.  The path is optional.  However, for the Selenium server
      to have complete control over the launched browser, it's best to
      give the full path to the browser *executable* (i.e., not a
      shell script).

      Possible environments include '*chrome', '*firefox',
      '*firefox3', '*googlechrome', '*iexplore', '*opera', '*safari'.

    EXAMPLES::

        sage: import sagenb.testing.run_tests as rt               # not tested
        sage: env = '*firefox3 /usr/lib64/firefox-3.5.6/firefox'  # not tested
        sage: rt.setup_tests('localhost', True, env)              # not tested
        sage: rt.run_any()                                        # not tested
        sage: rt.setup_tests('localhost', True, '*opera')         # not tested
        sage: rt.run_and_report()                                 # not tested
    """
    # TODO: Add a directory option for parallel testing.
    notebook_test_case.NB_OPTIONS['address'] = address
    notebook_test_case.NB_OPTIONS['secure'] = secure
    notebook_test_case.SEL_OPTIONS['environment'] = environment


def run_any(tests=all_tests, make_report=False, **kwargs):
    """
    Creates and runs an ad hoc test suite from a test name, case,
    suite, or a mixed list thereof.  If no matching tests are found,
    no tests are run.

    INPUT:

    - ``tests`` - a string, :class:`unittest.TestCase`,
      :class:`unittest.TestSuite`, or a mixed list thereof.  Strings
      can be test names, with or without the prefix 'test_'.

    - ``make_report`` - a boolean (default: False); whether to
      generate a HTML report of the test results.

    - ``kwargs`` - a dictionary; additional keyword options to pass to
      :func:`run_suite` or :func:`run_and_report`.

    EXAMPLES::

        sage: import sagenb.testing.run_tests as rt              # not tested
        sage: rt.run_any('simple_evaluation', make_report=True)  # not tested
        sage: rt.run_any(['4088', 'test_3711'], verbosity=1)     # not tested
        sage: rt.run_any('foo', False)                           # not tested
        sage: rt.run_any(rt.test_accounts.TestAccounts)          # not tested
        sage: rt.run_any(make_report=True)                       # not tested
    """
    import inspect
    from_name = unittest.TestLoader().loadTestsFromName
    from_case = unittest.TestLoader().loadTestsFromTestCase

    if not isinstance(tests, list):
        tests = [tests]

    alist = []
    for t in tests:
        if isinstance(t, str):
            if not t.startswith('test_'):
                t = 'test_' + t
            for c in CASES:
                try:
                    alist.append(from_name(c + '.' + t, module = CASES[c]))
                except AttributeError:
                    pass
        elif inspect.isclass(t) and issubclass(t, unittest.TestCase):
            alist.append(from_case(t))
        elif isinstance(t, unittest.TestSuite):
            alist.append(t)

    if alist:
        suite = unittest.TestSuite(alist)
        tot = suite.countTestCases()

        environment = notebook_test_case.SEL_OPTIONS['environment']
        print 'Running %d test%s in environment %s...' % (tot, '' if tot == 1 else 's', environment)

        if make_report:
            run_and_report(suite, environment = environment, **kwargs)
        else:
            run_suite(suite, **kwargs)


def run_suite(suite=all_tests, verbosity=2):
    """
    Runs a test suite.

    For the SageNB test suite, this assumes a Selenium server or Grid
    hub is running with the options given in
    :mod:`sagenb.testing.notebook_test_case` or set by
    :func:`setup_tests`

    INPUT:

    - ``suite`` - a TestSuite instance (default: all_tests); the test
      suite to run

    - ``verbosity`` - an integer (default: 2); how verbosely to report
      instantaneous test results

    EXAMPLES::

        sage: import sagenb.testing.run_tests as rt               # not tested
        sage: rt.run_suite()                                      # not tested
        sage: rt.run_suite(rt.test_worksheet.suite, verbosity=1)  # not tested
    """
    unittest.TextTestRunner(verbosity=verbosity).run(suite)


def run_and_report(suite=all_tests, verbosity=2, report_filename='report.html',
                   title='Sage Notebook Tests',
                   description='Selenium test results',
                   open_viewer=True, **kwargs):
    """
    Runs a test suite and generates a HTML report with the outcome
    (pass, fail, or error) and output, including any tracebacks, for
    each test, plus overall statistics.

    For the SageNB test suite, this assumes a Selenium server or Grid
    hub is running with the options given in
    :mod:`sagenb.testing.notebook_test_case` or set by
    :func:`setup_tests`.

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

    - ``kwargs`` - a dictionary; extra keyword arguments passed to the
      test runner's constructor

    EXAMPLES::

        sage: import sagenb.testing.run_tests as rt             # not tested
        sage: rt.run_and_report()                               # not tested
        sage: rt.run_and_report(report_filename='test1.html')   # not tested
        sage: rt.run_and_report(rt.test_accounts.suite)         # not tested
    """
    from HTMLTestRunner import HTMLTestRunner

    report_fd = open(report_filename, 'w')
    runner = HTMLTestRunner(verbosity = verbosity, stream = report_fd,
                            title = title, description = description,
                            **kwargs)
    runner.run(suite)

    if open_viewer:
        import os, subprocess
        subprocess.Popen(browser() + ' ' + os.path.abspath(report_filename),
                         shell=True)


if __name__ == '__main__':
    run_suite()
