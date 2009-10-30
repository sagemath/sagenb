# -*- coding: utf-8 -*-
"""
Tests for SageNB Accounts

AUTHORS:

- Mike Hansen (?) -- initial revision

- Tim Dumol (Oct. 28, 2009) -- made the tests work again. Separated this out.
"""
import unittest

from sagenb.testing.notebook_test_case import NotebookTestCase

class TestAccounts(NotebookTestCase):
    def _sage_startup_command(self):
        return 'sage -c "notebook(open_viewer=False, directory=\'%s\', accounts=True)"'\
            % self.temp_dir

    def test_3960(self):
        """
        Tests to make sure that Trac ticket #3960 is actually fixed.
        """
        sel = self.selenium
        
        self.register_user('mike')
        self.register_user('chris')

        self.login_as('mike')
        self.create_new_worksheet()
        out = self.eval_cell(1, '2+2')
        self.publish_worksheet()
        self.logout()

        self.login_as('chris')
        self.goto_published_worksheet(0)
        
        sel.click("link=Edit a copy.")
        # Simply waiting for the page to load fails with slow computers.
        self.wait_in_window('return this.location == "http://localhost:%d/home/chris/0/"'
                           % self.sagenb_port, 30000)
        sel.wait_for_page_to_load(30000)
        self.wait_in_window('return this.$.trim(this.$("#cell_output_nowrap_1").text()) == 4', 30000)

        self.assertEqual(sel.get_location(), 'http://localhost:%d/home/chris/0/' % self.sagenb_port)
        self.assertEqual(self.get_cell_output(1), '4')
        self.assert_(sel.is_text_present('by chris'), 'chris does not own the worksheet')

    def test_4088(self):
        """
        Check to see that the 'Welcome to Sage!' message is not visible on the
        published worksheets screen when there are no worksheets.
        """
        sel = self.selenium

        self.login_as('admin')
        sel.click("link=Published")
        sel.wait_for_page_to_load("30000")

        self.assert_(not sel.is_text_present('Welcome to Sage!'), 'welcome message is still present')


    def test_4050(self):
        """
        Tests to make sure that Trac ticket #4050 is actually fixed.
        """
        sel = self.selenium
        
        self.register_user('mike')
        self.register_user('chris')

        self.login_as('mike')
        self.create_new_worksheet()
        out = self.eval_cell(1, '2+2')
        self.rename_worksheet("Shared Worksheet")
        self.share_worksheet("chris")
        self.save_and_quit()
        self.logout()

        self.login_as('chris')
        sel.click("name-mike-0")
        sel.wait_for_page_to_load("30000")
        sel.select("//option[@value='copy_worksheet();']/parent::select", "value=copy_worksheet();")
        sel.wait_for_page_to_load("30000")
        self.save_and_quit()

        sel.click("name-chris-1")
        sel.wait_for_page_to_load("30000")


        self.assertEqual(sel.get_location(), 'http://localhost:%d/home/chris/1/' % self.sagenb_port)
        self.assertEqual(sel.get_title(), 'Copy of Shared Worksheet (Sage)')
        self.assert_(sel.is_text_present('by chris'), 'chris does not own the worksheet')
        self.assertEqual(self.get_cell_output(1), '4')
        
        self.save_and_quit()
        self.logout()

suite = unittest.TestLoader().loadTestsFromTestCase(TestAccounts)

if __name__ == '__main__':
    unittest.main()
