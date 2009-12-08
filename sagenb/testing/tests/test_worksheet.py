# -*- coding: utf-8 -*-
"""
Tests for SageNB Worksheets

AUTHORS:

- Mike Hansen (?) -- initial revision

- Tim Dumol (Oct. 28, 2009) -- made the tests work again. Separated this out. Added some more tests.
"""

import unittest, re

from sagenb.testing.notebook_test_case import NotebookTestCase

class TestWorksheet(NotebookTestCase):
    def setUp(self):
        NotebookTestCase.setUp(self)
        sel = self.selenium
        self.login_as('admin', 'asdfasdf')
        self.create_new_worksheet()

    def test_7433(self):
        """
        Tests that #7433 notebook: changing title of worksheet changes
        #title of corresponding published worksheet has been fixed.
        """
        sel = self.selenium
        self.rename_worksheet('To be published')
        self.publish_worksheet()
        self.save_and_quit()

        sel.click('link=Published')
        sel.wait_for_page_to_load(30000)
        self.open_worksheet_with_name('To be published')
        self.assert_(sel.is_element_present('//h1[contains(@class, "title") and contains(text(), "To be published")]'))

        sel.open('/home/admin')
        sel.wait_for_page_to_load(30000)
        self.open_worksheet_with_name('To be published')
        self.rename_worksheet('This has been published')
        self.save_and_quit()

        sel.click('link=Published')
        sel.wait_for_page_to_load(30000)
        self.open_worksheet_with_name('To be published')
        self.assert_(sel.is_element_present('//h1[contains(@class, "title") and contains(text(), "To be published")]'))

        sel.open('/home/admin')
        
        
    def test_edit(self):
        sel = self.selenium
        sel.click('//a[@href="edit"]')
        sel.wait_for_page_to_load("30000")

        sel.type('//textarea[@id="cell_intext"]',
                 '''
{{{id=1|
print(5 + 5)
///
15
}}}

{{{id=2|
print(13)
///
}}}
''')
        sel.click('id=button_save')
        sel.wait_for_page_to_load(30000)

        self.assert_(sel.is_element_present('//textarea[@id="cell_input_1" and contains(text(),"print(5 + 5)")]'))
        self.assert_(sel.is_element_present('//textarea[@id="cell_input_2" and contains(text(),"print(13)")]'))

        self.assertEqual(self.get_cell_output(1), u'15')
        
    def test_7341(self):
        sel = self.selenium
        sel.type('cell_input_1', 'fo')
        sel.get_eval('window.evaluate_cell_introspection(1, null, null);')
