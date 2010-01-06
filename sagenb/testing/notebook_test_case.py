# -*- coding: utf-8 -*-
"""
Notebook Test Case

This contains the base class for all SageNB test cases.
"""

import copy
import os
import pexpect
import re
import shutil
import signal
import subprocess
import tempfile
import time
import unittest

from selenium.selenium import selenium

# Default options.
NB_OPTIONS = {
    'address': 'localhost',   # Should *not* be left empty.
    'directory': '',          # Set automatically if empty.  Must end
                              # in '.sagenb'.
    'open_viewer': False,
    'port': 8000,
    'secure': False
}
SEL_OPTIONS = {
    'server_host': 'localhost',
    'server_port': 4444,
    'environment': '*firefox3 /usr/bin/firefox',
    'browser_url': ''         # Set automatically if empty.
}

# This is for Google Chrome, which caches '/new_worksheet', for some
# reason.
CACHE_SKIP = 0

KEY_CODES = {
    'tab': 9,
    'enter': 10,
    'shift': 16
}


class NotebookTestCase(unittest.TestCase):
    """
    Base class for SageNB test cases. Contains multiple utility
    functions, and sets up fixtures.
    """
    tags = ('seleniumtest',)

    def cleanup(self):
        nb_dir = self.nb_options['directory']

        if os.path.exists(nb_dir):
            twistd_pid_path = os.path.join(nb_dir, 'twistd.pid')
            if os.path.exists(twistd_pid_path):
                twistd_pid_fd = open(twistd_pid_path, 'r')
                twistd_pid = int(twistd_pid_fd.read())
                try:
                    os.kill(twistd_pid, signal.SIGTERM)
                    os.kill(twistd_pid, signal.SIGKILL)
                except OSError:
                    pass
                twistd_pid_fd.close()
            shutil.rmtree(nb_dir, ignore_errors=True)

    def setUp(self):
        """
        Makes sure that the tests start from a fresh slate, and starts
        the server.
        """
        self.nb_options = copy.deepcopy(NB_OPTIONS)
        self.nb_options['directory'] = (self.nb_options['directory'] or
                                        os.path.join(tempfile.gettempdir(),
                                                     'sagenb_tests.sagenb'))
        self.sel_options = copy.deepcopy(SEL_OPTIONS)

        self.cleanup()
        os.mkdir(self.nb_options['directory'])
        self.start_notebook(initial=True)

        self.selenium = selenium(self.sel_options['server_host'],
                                 self.sel_options['server_port'],
                                 self.sel_options['environment'],
                                 self.sel_options['browser_url'])
        self.selenium.start()
        self.selenium.open("/")

    def start_notebook(self, initial=False):
        """
        Starts the Sage notebook.  If initial is True, then it expects
        to have to enter the initial password twice.
        """
        self._p = pexpect.spawn(self._sage_startup_command())
        if initial:
            self._p.sendline("asdfasdf")
            self._p.sendline("asdfasdf")

        port_re = re.compile(r'http(?:s)?://' + self.nb_options['address'] +
                             r':(\d+)')

        line = self._p.readline()
        while not port_re.search(line):
            line = self._p.readline()

        m = port_re.search(line)
        self.sel_options['browser_url'] = (self.sel_options['browser_url'] or
                                           m.group(0))
        self.sagenb_port = int(m.group(1))

        self._p.expect("Starting factory")

    def _sage_startup_command(self):
        """
        Command to send to pexpect to start the notebook.
        """
        return 'sage -c "notebook(**%r)"' % self.nb_options

    def focus_cell(self, id):
        """
        Moves focus to cell with id ``id``.
        """
        sel = self.selenium
        sel.focus("cell_input_%s" % id)

    def eval_cell(self, id, text, timeout=20000, output=True):
        """
        Evaluates the cell id with input text text.

        If output is True, then the cell output is returned.
        """
        sel = self.selenium
        id = str(id)
        sel.type("cell_input_"+id, text)
        self.evaluate(id)
        self.wait_for_no_active_cells()
        if output:
            return self.get_cell_output(id)

    def evaluate(self, id):
        """
        Triggers evaluation of a given cell.
        """
