"""
HTML Test Runner

This is a test runner for use with Python's `unit testing framework`_.
A replacement for the standard :class:`unittest.TextTestRunner`, it
generates a HTML report of the test results.

.. _unit testing framework: http://docs.python.org/library/unittest.html

The simplest way to use :module:`HTMLTestRunner` is to invoke its main
method:

    import unittest
    import HTMLTestRunner

    ... define your tests ...

    if __name__ == '__main__':
        HTMLTestRunner.main()

For more customization options, instantiate a :class:`HTMLTestRunner`
object:

    # output to a file
    fp = file('my_report.html', 'wb')
    runner = HTMLTestRunner.HTMLTestRunner(
                stream=fp,
                title='My unit test',
                description='Unit test report by HTMLTestRunner.'
                )

    # run the test
    runner.run(my_test_suite)

AUTHORS:

- The original version is Wai Yip Tung's HTMLTestRunner_, which is
  available under a modified BSD license.

.. _HTMLTestRunner: http://tungwaiyip.info/software/HTMLTestRunner.html
"""


# The original license.
"""
------------------------------------------------------------------------
Copyright (c) 2004-2006, Wai Yip Tung
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

* Redistributions of source code must retain the above copyright notice,
  this list of conditions and the following disclaimer.
* Redistributions in binary form must reproduce the above copyright
  notice, this list of conditions and the following disclaimer in the
  documentation and/or other materials provided with the distribution.
* Neither the name Wai Yip Tung nor the names of its contributors may be
  used to endorse or promote products derived from this software without
  specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER
OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""


# TODO and CHANGES.
"""
TODO

 * Stabilize table width with "overflow: auto;".
 * Support multiple results tables (e.g., for doctests).
 * Use a backend server to select, run, and monitor live tests.

CHANGES

#7390 (added to sagenb 0.4):

 * Use Jinja2.
 * Use jQuery.
 * Added hide, show, toggle options.
 * Output and tracebacks are inline.
 * Use Pygments to highlight tracebacks.

0.8.1:

 * Thank you for Wolfgang Borgert's patch.
 * Validated XHTML.
 * Added description of test classes and test cases.

0.8.0:

 * Define Template_mixin class for customization.
 * Workaround a IE 6 bug that it does not treat <script> block as CDATA.

0.7.1:

 * Back port to Python 2.3. Thank you Frank Horowitz.
 * Fix missing scroll bars in detail log. Thank you Podi.
"""

import datetime, os, StringIO, sys, unittest

import jinja2
from sagenb.misc.misc import DATA
from sagenb.notebook.template import template

from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import get_formatter_by_name

#from pygments.styles import STYLE_MAP
# ['manni', 'colorful', 'murphy', 'autumn', 'bw', 'pastie', 'native',
# 'perldoc', 'borland', 'trac', 'default', 'fruity', 'vs', 'emacs',
# 'friendly']
PYGMENTS_STYLE = 'colorful'


# IE doesn't respect max-width in tables, so we use a fixed layout
# instead.
IE_STYLE_FIX = jinja2.Template(r"""
<!--[if IE]>
<style type="text/css">
.results {
    table-layout: fixed;
    width: auto;
}
.results td {
    width: 5%;
}
td.left {
    width: 65%;
}
.spanner {
    width: 35%;
}
</style>
<![endif]-->
""")

REPORT_CASE_TMPL = jinja2.Template(r"""
      <tr id="{{ case_id }}" class="{{ case_class }} case">
        <td class="case left">{{ desc }}</td>
        <td class="pass">{{ passes }}</td>
        <td class="fail">{{ failures }}</td>
        <td class="error">{{ errors }}</td>
        <td class="count">{{ count }}</td>
        <td class="hide">H</td>
        <td class="show">S</td>
        <td class="toggle">T</td>
      </tr>
""")

REPORT_TEST_TMPL = jinja2.Template(r"""
      <tr id="{{ test_id }}" class="{{ test_class }} {{ case_id }} test">
        <td class="test left">
          {{ desc }}
          <pre class="out_trace">{{ out_trace }}</pre>
        </td>
        <td colspan="8" class="spanner">
          {{ status }}
        </td>
      </tr>