#       self.tab('cell_input_1')

        sel.wait_for_condition('selenium.browserbot.getCurrentWindow().$("div.introspection ul").length > 0', 10000)

        self.assert_(sel.is_element_present('//a[text()="forall"]'))
        self.assert_(sel.is_element_present('//a[text()="forget"]'))
        self.assert_(sel.is_element_present('//a[text()="format"]'))
        self.assert_(sel.is_element_present('//a[text()="four_squares"]'))
        self.assert_(sel.is_element_present('//a[text()="fortran"]'))
        
    def test_3957(self):
        """
        Check to make sure that Trac #3957 works.
        """
        sel = self.selenium
        out = self.eval_cell(1, "plot(x^2, x)")
        # TODO: This is a bug. Note that the url ends with %22, which is the url escape for a double quotation mark (")
        self.assertEqual(out, u'<font color="black"><img src="/home/admin/0/cells/1/sage0.png?1%22"></font>')
        
        self.save_and_quit()

        sel.click("id=name-admin-0")
        sel.wait_for_page_to_load("30000")

        self.assertEqual(self.get_cell_output(1), u'<font color="black"><img src="/home/admin/0/cells/1/sage0.png?1%22"></font>')

    def test_3711(self):
        """
        Check to make sure that Trac #3711 works.
        """
        sel = self.selenium
        
        self.rename_worksheet("Test Worksheet")
        self.save_and_quit()


        #Delete the worksheet
        sel.click("//input[@id='admin-0' and @type='checkbox']")
        sel.click("//button[@onclick='delete_button();']")
        sel.wait_for_page_to_load("30000")
        sel.click("link=Trash")
        sel.wait_for_page_to_load("30000")

        self.assert_(sel.is_text_present('Test Worksheet'), 'worksheet was not moved to trash')

        sel.click("link=Sign out")
        sel.wait_for_page_to_load("30000")

        #Stop the notebook and start it back up again
        self.stop_notebook()
        self.start_notebook()

        #Log in as the admin user
        sel.open('/')
        self.login_as('admin', 'asdfasdf')

        #Check to make sure the test worksheet is still in the trash
        sel.click("link=Trash")
        sel.wait_for_page_to_load("30000")

        self.assert_(sel.is_text_present('Test Worksheet'), 'worksheet was not in trash')


        #Empty the trash
        sel.click("link=(Empty Trash)")
        self.failUnless(re.search(r"^Emptying the trash will permanently delete all items in the trash\. Continue[\s\S]$", sel.get_confirmation()))

        #Leave and make sure that the file was actually deleted
        sel.click("link=Active")
        sel.wait_for_page_to_load("30000")
        sel.click("link=Trash")
        sel.wait_for_page_to_load("30000")
        self.assert_(not sel.is_text_present('Test Worksheet'), 'trash was not emptied')

        #Create a new worksheet.
        self.create_new_worksheet()
        self.rename_worksheet("Archive Worksheet")
        self.save_and_quit()

        sel.click("//input[@id='admin-1']")
        sel.click("//button[@onclick='archive_button();']")
        sel.wait_for_page_to_load("30000")
        sel.click("link=Archived")
        sel.wait_for_page_to_load("30000")

        self.assert_(sel.is_text_present('Archive Worksheet'), 'worksheet was not archived')
        
        #Stop the notebook and start it back up again
        self.stop_notebook()
        self.start_notebook()

        #Log in as the admin user
        sel.open('/')
        self.login_as('admin', 'asdfasdf')

        self.assert_(not sel.is_text_present('Archive Worksheet'), 'worksheet was in the active list')

        #Check to make sure the test worksheet is still in the archive
        sel.click("link=Archived")
        sel.wait_for_page_to_load("30000")

        self.assert_(sel.is_text_present('Archive Worksheet'), 'worksheet was not in the archive')



    def test_simple_evaluation(self):
        """
        Check to see that we can perform some simple computations and get the
        correct answers.
        """
        out = self.eval_cell(1, "2+2")
        self.assertEqual(out, '4')

    def test_operations1(self):
        sel = self.selenium
        out = self.eval_cell(1, "%hide\n%html\n<h1>For testing purposes")
        self.assertEqual(out, """<font color="black"></font><h1><font color="black">For testing purposes</font></h1>""")

        out = self.eval_cell(2, "var('a b c d')")
        self.assertEqual(out, '(a, b, c, d)')

        out = self.eval_cell(3, "expr1 = a+b - c + 2*d\nexpr2 = d*c-a*b")
        self.assertEqual(out, '')

        out = self.eval_cell(4, "expr1")
        self.assertEqual(out, u'a + b - c + 2*d')

        out = self.eval_cell(5, "expr2")
        self.assertEqual(out, u'-a*b + c*d')

        sel.select("//table[@id='topbar']/tbody/tr[2]/td[1]/select[2]", "label=Action...")
        sel.select("//table[@id='topbar']/tbody/tr[2]/td[1]/select[2]", "label=Action...")
        sel.click("//option[@value='evaluate_all();']")


    def tearDown(self):
        sel = self.selenium
        sel.click("link=Sign out")
        sel.wait_for_page_to_load("30000")
        NotebookTestCase.tearDown(self)

suite = unittest.TestLoader().loadTestsFromTestCase(TestWorksheet)

if __name__ == '__main__':
    unittest.main()