#        self.shift_enter("cell_input_"+id)
        self.selenium.get_eval('window.evaluate_cell(%s, 0);' % id)

    def _get_cell_output_type(self, id, type='nowrap'):
        out = ''
        try:
            out =  self.selenium.get_eval("window.document.getElementById('cell_output_%s_%s').innerHTML" % (type, id)).strip()
        except:
            pass
        return out

    def get_cell_output(self, id):
        """
        Gets the output of cell id.
        """
        out = ''
        out = self._get_cell_output_type(id, 'nowrap')
        if out == '':
            out = self._get_cell_output_type(id, 'html')

        # Browser contortions. TODO: Simplify this with regular
        # expressions.
        preshrunk = '<pre class="shrunk">'
        PREshrunk = '<PRE class="shrunk">'
        PREshrunk2 = '<PRE class=shrunk>'

        if out.startswith(preshrunk) or out.startswith(PREshrunk):
            out = out[len(preshrunk):-6]
        if out.startswith(PREshrunk2):
            out = out[len(PREshrunk2):-6]

        out = out.strip()
        return out

    def wait_for_no_active_cells(self, timeout=20000):
        """
        Tells Selenium to wait until they're are no active cells on
        the worksheet.
        """
        self.selenium.wait_for_condition("selenium.browserbot.getCurrentWindow().active_cell_list.length == 0", "%s"%timeout)

    def enter(self, locator):
        """
        Presses enter in the element ``locator``.
        """
#        self.selenium.focus(locator)
        self.selenium.key_press(locator, '13')
#        self.selenium.key_press_native(KEY_CODES['enter'])

    def shift_enter(self, locator):
        """
        Presses shift-enter in the element ``locator``.   For example,
        self.shift_enter('cell_input_0')
        """
        sel = self.selenium
#        self.selenium.focus(locator)
        sel.shift_key_down()
#        sel.key_down_native(KEY_CODES['shift'])
        self.enter(locator)
        sel.shift_key_up()
#        sel.key_up_native(KEY_CODES['shift'])

    def tab(self, locator):
        """
        Presses tab in the element ``locator``.
        """
        self.selenium.focus(locator)
        self.selenium.key_press_native(KEY_CODES['tab'])

    def introspect(self, id):
        """
        Evaluates introspection in the given cell.
        """