""")


class OutputRedirector(object):
    """
    Redirect stdout and stderr.  We use a redirector to capture output
    during testing.  Output sent to sys.stdout and sys.stderr are
    automatically captured.  But in some cases, sys.stdout is already
    cached before HTMLTestRunner is invoked (e.g., calling
    logging.basicConfig).  To capture that output, we use the
    redirectors for the cached stream.  For example,

    >>> logging.basicConfig(stream=HTMLTestRunner.stdout_redirector)
    """
    def __init__(self, fp):
        self.fp = fp

    def write(self, s):
        self.fp.write(s)

    def writelines(self, lines):
        self.fp.writelines(lines)

    def flush(self):
        self.fp.flush()

stdout_redirector = OutputRedirector(sys.stdout)
stderr_redirector = OutputRedirector(sys.stderr)


class _TestResult(unittest.TestResult):
    """
    A pure representation of unittest results.  It lacks the output
    and reporting abilities of unittest._TextTestResult.
    """
    # Status enums.
    PASS = 0
    FAIL = 1
    ERROR = 2

    def __init__(self, verbosity=1):
        """
        Initialize variables.  In particular, self.result is a list
        of 4-tuples:

        ( result code, TestCase object, Test output, stack trace )

        The result code is PASS, FAIL, or ERROR.  Test output is a
        byte string.
        """
        unittest.TestResult.__init__(self)
        self.stdout0 = None
        self.stderr0 = None
        self.success_count = 0
        self.failure_count = 0
        self.error_count = 0
        self.total_count = 0
        self.verbosity = verbosity
        self.result = []

    def startTest(self, test):
        """
        Set up output capture.

        Called when the test case test is about to be run.  The
        default implementation simply increments the instance’s
        testsRun counter.
        """
        unittest.TestResult.startTest(self, test)
        # Just one buffer for both stdout and stderr.
        self.outputBuffer = StringIO.StringIO()
        stdout_redirector.fp = self.outputBuffer
        stderr_redirector.fp = self.outputBuffer
        self.stdout0 = sys.stdout
        self.stderr0 = sys.stderr
        sys.stdout = stdout_redirector
        sys.stderr = stderr_redirector

    def complete_output(self):
        """
        Disconnect output redirection and return buffer.  Safe to call
        multiple times.
        """
        if self.stdout0:
            sys.stdout = self.stdout0
            sys.stderr = self.stderr0
            self.stdout0 = None
            self.stderr0 = None
        return self.outputBuffer.getvalue()

    def stopTest(self, test):
        """
        Called after the test case test has been executed, regardless
        of the outcome.  The default implementation does nothing.

        We disconnect stdout.  Usually one of addSuccess, addError or
        addFailure would have been called, but there are some unittest
        paths that can bypass these.  This method is guaranteed to be
        called.
        """
        self.complete_output()

    def addSuccess(self, test):
        """
        Called when the test case test succeeds.  The default
        implementation does nothing.
        """
        self.success_count += 1
        self.total_count += 1
        unittest.TestResult.addSuccess(self, test)

        output = self.complete_output()
        self.result.append((self.__class__.PASS, test, output, ''))

        if self.verbosity > 1:
            sys.stderr.write('ok ')
            sys.stderr.write(str(test))
            sys.stderr.write('\n')
        else:
            sys.stderr.write('.')

    def addError(self, test, err):
        """
        Called when the test case test raises an unexpected exception
        err is a tuple of the form returned by sys.exc_info(): (type,
        value, traceback).

        The default implementation appends a tuple (test,
        formatted_err) to the instance’s errors attribute, where
        formatted_err is a formatted traceback derived from err.
        """
        self.error_count += 1
        self.total_count += 1
        unittest.TestResult.addError(self, test, err)
        _, _exc_str = self.errors[-1]
        output = self.complete_output()
        self.result.append((self.__class__.ERROR, test, output, _exc_str))
        if self.verbosity > 1:
            sys.stderr.write('E  ')
            sys.stderr.write(str(test))
            sys.stderr.write('\n')
        else:
            sys.stderr.write('E')

    def addFailure(self, test, err):
        """
        Called when the test case test signals a failure. err is a
        tuple of the form returned by sys.exc_info(): (type, value,
        traceback).

        The default implementation appends a tuple (test,
        formatted_err) to the instance’s failures attribute, where
        formatted_err is a formatted traceback derived from err.
        """
        self.failure_count += 1
        self.total_count += 1
        unittest.TestResult.addFailure(self, test, err)
        _, _exc_str = self.failures[-1]
        output = self.complete_output()
        self.result.append((self.__class__.FAIL, test, output, _exc_str))
        if self.verbosity > 1:
            sys.stderr.write('F  ')
            sys.stderr.write(str(test))
            sys.stderr.write('\n')
        else:
            sys.stderr.write('F')


class HTMLTestRunner(object):
    """
    A unittest test runner that generates an HTML report of the test
    results.
    """
    def __init__(self, stream=sys.stdout, verbosity=1, title=None,
                 description=None):
        """
        Initialize variables.
        """
        self.stream = stream
        self.verbosity = verbosity
        self.title = title
        self.description = description

        # Set up Pygments syntax highlighting.
        self.formatter = get_formatter_by_name('html', noclasses=True,
                                               style=PYGMENTS_STYLE)
        self.trace_lexer = get_lexer_by_name('pytb')

    def run(self, test):
        """
        Run the given test case or test suite, generate a report,
        write the report, and return the results.
        """
        result = _TestResult(self.verbosity)

        self.start_time = datetime.datetime.now()
        test(result)
        self.stop_time = datetime.datetime.now()
        self.elapsed_time = self.stop_time - self.start_time
        print >>sys.stderr, '\nTime Elapsed: %s' % self.elapsed_time

        report = self.generate_report(result)
        self.stream.write(report.encode('utf8'))

        return result

    def sort_result(self, result_list):
        """
        Return the test results grouped by case.
        """
        case_map = {}
        case_types = []

        for status, test_case, output, trace in result_list:
            case_type = test_case.__class__

            if not case_map.has_key(case_type):
                case_map[case_type] = []
                case_types.append(case_type)

            case_map[case_type].append((status, test_case, output, trace))

        return [(typ, case_map[typ]) for typ in case_types]

    def generate_report(self, result):
        """
        Return a HTML report with the results of all cases and tests.
        """
        # Jinja template dictionary.
        template_dict = {}

        template_dict['title'] = jinja2.escape(self.title)
        template_dict['description'] = jinja2.escape(self.description)
        template_dict['sagenb_version'] = None
        template_dict['start_time'] = str(self.start_time)[:19]
        template_dict['stop_time'] = str(self.stop_time)[:19]
        template_dict['elapsed_time'] = self.elapsed_time
        template_dict['pass_total'] = result.success_count
        template_dict['fail_total'] = result.failure_count
        template_dict['error_total'] = result.error_count
        template_dict['count_total'] = result.total_count

        rows = []
        sorted_result = self.sort_result(result.result)

        # Iterate over cases.
        for i, (case_type, case_results) in enumerate(sorted_result):
            # Stats for this case.
            passes = 0
            failures = 0
            errors = 0
            for status, test_case, output, trace in case_results:
                if status == _TestResult.PASS:
                    passes += 1
                elif status == _TestResult.FAIL:
                    failures += 1
                else:
                    errors += 1

            # Case description.
            if case_type.__module__ == '__main__':
                name = case_type.__name__
            else:
                name = '%s.%s' % (case_type.__module__, case_type.__name__)
            doc = case_type.__doc__ and case_type.__doc__.split('\n')[0] or ''
            desc = jinja2.escape(doc and '%s: %s' % (name, doc) or name)

            case_id = name.replace('.', '-') + '_%d' % i
            case_class = failures > 0 and 'case_fail' or errors > 0 and 'case_error' or 'case_pass'
            count = passes + failures + errors

            rows.append(REPORT_CASE_TMPL.render(locals()))

            # Iterate over this case's tests.
            for j, (status, test_case, output, trace) in enumerate(case_results):
                self.report_for_one_test(rows, case_id, j, status,
                                         test_case, output, trace)

        template_dict['test_cases_and_tests'] = '\n'.join(rows)

        # Make the report self-contained.
        stylesheet = template(os.path.join('css', 'test_report.css'))
        template_dict['stylesheet'] = '<style type="text/css"><!--\n' + stylesheet + '\n--></style>'
        template_dict['stylesheet'] += IE_STYLE_FIX.render()

        jquery = open(os.path.join(DATA,
                                   'jquery/jquery-1.3.2.min.js'), 'r').read()
        template_dict['javascript'] = '<script type="text/javascript">\n' + jquery + '\n</script>'
        return template(os.path.join('html', 'test_report.html'),
                        **template_dict)

    def report_for_one_test(self, rows, case_id, test_num, status,
                            test_case, output, trace):
        """
        Generate the HTML for one test's results.
        """
        # Test description.
        name = test_case.id().split('.')[-1]
        test_id = name + '_%d' % test_num

        doc = test_case.shortDescription() or ''
        desc = jinja2.escape(doc and ('%s: %s' % (name, doc)) or name)

        # Include output, syntax-highlight tracebacks.
        out_trace = ''
        for x in [output, trace]:
            if isinstance(x, str):
                x = unicode(x.encode('string_escape'))
                # x = x.decode('latin-1')
        trace = highlight(trace, self.trace_lexer, self.formatter)
        out_trace = jinja2.escape(output) + jinja2.Markup(trace)

        test_class = ''
        if status == _TestResult.PASS:
            status = 'pass'
            test_class += 'hidden '
        elif status == _TestResult.FAIL:
            status = 'fail'
        else:
            status = 'error'            

        test_class += 'test_' + status
        rows.append(REPORT_TEST_TMPL.render(locals()))


##############################################################################
# Facilities for running tests from the command line
##############################################################################

# Note: Reuse unittest.TestProgram to launch test. In the future we
# may build our own launcher to support more specific command line
# parameters like test title, CSS, etc.
class TestProgram(unittest.TestProgram):
    """
    A variation of the unittest.TestProgram. Please refer to the base
    class for command line parameters.
    """
    def runTests(self):
        # Pick HTMLTestRunner as the default test runner.  The base
        # class's testRunner parameter is not useful, because it means
        # we have to instantiate HTMLTestRunner before we know
        # self.verbosity.
        if self.testRunner is None:
            self.testRunner = HTMLTestRunner(verbosity=self.verbosity)
        unittest.TestProgram.runTests(self)

main = TestProgram


##############################################################################
# Executing this module from the command line
##############################################################################

if __name__ == "__main__":
    main(module=None)
