# -*- coding: utf-8 -*-
"""
Tests to be run on the worksheet list.

AUTHORS:

- Tim Dumol (Oct. 28, 2009) -- inital version.
"""

import unittest

from sagenb.testing.notebook_test_case import NotebookTestCase

class TestWorksheetList(NotebookTestCase):
    def setUp(self):
        super(TestWorksheetList,self).setUp()
        sel = self.selenium
        self.login_as('admin', 'asdfasdf')
    
    def test_opening_worksheet(self):
        """
        Makes sure that opening a worksheet works.
        """
        sel = self.selenium
        self.create_new_worksheet('New worksheet')
        self.save_and_quit()
        sel.click("//a[@class='worksheetname']")
        sel.wait_for_page_to_load("30000")


    def test_creating_worksheet(self):
        """
        Tests worksheet creation.
        """
        sel = self.selenium
        self.create_new_worksheet('Creating a Worksheet')
        
        # Verify that the page has all the requisite elements.
        elements = ('link=Home', 'link=Help', 'link=Worksheet', 'link=Sign out',
                    'link=Toggle', 'link=Settings', 'link=Report a Problem',
                    'link=Log', 'link=Published', '//a[@id="worksheet_title"]',
                    '//button[@name="button_save"]')
        for element in elements:
            self.assert_(sel.is_element_present(element))
        

    def _search(self, phrase):
        """
        Searches for a phrase.
        """
        sel = self.selenium
        self.wait_in_window('return this.$("#search_worksheets").length > 0;', 30000)
        sel.type('id=search_worksheets', phrase)
        sel.click('//button[text()="Search Worksheets"]') # TODO: Fix for l18n
        sel.wait_for_page_to_load("30000")
            
    def test_searching_for_worksheets(self):
        """
        Tests search function.
        """
        sel = self.selenium

        worksheet_names = [
            'Did you just say wondeeerful?',
            'My wonderful search phrase',
            'Not a search target'
            ]

        for name in worksheet_names:
            self.create_new_worksheet(name)
            self.publish_worksheet()
            self.save_and_quit()

        pages = ('/home/admin/', '/pub')

        for page in pages:
            sel.open(page)
            self._search('wonderful')
            self.assert_(sel.is_element_present('//a[@class="worksheetname" and contains(text(), "My wonderful search phrase")]'),
                         'Search phrase not found on %s' % page)
            self.failIf(sel.is_element_present('//a[@class="worksheetname" and contains(text(), "Not a search target")]'),
                        'Non-matching search results found on %s' % page)

    def test_7428(self):
        """
        #7428: Newly/Re-published worksheets should be at the top of the
        "Published Worksheets" list and their "Last Edited" fields
        should contain the username, not 'pub' (assuming it's not
        shared).
        """
        sel = self.selenium
        ws_titles = ['apple', 'orange']

        def check_pub(title, prefix='Newly'):
            self.goto_published_worksheets()
            self.assertEqual(sel.get_text('css=td.worksheet_link'), title,
                             '%s-published worksheet %s not listed first' % (prefix, title))
            lastedit = sel.get_text('css=span.lastedit')
            self.assert_(self.username in lastedit,
                         '%s-published worksheet has wrong last edited field %s' % (prefix, lastedit))

        for w in ws_titles:
            self.create_new_worksheet(w)
            self.publish_worksheet()
            self.save_and_quit()
            check_pub(w)

        self.open_worksheet_with_title(ws_titles[0])
        self.republish_worksheet()
        self.save_and_quit()
        check_pub(ws_titles[0], prefix='Re')

    def test_7444(self):
        """
        #7444: Searching published worksheets after publishing a
        worksheet for the first time should not raise an error.
        """
        sel = self.selenium
        self.create_new_worksheet('banana')
        self.publish_worksheet()
        self.save_and_quit()
        self.goto_published_worksheets()
        self._search('anything')
        self.failIf(sel.is_text_present('Internal Server Error'), 
                    'Published worksheet search caused a server error')
 

suite = unittest.TestLoader().loadTestsFromTestCase(TestWorksheetList)

if __name__ == '__main__':
    unittest.main()