#        self.tab('cell_input_%s' % id)
        self.selenium.get_eval('window.set_cursor_position(window.get_cell(%s), 100);' % id)
        self.selenium.get_eval('window.evaluate_cell_introspection(%s, null, null);' % id)

    def save_and_quit(self):
        """
        Save and close the current worksheet and wait until we
        arrive at the main page.
        """
        sel = self.selenium
        sel.click("//button[@name='button_save' and @onclick='save_worksheet_and_close();']")
        sel.wait_for_page_to_load("30000")
        self.wait_for_title('Active Worksheets -- Sage')

    def wait_for_title(self, title):
        """
        Tells Selenium to wait until the title of the page has changed
        to title since it doesn't recognize many of the page reloads
        in the Sage notebook.
        """
        self.selenium.wait_for_condition('selenium.browserbot.getCurrentWindow().document.title.replace(/^\s+|\s+$/g, "") == "%s"'%title, 30000)

    def rename_worksheet(self, new_title):
        """
        Renames the current worksheet.
        """
        sel = self.selenium
        sel.click("worksheet_title")
        # Note: These locators also detect modal prompts that have
        # been hidden, but not deleted.
        sel.type('//div[contains(@class,"modal-prompt")]//input[@type="text"]', new_title)
        sel.click('//div[contains(@class, "modal-prompt")]/form/div[@class="button-div"]/button[@type="submit"]')
        sel.wait_for_condition('selenium.browserbot.getCurrentWindow().$("#worksheet_title").text() == "%s"' % new_title, 5000)

    def register_user(self, username, password='asdfasdf'):
        """
        Registers a new user for the Sage notebook.

        This assumes that you're at the login page.
        """
        sel = self.selenium
        sel.click("id=register-link")
        sel.wait_for_page_to_load(30000)
        self.wait_for_title("Sign up -- Sage")

        sel.type("username", username)
        sel.type("password", password)
        sel.type("retype_password", password)
        sel.click("id=create-account-button")
        sel.wait_for_page_to_load(30000)
        self.wait_for_title('Sign in -- Sage')
        self.assertTrue(sel.is_text_present('regexp:Congratulations'))

    def login_as(self, username, password='asdfasdf'):
        """
        Login as user username.  This assumes that you're at
        the login page.
        """
        self.username = username
        self.password = password

        sel = self.selenium
        sel.type("email", self.username)
        sel.type("password", self.password)
        sel.click("//button[text()='Sign in']")
        sel.wait_for_page_to_load("30000")

    def logout(self):
        """
        This logs the user out by clicking the 'Sign out' link.
        """
        self.username = None
        self.password = None

        sel = self.selenium
        sel.click("link=Sign out")
        sel.wait_for_page_to_load("30000")

    def go_home(self):
        """
        Open the currently logged-in user's home page (i.e., active
        worksheet list).
        """
        sel = self.selenium
        sel.open('/home/' + self.username)
        sel.wait_for_page_to_load("30000")

    def create_new_worksheet(self, title = "My New Worksheet"):
        sel = self.selenium
        self.go_home()

        global CACHE_SKIP
        CACHE_SKIP += 1
        sel.open('/new_worksheet?%d' % CACHE_SKIP)
        sel.wait_for_page_to_load("30000")
        self.assert_(sel.is_element_present('//a[@id="worksheet_title" and contains(text(),"Untitled")]'))
        sel.type('//div[contains(@class,"modal-prompt")]//input[@type="text"]', title)
        sel.click('//div[contains(@class, "modal-prompt")]/form/div[@class="button-div"]/button[@type="submit"]')
        sel.wait_for_condition('selenium.browserbot.getCurrentWindow().$("#worksheet_title").text() == "%s"' % title, 5000)

    def open_worksheet_with_title(self, title):
        """
        Open the worksheet with the given title, starting at
        worksheet list.  This assumes the list contains the title.
        """
        self.go_home()
        sel = self.selenium
        sel.click('link=%s' % title)
        sel.wait_for_page_to_load("30000")

    def publish_worksheet(self):
        """
        Publishes the current worksheet.  This assumes you're at the
        main worksheet page.  After it has finished publishing, it
        returns back to the worksheet.
        """
        sel = self.selenium
        sel.click("link=Publish")
        sel.wait_for_page_to_load("30000")
        sel.click("//button[text()='Yes']")
        sel.wait_for_page_to_load("30000")
        sel.click("link=Worksheet")
        sel.wait_for_page_to_load("30000")

    def republish_worksheet(self):
        """
        Re-publish the current worksheet.  Begins and ends at the main
        worksheet page.
        """
        sel = self.selenium
        sel.click("link=Publish")
        sel.wait_for_page_to_load("30000")
        sel.click("//button[text()='Re-publish worksheet']")
        sel.wait_for_page_to_load("30000")
        sel.click("link=Worksheet")
        sel.wait_for_page_to_load("30000")

    def goto_published_worksheets(self):
        """
        Go to the "Published Worksheets" page.
        """
        sel = self.selenium
        sel.open('/pub')
        sel.wait_for_page_to_load("30000")

    def goto_published_worksheet(self, id):
        """
        Goto the publishes worksheet with specified id.
        """
        id = str(id)
        sel = self.selenium
        sel.click("link=Published")
        sel.wait_for_page_to_load("30000")
        sel.click("name-pub-"+id)
        sel.wait_for_condition('selenium.browserbot.getCurrentWindow().worksheet_filename == "%s"'%('pub/'+id), 30000)

    def open_worksheet_with_name(self, name):
        """
        Opens the worksheet with the given name. Assumes that client
        is at list page.
        """
        sel = self.selenium
        self.wait_in_window(u'return this.$("a.worksheetname").attr("title").indexOf("{0}") != -1'.format(name),
                           30000)
        sel.click(u'//a[contains(@class, "worksheetname") and contains(@title, "{0}")]'.format(name))
        sel.wait_for_page_to_load(30000)

    def share_worksheet(self, collaborators):
        """
        Share the current worksheet with collaborators.
        """
        sel = self.selenium
        sel.click("link=Share")
        sel.wait_for_page_to_load("30000")
        sel.type("collaborators", collaborators)
        sel.click("//input[@value='Invite Collaborators']")
        sel.wait_for_page_to_load("30000")

    def wait_in_window(self, string, timeout):
        """
        Evaluates a javascript string until it returns true or timeout
        is reached. The string is evaluated in the scope of the
        browser window. Use ``this`` to access the browser window.
        """
        self.selenium.wait_for_condition('(function(){ %s }).apply(selenium.browserbot.getCurrentWindow())'
                                         % string, timeout)

    def stop_notebook(self):
        """
        Stops the Sage notebook.
        """
        self._p.sendline(chr(3)+chr(3))
        self._p.kill(signal.SIGKILL)
        self._p = None

    def tearDown(self):
        """
        Stops the notebook and cleans up.
        """
        self.stop_notebook()
        self.cleanup()
        self.selenium.stop()
