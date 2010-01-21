# -*- coding: utf-8 -*-
"""
A Cell.

A cell is a single input/output block. Worksheets are built out of
a list of cells.
"""

###########################################################################
#       Copyright (C) 2006 William Stein <wstein@gmail.com>
#
#  Distributed under the terms of the GNU General Public License (GPL)
#                  http://www.gnu.org/licenses/
###########################################################################

import os
import re
import shutil
from cgi import escape

from jsmath import math_parse
from sagenb.misc.misc import (word_wrap, SAGE_DOC, strip_string_literals,
                              set_restrictive_permissions, unicode_str,
                              encoded_str)

# Maximum number of characters allowed in output.  This is needed
# avoid overloading web browser.  For example, it should be possible
# to gracefully survive:
#    while True:
#       print "hello world"
# On the other hand, we don't want to loose the output of big matrices
# and numbers, so don't make this too small.
MAX_OUTPUT = 32000
MAX_OUTPUT_LINES = 120

# Used to detect and format tracebacks.  See :func:`format_exception`.
TRACEBACK = 'Traceback (most recent call last):'

# This regexp matches "cell://blah..." in a non-greedy way (the ?), so
# we don't get several of these combined in one.
re_cell = re.compile('"cell://.*?"')
re_cell_2 = re.compile("'cell://.*?'")   # same, but with single quotes
# Matches script blocks.
re_script = re.compile(r'<script[^>]*?>.*?</script>', re.DOTALL | re.I)

# Whether to enable editing of :class:`TextCell`s with TinyMCE.
JEDITABLE_TINYMCE = True


###########################
# Generic (abstract) cell #
###########################
class Cell_generic:
    def is_interactive_cell(self):
        """
        Returns whether this cell uses
        :func:`sagenb.notebook.interact.interact` as a function call
        or decorator.

        OUTPUT:

        - a boolean

        EXAMPLES::

            sage: from sagenb.notebook.cell import Cell_generic
            sage: C = sagenb.notebook.cell.TextCell(0, '2+3', None)
            sage: Cell_generic.is_interactive_cell(C)
            False
        """
        return False

    def delete_output(self):
        """
        Delete all output in this cell. This is not executed - it is an
        abstract function that must be overwritten in a derived class.

        EXAMPLES:

        This function just raises a NotImplementedError, since it must
        be defined in a derived class.

        ::

            sage: C = sagenb.notebook.cell.Cell_generic()
            sage: C.delete_output()
            Traceback (most recent call last):
            ...
            NotImplementedError
        """
        raise NotImplementedError


#############
# Text cell #
#############
class TextCell(Cell_generic):
    def __init__(self, id, text, worksheet):
        """
        Creates a new text cell.

        INPUT:

        - ``id`` - an integer or string; this cell's ID

        - ``text`` - a string; this cell's contents

        - ``worksheet`` - a
          :class:`sagenb.notebook.worksheet.Worksheet` instance; this
          cells parent worksheet

        EXAMPLES::

            sage: C = sagenb.notebook.cell.TextCell(0, '2+3', None)
            sage: C == loads(dumps(C))
            True
        """
        text = unicode_str(text)
        try:
            self.__id = int(id)
        except ValueError:
            self.__id = id

        self.__text = text
        self.__worksheet = worksheet

    def __repr__(self):
        """
        Returns a string representation of this text cell.

        OUTPUT:

        - a string

        EXAMPLES::

            sage: C = sagenb.notebook.cell.TextCell(0, '2+3', None)
            sage: C.__repr__()
            'TextCell 0: 2+3'
        """
        return "TextCell %s: %s"%(self.__id, encoded_str(self.__text))

    def delete_output(self):
        """
        Delete all output in this text cell.  This does nothing since
        text cells have no output.

        EXAMPLES::

            sage: C = sagenb.notebook.cell.TextCell(0, '2+3', None)
            sage: C
            TextCell 0: 2+3
            sage: C.delete_output()
            sage: C
            TextCell 0: 2+3
        """
        pass # nothing to do -- text cells have no output

    def set_input_text(self, input_text):
        """
        Sets the input text of this text cell.

        INPUT:

        - ``input_text`` - a string; the new input text for this cell

        EXAMPLES::

            sage: C = sagenb.notebook.cell.TextCell(0, '2+3', None)
            sage: C
            TextCell 0: 2+3
            sage: C.set_input_text("3+2")
            sage: C
            TextCell 0: 3+2
        """
        input_text = unicode_str(input_text)
        self.__text = input_text

    def set_worksheet(self, worksheet, id=None):
        """
        Updates this text cell's worksheet object and, optionally, its
        ID.

        INPUT:

        - ``worksheet`` - a
          :class:`sagenb.notebook.worksheet.Worksheet` instance; the
          cell's new parent worksheet object

        - ``id`` - an integer or string (default: None); the cell's
          new ID

        EXAMPLES::

            sage: C = sagenb.notebook.cell.TextCell(0, '2+3', None)
            sage: W = "worksheet object"
            sage: C.set_worksheet(W)
            sage: C.worksheet()
            'worksheet object'
            sage: C.set_worksheet(None, id=2)
            sage: C.id()
            2
        """
        self.__worksheet = worksheet
        if id is not None:
            self.__id = id

    def worksheet(self):
        """
        Returns this text cell's worksheet object

        OUTPUT:

        - a :class:`sagenb.notebook.worksheet.Worksheet` instance


        EXAMPLES::

            sage: C = sagenb.notebook.cell.TextCell(0, '2+3', 'worksheet object')
            sage: C.worksheet()
            'worksheet object'
        """
        return self.__worksheet

    def html(self, wrap=None, div_wrap=True, do_print=False,
             do_math_parse=True, editing=False):
        """
        Returns HTML code for this text cell, including its contents
        and associated script elements.

        INPUT:

        - ``wrap`` -- an integer (default: None); number of columns to
          wrap at (not used)

        - ``div_wrap`` -- a boolean (default: True); whether to wrap
          in a div (not used)

        - ``do_print`` - a boolean (default: False); whether to render the
          cell for printing

        - ``do_math_parse`` - a boolean (default: True); whether to
          process the contents for JSMath (see
          :func:`sagenb.notebook.jsmath.math_parse`)

        - ``editing`` - a boolean (default: False); whether to open an
          editor for this cell

        OUTPUT:

        - a string

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(tmp_dir()+'.sagenb')
            sage: nb.add_user('sage','sage','sage@sagemath.org',force=True)
            sage: W = nb.create_new_worksheet('Test', 'sage')
            sage: C = sagenb.notebook.cell.TextCell(0, '2+3', W)
            sage: C.html()
            u'...text_cell...2+3...'
            sage: C.set_input_text("$2+3$")
            sage: C.html(do_math_parse=True)
            u'...text_cell...class="math"...2+3...'
        """
        from template import template
        return template(os.path.join('html', 'notebook', 'text_cell.html'),
                        cell = self, wrap = wrap, do_print = do_print,
                        do_math_parse = do_math_parse, editing = editing,
                        div_wrap=div_wrap)

    def plain_text(self, prompts=False):
        u"""
        Returns a plain text version of this ext cell.

        INPUT:

        - ``prompts`` - a boolean (default: False); whether to strip
          interpreter prompts from the beginning of each line

        OUTPUT:

        - a string

        EXAMPLES::

            sage: C = sagenb.notebook.cell.TextCell(0, '2+3', None)
            sage: C.plain_text()
            u'2+3'
            sage: C = sagenb.notebook.cell.TextCell(0, u'ΫäĻƾṀБ', None)
            sage: C.plain_text()
            u'\xce\xab\xc3\xa4\xc4\xbb\xc6\xbe\xe1\xb9\x80\xd0\x91'
        """
        return self.__text

    def edit_text(self):
        """
        Returns the text to be displayed for this text cell in the
        Edit window.

        OUTPUT:

        - a string

        EXAMPLES::

            sage: C = sagenb.notebook.cell.TextCell(0, '2+3', None)
            sage: C.edit_text()
            u'2+3'
        """
        return self.__text

    def id(self):
        """
        Returns this text cell's ID.

        OUTPUT:

        - an integer or string

        EXAMPLES::

            sage: C = sagenb.notebook.cell.TextCell(0, '2+3', None)
            sage: C.id()
            0
        """
        return self.__id

    def is_auto_cell(self):
        """
        Returns whether this is an automatically evaluated text cell.
        This is always false for :class:`TextCell`\ s.

        OUTPUT:

        - a boolean

        EXAMPLES::

            sage: C = sagenb.notebook.cell.TextCell(0, '2+3', None)
            sage: C.is_auto_cell()
            False
        """
        return False

    def __cmp__(self, right):
        """
        Compares text cells by ID.

        INPUT:

        - ``right`` - a :class:`TextCell` instance; the cell to
          compare to this cell

        OUTPUT:

        - a boolean

        EXAMPLES::

            sage: C1 = sagenb.notebook.cell.TextCell(0, '2+3', None)
            sage: C2 = sagenb.notebook.cell.TextCell(0, '3+2', None)
            sage: C3 = sagenb.notebook.cell.TextCell(1, '2+3', None)
            sage: C1 == C1
            True
            sage: C1 == C2
            True
            sage: C1 == C3
            False
        """
        return cmp(self.id(), right.id())

    def set_cell_output_type(self, typ='wrap'):
        """
        Sets this text cell's output type.  This does nothing for
        :class:`TextCell`\ s.

        INPUT:

        - ``typ`` - a string (default: 'wrap'); the target output type

        EXAMPLES::

            sage: C = sagenb.notebook.cell.TextCell(0, '2+3', None)
            sage: C.set_cell_output_type("wrap")
        """
        pass # ignored


################
# Compute cell #
###############
class Cell(Cell_generic):
    def __init__(self, id, input, out, worksheet):
        """
        Creates a new compute cell.

        INPUT:

        - ``id`` - an integer or string; the new cell's ID

        - ``input`` - a string; this cell's input

        - ``out`` - a string; this cell's output

        - ``worksheet`` - a
          :class:`sagenb.notebook.worksheet.Worksheet` instance; this
          cell's worksheet object

        EXAMPLES::

            sage: C = sagenb.notebook.cell.Cell(0, '2+3', '5', None)
            sage: C == loads(dumps(C))
            True
        """
        out = unicode_str(out)
        input = unicode_str(input)
        try:
            self.__id = int(id)
        except ValueError:
            self.__id = id

        self.__out   = out.replace('\r','')
        self.__worksheet = worksheet
        self.__interrupted = False
        self.__completions = False
        self.has_new_output = False
        self.__no_output_cell = False
        self.__asap = False
        self.__version = -1
        self.set_input_text(input.replace('\r',''))

    def set_asap(self, asap):
        """
        Sets whether to evaluate this compute cell as soon as possible
        (ASAP).

        INPUT:

        - ``asap`` - a boolean convertible

        EXAMPLES::

            sage: C = sagenb.notebook.cell.Cell(0, '2+3', '5', None)
            sage: C.is_asap()
            False
            sage: C.set_asap(True)
            sage: C.is_asap()
            True
        """
        self.__asap = bool(asap)

    def is_asap(self):
        """
        Returns whether this compute cell is to be evaluated as soon
        as possible (ASAP).

        OUTPUT:

        - a boolean

        EXAMPLES::

            sage: C = sagenb.notebook.cell.Cell(0, '2+3', '5', None)
            sage: C.is_asap()
            False
            sage: C.set_asap(True)
            sage: C.is_asap()
            True
        """
        try:
            return self.__asap
        except AttributeError:
            self.__asap = False
            return self.__asap

    def delete_output(self):
        """
        Deletes all output in this compute cell.

        EXAMPLES::

            sage: C = sagenb.notebook.cell.Cell(0, '2+3', '5', None); C
            Cell 0; in=2+3, out=5
            sage: C.delete_output()
            sage: C
            Cell 0; in=2+3, out=
        """
        self.__out = u''
        self.__out_html = u''
        self.__evaluated = False

    def evaluated(self):
        r"""
        Returns whether this compute cell has been successfully
        evaluated in a currently running session.  This is not about
        whether the output of the cell is valid given the input.

        OUTPUT:

        - a boolean

        EXAMPLES: We create a worksheet with a cell that has wrong output::

            sage: nb = sagenb.notebook.notebook.load_notebook(tmp_dir()+'.sagenb')
            sage: nb.add_user('sage','sage','sage@sagemath.org',force=True)
            sage: W = nb.create_new_worksheet('Test', 'sage')
            sage: W.edit_save('{{{\n2+3\n///\n20\n}}}')
            sage: C = W.cell_list()[0]
            sage: C
            Cell 0; in=2+3, out=
            20

        We re-evaluate that input cell::

            sage: C.evaluate()
            sage: W.check_comp(wait=9999)     # random output -- depends on computer speed
            ('w', Cell 0; in=2+3, out=)

        Now the output is right::

            sage: C     # random output -- depends on computer speed
            Cell 0; in=2+3, out=

        And the cell is considered to have been evaluated.

        ::

            sage: C.evaluated()     # random output -- depends on computer speed
            True

        ::

            sage: W.quit()
            sage: nb.delete()
        """
        # Cells are never considered evaluated in a new session.
        if not self.worksheet().compute_process_has_been_started():
            self.__evaluated = False
            return False

        # Figure out if the worksheet is using the same sage
        # session as this cell.  (I'm not sure when this would
        # be False.)
        same_session = self.worksheet().sage() is self.sage()
        try:
            # Always not evaluated if sessions are different.
            if not same_session:
                self.__evaluated = False
                return False
            return self.__evaluated
        except AttributeError:
            # Default assumption is that cell has not been evaluated.
            self.__evaluated = False
            return False

    def set_no_output(self, no_output):
        """
        Sets whether this is a "no output" compute cell, i.e., we
        don't care about its output.

        INPUT:

        - ``no_output`` - a boolean convertible

        EXAMPLES::

            sage: C = sagenb.notebook.cell.Cell(0, '2+3', '5', None)
            sage: C.is_no_output()
            False
            sage: C.set_no_output(True)
            sage: C.is_no_output()
            True
        """
        self.__no_output = bool(no_output)

    def is_no_output(self):
        """
        Returns whether this is a "no output" compute cell, i.e., we
        don't care about its output.

        OUTPUT:

        - a boolean

        EXAMPLES::

            sage: C = sagenb.notebook.cell.Cell(0, '2+3', '5', None)
            sage: C.is_no_output()
            False
            sage: C.set_no_output(True)
            sage: C.is_no_output()
            True
        """
        try:
            return self.__no_output
        except AttributeError:
            self.__no_output = False
            return self.__no_output

    def set_cell_output_type(self, typ='wrap'):
        """
        Sets this compute cell's output type.

        INPUT:

        - ``typ`` - a string (default: 'wrap'); the target output type

        EXAMPLES::

            sage: C = sagenb.notebook.cell.Cell(0, '2+3', '5', None)
            sage: C.cell_output_type()
            'wrap'
            sage: C.set_cell_output_type('nowrap')
            sage: C.cell_output_type()
            'nowrap'
        """
        self.__type = typ

    def cell_output_type(self):
        """
        Returns this compute cell's output type.

        OUTPUT:

        - a string

        EXAMPLES::

            sage: C = sagenb.notebook.cell.Cell(0, '2+3', '5', None)
            sage: C.cell_output_type()
            'wrap'
            sage: C.set_cell_output_type('nowrap')
            sage: C.cell_output_type()
            'nowrap'
        """
        try:
            return self.__type
        except AttributeError:
            self.__type = 'wrap'
            return self.__type

    def set_worksheet(self, worksheet, id=None):
        """
        Sets this compute cell's worksheet object and, optionally, its
        ID.

        INPUT:

        - ``worksheet`` - a
          :class:`sagenb.notebook.worksheet.Worksheet` instance; the
          cell's new worksheet object

        - ``id`` - an integer or string (default: None); the cell's
          new ID

        EXAMPLES::

            sage: C = sagenb.notebook.cell.Cell(0, '2+3', '5', None)
            sage: W = "worksheet object"
            sage: C.set_worksheet(W)
            sage: C.worksheet()
            'worksheet object'
            sage: C.set_worksheet(None, id=2)
            sage: C.id()
            2
        """
        self.__worksheet = worksheet
        if id is not None:
            self.set_id(id)

    def worksheet(self):
        """
        Returns this compute cell's worksheet object.

        OUTPUT:

        - a :class:`sagenb.notebook.worksheet.Worksheet` instance

        EXAMPLES::

            sage: C = sagenb.notebook.cell.Cell(0, '2+3', '5', 'worksheet object')
            sage: C.worksheet()
            'worksheet object'
        """
        return self.__worksheet

    def update_html_output(self, output=''):
        """
        Updates this compute cell's the file list with HTML-style
        links or embeddings.

        For interactive cells, the HTML output section is always
        empty, mainly because there is no good way to distinguish
        content (e.g., images in the current directory) that goes into
        the interactive template and content that would go here.

        INPUT:

        - ``output`` - a string (default: ''); the new output

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(tmp_dir()+'.sagenb')
            sage: nb.add_user('sage','sage','sage@sagemath.org',force=True)
            sage: W = nb.create_new_worksheet('Test', 'sage')
            sage: C = sagenb.notebook.cell.Cell(0, 'plot(sin(x),0,5)', '', W)
            sage: C.evaluate()
            sage: W.check_comp(wait=9999)     # random output -- depends on computer speed
            ('d', Cell 0; in=plot(sin(x),0,5), out=
            <html><font color='black'><img src='cell://sage0.png'></font></html>
            <BLANKLINE>
            )
            sage: C.update_html_output()
            sage: C.output_html()     # random output -- depends on computer speed
            '<img src="/home/sage/0/cells/0/sage0.png?...">'
            sage: W.quit()
            sage: nb.delete()
        """
        if self.is_interactive_cell():
            self.__out_html = u""
        else:
            self.__out_html = self.files_html(output)

    def id(self):
        """
        Returns this compute cell's ID.

        OUTPUT:

        - an integer or string

        EXAMPLES::

            sage: C = sagenb.notebook.cell.Cell(0, '2+3', '5', None)
            sage: C.id()
            0
        """
        return self.__id

    def set_id(self, id):
        """
        Sets this compute cell's ID.

        INPUT:

        - ``id`` - an integer or string; the new ID

        EXAMPLES::

            sage: C = sagenb.notebook.cell.Cell(0, '2+3', '5', None)
            sage: C.set_id(2)
            sage: C.id()
            2
        """
        self.__id = id

    def worksheet(self):
        """
        Returns this compute cell's worksheet object.

        OUTPUT:

        - a :class:`sagenb.notebook.worksheet.Worksheet` instance

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(tmp_dir()+'.sagenb')
            sage: nb.add_user('sage','sage','sage@sagemath.org',force=True)
            sage: W = nb.create_new_worksheet('Test', 'sage')
            sage: C = sagenb.notebook.cell.Cell(0, '2+3', '5', W)
            sage: C.worksheet() is W
            True
            sage: nb.delete()
        """
        return self.__worksheet

    def worksheet_filename(self):
        """
        Returns the filename of this compute cell's worksheet object.

        OUTPUT:

        - a string

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(tmp_dir()+'.sagenb')
            sage: nb.add_user('sage','sage','sage@sagemath.org',force=True)
            sage: W = nb.create_new_worksheet('Test', 'sage')
            sage: C = sagenb.notebook.cell.Cell(0, '2+3', '5', W)
            sage: C.worksheet_filename()
            'sage/0'
            sage: nb.delete()
        """
        return self.__worksheet.filename()

    def notebook(self):
        """
        Returns this compute cell's associated notebook object.

        OUTPUT:

        - a :class:`sagenb.notebook.notebook.Notebook` instance

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.load_notebook(tmp_dir()+'.sagenb')
            sage: nb.add_user('sage','sage','sage@sagemath.org',force=True)
            sage: W = nb.create_new_worksheet('Test', 'sage')
            sage: C = sagenb.notebook.cell.Cell(0, '2+3', '5', W)
            sage: C.notebook() is nb
            True
            sage: nb.delete()
        """
        return self.__worksheet.notebook()

    def directory(self):
        """
        Returns the name of this compute cell's directory, creating
        it, if it doesn't already exist.

        OUTPUT:

        - a string

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(tmp_dir()+'.sagenb')
            sage: nb.add_user('sage','sage','sage@sagemath.org',force=True)
            sage: W = nb.create_new_worksheet('Test', 'sage')
            sage: C = sagenb.notebook.cell.Cell(0, '2+3', '5', W)
            sage: C.directory()
            '.../home/sage/0/cells/0'
            sage: nb.delete()
        """
        dir = self._directory_name()
        if not os.path.exists(dir):
            os.makedirs(dir)
        set_restrictive_permissions(dir)
        return dir

    def _directory_name(self):
        """
        Returns the name of this compute cell's directory.

        OUTPUT:

        - a string

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(tmp_dir()+'.sagenb')
            sage: nb.add_user('sage','sage','sage@sagemath.org',force=True)
            sage: W = nb.create_new_worksheet('Test', 'sage')
            sage: C = sagenb.notebook.cell.Cell(0, '2+3', '5', W)
            sage: C._directory_name()
            '.../home/sage/0/cells/0'
            sage: nb.delete()
        """
        return os.path.join(self.__worksheet.directory(), 'cells', str(self.id()))

    def __cmp__(self, right):
        """
        Compares compute cells by ID.

        INPUT:

        - ``right`` - a :class:`Cell` instance; the cell to compare
          this this cell

        OUTPUT:

        - a boolean

        EXAMPLES::

            sage: C1 = sagenb.notebook.cell.Cell(0, '2+3', '5', None)
            sage: C2 = sagenb.notebook.cell.Cell(0, '3+2', '5', None)
            sage: C3 = sagenb.notebook.cell.Cell(1, '2+3', '5', None)
            sage: C1 == C1
            True
            sage: C1 == C2
            True
            sage: C1 == C3
            False
        """
        return cmp(self.id(), right.id())

    def __repr__(self):
        """
        Returns a string representation of this compute cell.

        OUTPUT:

        - a string

        EXAMPLES::

            sage: C = sagenb.notebook.cell.Cell(0, '2+3', '5', None); C
            Cell 0; in=2+3, out=5
        """
        return 'Cell %s; in=%s, out=%s'%(self.__id, encoded_str(self.__in), encoded_str(self.__out))

    def word_wrap_cols(self):
        """
        Returns the number of columns for word wrapping this compute
        cell.  This defaults to 70, but the default setting for a
        notebook is 72.

        OUTPUT:

        - an integer

        EXAMPLES::

            sage: C = sagenb.notebook.cell.Cell(0, '2+3', '5', None)
            sage: C.word_wrap_cols()
            70
            sage: nb = sagenb.notebook.notebook.Notebook(tmp_dir()+'.sagenb')
            sage: nb.add_user('sage','sage','sage@sagemath.org',force=True)
            sage: W = nb.create_new_worksheet('Test', 'sage')
            sage: C = sagenb.notebook.cell.Cell(0, '2+3', '5', W)
            sage: C.word_wrap_cols()
            72
            sage: nb.delete()
        """
        try:
            return self.notebook().conf()['word_wrap_cols']
        except AttributeError:
            return 70

    def plain_text(self, ncols=0, prompts=True, max_out=None):
        r"""
        Returns the plain text version of this compute cell.

        INPUT:

        - ``ncols`` - an integer (default: 0); the number of word wrap
          columns

        - ``prompts`` - a boolean (default: False); whether to strip
          interpreter prompts from the beginning of each line

        - ``max_out`` - an integer (default: None); the maximum number
          of characters to return

        OUTPUT:

        - a string

        EXAMPLES::

            sage: C = sagenb.notebook.cell.Cell(0, '2+3', '5', None)
            sage: len(C.plain_text())
            11
        """
        if ncols == 0:
            ncols = self.word_wrap_cols()
        s = u''

        self.__in = unicode_str(self.__in)

        input_lines = self.__in

        pr = 'sage: '

        if prompts:
            input_lines = input_lines.splitlines()
            has_prompt = False
            if pr == 'sage: ':
                for v in input_lines:
                    w = v.lstrip()
                    if w[:5] == 'sage:' or w[:3] == '>>>' or w[:3] == '...':
                        has_prompt = True
                        break
            else:
                # discard first line since it sets the prompt
                input_lines = input_lines[1:]

            if has_prompt:
                s += '\n'.join(input_lines) + '\n'
            else:
                in_loop = False
                for v in input_lines:
                    if len(v) == 0:
                        pass
                    elif len(v.lstrip()) != len(v):  # starts with white space
                        in_loop = True
                        s += '...   ' + v + '\n'
                    elif v[:5] == 'else:':
                        in_loop = True
                        s += '...   ' + v + '\n'
                    else:
                        if in_loop:
                            s += '...\n'
                            in_loop = False
                        s += pr + v + '\n'
        else:
            s += self.__in

        if prompts:
            msg = TRACEBACK
            if self.__out.strip().startswith(msg):
                v = self.__out.strip().splitlines()
                w = [msg, '...']
                for i in range(1,len(v)):
                    if not (len(v[i]) > 0 and v[i][0] == ' '):
                        w = w + v[i:]
                        break
                out = '\n'.join(w)
            else:
                out = self.output_text(ncols, raw=True, html=False)
        else:
            out = self.output_text(ncols, raw=True, html=False, allow_interact=False)
            out = '///\n' + out.strip('\n')

        if not max_out is None and len(out) > max_out:
            out = out[:max_out] + '...'

        # Get rid of spurious carriage returns
        s = s.strip('\n')
        out = out.strip('\n').strip('\r').strip('\r\n')
        s = s + '\n' + out

        if not prompts:
            s = s.rstrip('\n')
        return s

    def edit_text(self, ncols=0, prompts=False, max_out=None):
        r"""
        Returns the text displayed for this compute cell in the Edit
        window.

        INPUT:

        - ``ncols`` - an integer (default: 0); the number of word wrap
          columns

        - ``prompts`` - a boolean (default: False); whether to strip
          interpreter prompts from the beginning of each line

        - ``max_out`` - an integer (default: None); the maximum number
          of characters to return

        OUTPUT:

        - a string

        EXAMPLES::

            sage: C = sagenb.notebook.cell.Cell(0, '2+3', '5', None)
            sage: C.edit_text()
            u'{{{id=0|\n2+3\n///\n5\n}}}'
            sage: C = sagenb.notebook.cell.Cell(0, u'ΫäĻƾṀБ', u'ΫäĻƾṀБ', None)
            sage: C.edit_text()
            u'{{{id=0|\n\xce\xab\xc3\xa4\xc4\xbb\xc6...\xb9\x80\xd0\x91\n}}}'
        """
        s = self.plain_text(ncols, prompts, max_out)
        return u'{{{id=%s|\n%s\n}}}'%(self.id(), s)

    def is_last(self):
        """
        Returns whether this compute cell is the last cell in its
        worksheet object.

        OUTPUT:

        - a boolean

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(tmp_dir()+'.sagenb')
            sage: nb.add_user('sage','sage','sage@sagemath.org',force=True)
            sage: W = nb.create_new_worksheet('Test', 'sage')
            sage: C = W.new_cell_after(0, "2^2"); C
            Cell 2; in=2^2, out=
            sage: C.is_last()
            True
            sage: C = W.get_cell_with_id(0)
            sage: C.is_last()
            False
            sage: nb.delete()
        """
        return self.__worksheet.cell_list()[-1] == self

    def next_id(self):
        """
        Returns the ID of the next cell in this compute cell's
        worksheet object.  If this cell is not in the worksheet or is
        the last cell, it returns the ID of the worksheet's first
        cell.

        OUTPUT:

        - an integer or string

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(tmp_dir()+'.sagenb')
            sage: nb.add_user('sage','sage','sage@sagemath.org',force=True)
            sage: W = nb.create_new_worksheet('Test', 'sage')
            sage: C = W.new_cell_after(1, "2^2")
            sage: C = W.get_cell_with_id(1)
            sage: C.next_id()
            2
            sage: C = W.get_cell_with_id(2)
            sage: C.next_id()
            1
            sage: nb.delete()
        """
        L = self.__worksheet.cell_list()
        try:
            k = L.index(self)
        except ValueError:
            print "Warning -- cell %s no longer exists"%self.id()
            return L[0].id()
        try:
            return L[k+1].id()
        except IndexError:
            return L[0].id()

    def interrupt(self):
        """
        Sets this compute cell's evaluation as interrupted.

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(tmp_dir()+'.sagenb')
            sage: nb.add_user('sage','sage','sage@sagemath.org',force=True)
            sage: W = nb.create_new_worksheet('Test', 'sage')
            sage: C = W.new_cell_after(0, "2^2")
            sage: C.interrupt()
            sage: C.interrupted()
            True
            sage: C.evaluated()
            False
            sage: nb.delete()
        """
        self.__interrupted = True
        self.__evaluated = False

    def interrupted(self):
        """
        Returns whether this compute cell's evaluation has been
        interrupted.

        OUTPUT:

        - a boolean

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(tmp_dir()+'.sagenb')
            sage: nb.add_user('sage','sage','sage@sagemath.org',force=True)
            sage: W = nb.create_new_worksheet('Test', 'sage')
            sage: C = W.new_cell_after(0, "2^2")
            sage: C.interrupt()
            sage: C.interrupted()
            True
            sage: nb.delete()
        """
        return self.__interrupted

    def computing(self):
        """
        Returns whether this compute cell is queued for evaluation by
        its worksheet object.

        OUTPUT:

        - a boolean

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(tmp_dir()+'.sagenb')
            sage: nb.add_user('sage','sage','sage@sagemath.org',force=True)
            sage: W = nb.create_new_worksheet('Test', 'sage')
            sage: C = W.new_cell_after(0, "2^2")
            sage: C.computing()
            False
            sage: nb.delete()
        """
        return self in self.__worksheet.queue()

    def is_interactive_cell(self):
        r"""
        Returns whether this compute cell contains
        :func:`sagenb.notebook.interact.interact` either as a function
        call or decorator.

        OUTPUT:

        - a boolean

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(tmp_dir()+'.sagenb')
            sage: nb.add_user('sage','sage','sage@sagemath.org',force=True)
            sage: W = nb.create_new_worksheet('Test', 'sage')
            sage: C = W.new_cell_after(0, "@interact\ndef f(a=slider(0,10,1,5):\n    print a^2")
            sage: C.is_interactive_cell()
            True
            sage: C = W.new_cell_after(C.id(), "2+2")
            sage: C.is_interactive_cell()
            False
            sage: nb.delete()
        """
        # Do *not* cache
        s = strip_string_literals(self.input_text())
        if len(s) == 0: return False
        s = s[0]
        return bool(re.search('(?<!\w)interact\s*\(.*\).*', s) or re.search('\s*@\s*interact\s*\n', s))

    def is_interacting(self):
        r"""
        Returns whether this compute cell is currently
        :func:`sagenb.notebook.interact.interact`\ ing.

        OUTPUT:

        - a boolean

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(tmp_dir()+'.sagenb')
            sage: nb.add_user('sage','sage','sage@sagemath.org',force=True)
            sage: W = nb.create_new_worksheet('Test', 'sage')
            sage: C = W.new_cell_after(0, "@interact\ndef f(a=slider(0,10,1,5):\n    print a^2")
            sage: C.is_interacting()
            False
        """
        return hasattr(self, 'interact')

    def stop_interacting(self):
        """
        Stops :func:`sagenb.notebook.interact.interact`\ ion for this
        compute cell.

        TODO: Add doctests.
        """
        if self.is_interacting():
            del self.interact

    def set_input_text(self, input):
        """
        Sets the input text of this compute cell.

        INPUT:

        - ``input`` - a string; the new input text

        TODO: Add doctests for the code dealing with interact.

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(tmp_dir()+'.sagenb')
            sage: nb.add_user('sage','sage','sage@sagemath.org',force=True)
            sage: W = nb.create_new_worksheet('Test', 'sage')
            sage: C = W.new_cell_after(0, "2^2")
            sage: C.evaluate()
            sage: W.check_comp(wait=9999)     # random output -- depends on computer speed
            ('d', Cell 1; in=2^2, out=
            4
            )
            sage: C.version()
            0
            sage: C.set_input_text('3+3')
            sage: C.input_text()
            u'3+3'
            sage: C.evaluated()
            False
            sage: C.version()
            1
            sage: W.quit()
            sage: nb.delete()
        """
        # Stuff to deal with interact
        input = unicode_str(input)

        if input.startswith('%__sage_interact__'):
            self.interact = input[len('%__sage_interact__')+1:]
            self.__version = self.version() + 1
            return
        elif self.is_interacting():
            try:
                del self.interact
                del self._interact_output
            except AttributeError:
                pass

        # We have updated the input text so the cell can't have
        # been evaluated.
        self.__evaluated = False
        self.__version = self.version() + 1
        self.__in = input
        if hasattr(self, '_html_cache'):
            del self._html_cache

        #Run get the input text with all of the percent
        #directives parsed
        self._cleaned_input = self.parse_percent_directives()

    def input_text(self):
        """
        Returns this compute cell's input text.

        OUTPUT:

        - a string

        EXAMPLES::

            sage: C = sagenb.notebook.cell.Cell(0, '2+3', '5', None)
            sage: C.input_text()
            u'2+3'
        """
        return self.__in

    def cleaned_input_text(self):
        r"""
        Returns this compute cell's "cleaned" input text, i.e., its
        input with all of its percent directives removed.  If this
        cell is interacting, it returns the interacting text.

        OUTPUT:

        - a string

        EXAMPLES::

            sage: C = sagenb.notebook.cell.Cell(0, '%hide\n%maxima\n2+3', '5', None)
            sage: C.cleaned_input_text()
            u'2+3'
        """
        if self.is_interacting():
            return self.interact
        else:
            return self._cleaned_input

    def parse_percent_directives(self):
        r"""
        Parses this compute cell's percent directives, determines its
        system (if any), and returns the "cleaned" input text.

        OUTPUT:

        - a string

        EXAMPLES::

            sage: C = sagenb.notebook.cell.Cell(0, '%hide\n%maxima\n2+3', '5', None)
            sage: C.parse_percent_directives()
            u'2+3'
            sage: C.percent_directives()
            [u'hide', u'maxima']
        """
        self._system = None
        text = self.input_text().splitlines()
        directives = []
        i = 0
        for i, line in enumerate(text):
            line = line.strip()
            if not line.startswith('%'):
                #Handle the #auto case here for now
                if line == "#auto":
                    pass
                else:
                    break
            elif line in ['%auto', '%hide', '%hideall', '%save_server', '%time', '%timeit']:
                # We do not consider any of the above percent
                # directives as specifying a system.
                pass
            else:
                self._system = line[1:]

            directives.append(line[1:])

        self._percent_directives = directives
        return "\n".join(text[i:]).strip()

    def percent_directives(self):
        r"""
        Returns a list of this compute cell's percent directives.

        OUTPUT:

        - a list of strings

        EXAMPLES::

            sage: C = sagenb.notebook.cell.Cell(0, '%hide\n%maxima\n2+3', '5', None)
            sage: C.percent_directives()
            [u'hide', u'maxima']
        """
        return self._percent_directives

    def system(self):
        r"""
        Returns the system used to evaluate this compute cell.  The
        system is specified by a percent directive like '%maxima' at
        the top of a cell.

        Returns None, if no system is explicitly specified.  In this
        case, the notebook evaluates the cell using the worksheet's
        default system.

        OUTPUT:

        - a string

        EXAMPLES::

            sage: C = sagenb.notebook.cell.Cell(0, '%maxima\n2+3', '5', None)
            sage: C.system()
            u'maxima'
            sage: prefixes = ['%hide', '%time', '']
            sage: cells = [sagenb.notebook.cell.Cell(0, '%s\n2+3'%prefix, '5', None) for prefix in prefixes]
            sage: [(C, C.system()) for C in cells if C.system() is not None]
            []
        """
        self.parse_percent_directives()
        return self._system


    def is_auto_cell(self):
        r"""
        Returns whether this compute cell is evaluated automatically
        when its worksheet object starts up.

        OUTPUT:

        - a boolean

        EXAMPLES::

            sage: C = sagenb.notebook.cell.Cell(0, '2+3', '5', None)
            sage: C.is_auto_cell()
            False
            sage: C = sagenb.notebook.cell.Cell(0, '#auto\n2+3', '5', None)
            sage: C.is_auto_cell()
            True
        """
        return 'auto' in self.percent_directives()

    def changed_input_text(self):
        """
        Returns the changed input text for this compute cell.  If
        there is any changed input text, it is reset to '' before this
        method returns.

        OUTPUT:

        - a string

        EXAMPLES::

            sage: C = sagenb.notebook.cell.Cell(0, '2+3', '5', None)
            sage: C.changed_input_text()
            ''
            sage: C.set_changed_input_text('3+3')
            sage: C.input_text()
            u'3+3'
            sage: C.changed_input_text()
            u'3+3'
            sage: C.changed_input_text()
            ''
            sage: C.version()
            0
        """
        try:
            t = self.__changed_input
            del self.__changed_input
            return t
        except AttributeError:
            return ''

    def set_changed_input_text(self, new_text):
        """
        Updates this compute cell's changed input text.  Note: This
        does not update the version of the cell.  It's typically used,
        e.g., for tab completion.

        INPUT:

        - ``new_text`` - a string; the new changed input text

        EXAMPLES::

            sage: C = sagenb.notebook.cell.Cell(0, '2+3', '5', None)
            sage: C.set_changed_input_text('3+3')
            sage: C.input_text()
            u'3+3'
            sage: C.changed_input_text()
            u'3+3'
        """
        new_text = unicode_str(new_text)

        self.__changed_input = new_text
        self.__in = new_text

    def set_output_text(self, output, html, sage=None):
        r"""
        Sets this compute cell's output text.

        INPUT:

        - ``output`` - a string; the updated output text

        - ``html`` - a string; updated output HTML

        - ``sage`` - a :class:`sage` instance (default: None); the
          sage instance to use for this cell(?)

        EXAMPLES::

            sage: C = sagenb.notebook.cell.Cell(0, '2+3', '5', None)
            sage: len(C.plain_text())
            11
            sage: C.set_output_text('10', '10')
            sage: len(C.plain_text())
            12
        """
        output = unicode_str(output)
        html = unicode_str(html)
        if output.count('<?__SAGE__TEXT>') > 1:
            html = u'<h3><font color="red">WARNING: multiple @interacts in one cell disabled (not yet implemented).</font></h3>'
            output = u''

        # In interacting mode, we just save the computed output
        # (do not overwrite).
        if self.is_interacting():
            self._interact_output = (output, html)
            return

        if hasattr(self, '_html_cache'):
            del self._html_cache

        output = output.replace('\r','')
        # We do not truncate if "notruncate" or "Output truncated!" already
        # appears in the output.  This notruncate tag is used right now
        # in sage.server.support.help.
        if 'notruncate' not in output and 'Output truncated!' not in output and \
               (len(output) > MAX_OUTPUT or output.count('\n') > MAX_OUTPUT_LINES):
            url = ""
            if not self.computing():
                file = os.path.join(self.directory(), "full_output.txt")
                open(file,"w").write(output.encode('utf-8', 'ignore'))
                url = "<a target='_new' href='%s/full_output.txt' class='file_link'>full_output.txt</a>"%(
                    self.url_to_self())
                html+="<br>" + url
            lines = output.splitlines()
            start = '\n'.join(lines[:MAX_OUTPUT_LINES/2])[:MAX_OUTPUT/2]
            end = '\n'.join(lines[-MAX_OUTPUT_LINES/2:])[-MAX_OUTPUT/2:]
            warning = 'WARNING: Output truncated!  '
            if url:
                # make the link to the full output appear at the top too.
                warning += '\n<html>%s</html>\n'%url
            output = warning + '\n\n' + start + '\n\n...\n\n' + end
        self.__out = output
        if not self.is_interactive_cell():
            self.__out_html = html
        self.__sage = sage

    def sage(self):
        """
        Returns the :class:`sage` instance for this compute cell(?).

        OUTPUT:

        - an instance of :class:`sage`

        EXAMPLES::

            sage: C = sagenb.notebook.cell.Cell(0, '2+3', '5', None)
            sage: C.sage() is None
            True
        """
        try:
            return self.__sage
        except AttributeError:
            return None

    def output_html(self):
        """
        Returns this compute cell's HTML output.

        OUTPUT:

        - a string

        EXAMPLES::

            sage: C = sagenb.notebook.cell.Cell(0, '2+3', '5', None)
            sage: C.output_html()
            ''
            sage: C.set_output_text('5', '<strong>5</strong>')
            sage: C.output_html()
            u'<strong>5</strong>'
        """
        try:
            return self.__out_html
        except AttributeError:
            self.__out_html = ''
            return ''

    def process_cell_urls(self, urls):
        """
        Processes this compute cell's ``'cell://.*?'`` URLs, replacing
        the protocol with the cell's path and appending the cell's
        version number.

        INPUT:

        - ``urls`` - a string; the URLs to process

        OUTPUT:

        - a string

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(tmp_dir()+'.sagenb')
            sage: nb.add_user('sage','sage','sage@sagemath.org',force=True)
            sage: W = nb.create_new_worksheet('Test', 'sage')
            sage: C = sagenb.notebook.cell.Cell(0, '2+3', '5', W)
            sage: C.process_cell_urls('"cell://foobar"')
            '/home/sage/0/cells/0/foobar?0'
        """
        end = '?%d' % self.version()
        begin = self.url_to_self()
        for s in re_cell.findall(urls) + re_cell_2.findall(urls):
            urls = urls.replace(s,begin + s[7:-1] + end)
        return urls

    def output_text(self, ncols=0, html=True, raw=False, allow_interact=True):
        u"""
        Returns this compute cell's output text.

        INPUT:

        - ``ncols`` - an integer (default: 0); the number of word wrap
          columns

        - ``html`` - a boolean (default: True); whether to output HTML

        - ``raw`` - a boolean (default: False); whether to output raw
          text (takes precedence over HTML)

        - ``allow_interact`` - a boolean (default: True); whether to
          allow :func:`sagenb.notebook.interact.interact`\ ion

        OUTPUT:

        - a string

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(tmp_dir()+'.sagenb')
            sage: nb.add_user('sage','sage','sage@sagemath.org',force=True)
            sage: W = nb.create_new_worksheet('Test', 'sage')
            sage: C = sagenb.notebook.cell.Cell(0, '2+3', '5', W)
            sage: C.output_text()
            u'<pre class="shrunk">5</pre>'
            sage: C.output_text(html=False)
            u'<pre class="shrunk">5</pre>'
            sage: C.output_text(raw=True)
            u'5'
            sage: C = sagenb.notebook.cell.Cell(0, u'ΫäĻƾṀБ', u'ΫäĻƾṀБ', W)
            sage: C.output_text()
            u'<pre class="shrunk">\xce\xab\xc3\xa4\xc4\xbb\xc6\xbe\xe1\xb9\x80\xd0\x91</pre>'
            sage: C.output_text(raw=True)
            u'\xce\xab\xc3\xa4\xc4\xbb\xc6\xbe\xe1\xb9\x80\xd0\x91'
        """
        if allow_interact and hasattr(self, '_interact_output'):
            # Get the input template
            z = self.output_text(ncols, html, raw, allow_interact=False)
            if not '<?__SAGE__TEXT>' in z or not '<?__SAGE__HTML>' in z:
                return z
            if ncols:
                # Get the output template
                try:
                    # Fill in the output template
                    output,html = self._interact_output
                    output = self.parse_html(output, ncols)
                    z = z.replace('<?__SAGE__TEXT>', output)
                    z = z.replace('<?__SAGE__HTML>', html)
                    return z
                except (ValueError, AttributeError), msg:
                    print msg
                    pass
            else:
                # Get rid of the interact div to avoid updating the
                # wrong output location during interact.
                return ''

        self.__out = unicode_str(self.__out)

        is_interact = self.is_interactive_cell()
        if is_interact and ncols == 0:
            if 'Traceback (most recent call last)' in self.__out:
                s = self.__out.replace('cell-interact','')
                is_interact=False
            else:
                return u'<h2>Click to the left again to hide and once more to show the dynamic interactive window</h2>'
        else:
            s = self.__out

        if raw:
            return s

        if html:
            s = self.parse_html(s, ncols)

        if (not is_interact and not self.is_html() and len(s.strip()) > 0 and
            '<div class="docstring">' not in s):
            s = '<pre class="shrunk">' + s.strip('\n') + '</pre>'

        return s.strip('\n')

    def parse_html(self, s, ncols):
        r"""
        Parses HTML for output, escaping and wrapping HTML and
        removing script elements.

        INPUT:

        - ``s`` - a string; the HTML to parse

        - ``ncols`` - an integer; the number of word wrap columns

        OUTPUT:

        - a string

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(tmp_dir()+'.sagenb')
            sage: nb.add_user('sage','sage','sage@sagemath.org',force=True)
            sage: W = nb.create_new_worksheet('Test', 'sage')
            sage: C = sagenb.notebook.cell.Cell(0, '2+3', '5', W)
            sage: C.parse_html('<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN">\n<html><head></head><body>Test</body></html>', 80)
            '&lt;!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0...Test</body>'
        """
        def format(x):
            return word_wrap(escape(x), ncols)

        def format_html(x):
            return self.process_cell_urls(x)

        # If there is an error in the output, specially format it.
        if not self.is_interactive_cell():
            s = format_exception(format_html(s), ncols)

        # Everything not wrapped in <html> ... </html> should be
        # escaped and word wrapped.
        t = ''

        while len(s) > 0:
            i = s.find('<html>')
            if i == -1:
                t += format(s)
                break
            j = s.find('</html>')
            if j == -1:
                t += format(s[:i])
                break
            t += format(s[:i]) + format_html(s[i+6:j])
            s = s[j+7:]
        t = t.replace('</html>','')

        # Get rid of the <script> tags, since we do not want them to
        # be evaluated twice.  They are only evaluated in the wrapped
        # version of the output.
        if ncols == 0:
            t = re_script.sub('', t)
        return t


    def has_output(self):
        """
        Returns whether this compute cell has any output.

        OUTPUT:

        - a boolean

        EXAMPLES::

            sage: C = sagenb.notebook.cell.Cell(0, '2+3', '5', None)
            sage: C.has_output()
            True
            sage: C = sagenb.notebook.cell.Cell(0, '2+3', '', None)
            sage: C.has_output()
            False
        """
        return len(self.__out.strip()) > 0

    def is_html(self):
        r"""
        Returns whether this is an HTML compute cell, e.g., its system
        is 'html'.  This is typically specified by the percent
        directive ``%html``.

        OUTPUT:

        - a boolean

        EXAMPLES::

            sage: C = sagenb.notebook.cell.Cell(0, "%html\nTest HTML", None, None)
            sage: C.system()
            u'html'
            sage: C.is_html()
            True
            sage: C = sagenb.notebook.cell.Cell(0, "Test HTML", None, None)
            sage: C.is_html()
            False
        """
        return self.system() == 'html'

    #################
    # Introspection #
    #################
    def set_introspect_html(self, html, completing=False, raw=False):
        u"""
        Sets this compute cell's introspection text.

        INPUT:

        - ``html`` - a string; the updated text

        - ``completing`` - a boolean (default: False); whether the
          completions menu is open

        - ``raw`` - a boolean (default: False)

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(tmp_dir()+'.sagenb')
            sage: nb.add_user('sage','sage','sage@sagemath.org',force=True)
            sage: W = nb.create_new_worksheet('Test', 'sage')
            sage: C = sagenb.notebook.cell.Cell(0, 'sage?', '', W)
            sage: C.introspect()
            False
            sage: C.evaluate(username='sage')
            sage: W.check_comp(9999)     # random output -- depends on computer speed
            ('d', Cell 0; in=sage?, out=)
            sage: C.set_introspect_html('foobar')
            sage: C.introspect_html()
            u'foobar'
            sage: C.set_introspect_html('`foobar`')
            sage: C.introspect_html()
            u'`foobar`'
            sage: C.set_introspect_html(u'ΫäĻƾṀБ')
            sage: C.introspect_html()
            u'\xce\xab\xc3\xa4\xc4\xbb\xc6\xbe\xe1\xb9\x80\xd0\x91'
            sage: W.quit()
            sage: nb.delete()
        """
        html = unicode_str(html)

        self.__introspect_html = html

    def introspect_html(self):
        """
        Returns this compute cell's introspection text, setting it to
        '', if none is available.

        OUTPUT:

        - a string

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(tmp_dir()+'.sagenb')
            sage: nb.add_user('sage','sage','sage@sagemath.org',force=True)
            sage: W = nb.create_new_worksheet('Test', 'sage')
            sage: C = sagenb.notebook.cell.Cell(0, 'sage?', '', W)
            sage: C.introspect()
            False
            sage: C.evaluate(username='sage')
            sage: W.check_comp(9999)     # random output -- depends on computer speed
            ('d', Cell 0; in=sage?, out=)
            sage: C.introspect_html()     # random output -- depends on computer speed
            u'...<div class="docstring">...sage...</pre></div>...'
            sage: W.quit()
            sage: nb.delete()
        """
        if not self.introspect():
            return ''
        try:
            return self.__introspect_html
        except AttributeError:
            self.__introspect_html = u''
            return u''

    def introspect(self):
        """
        Returns compute cell's introspection text.

        OUTPUT:

        - a string 2-tuple ("before" and "after" text) or boolean (not
          introspecting)

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(tmp_dir()+'.sagenb')
            sage: nb.add_user('sage','sage','sage@sagemath.org',force=True)
            sage: W = nb.create_new_worksheet('Test', 'sage')
            sage: C = sagenb.notebook.cell.Cell(0, 'sage?', '', W)
            sage: C.introspect()
            False
            sage: C.evaluate(username='sage')
            sage: W.check_comp(9999)     # random output -- depends on computer speed
            ('d', Cell 0; in=sage?, out=)
            sage: C.introspect()
            [u'sage?', '']
            sage: W.quit()
            sage: nb.delete()
        """
        try:
            return self.__introspect
        except AttributeError:
            return False

    def unset_introspect(self):
        """
        Clears this compute cell's introspection text.

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(tmp_dir()+'.sagenb')
            sage: nb.add_user('sage','sage','sage@sagemath.org',force=True)
            sage: W = nb.create_new_worksheet('Test', 'sage')
            sage: C = sagenb.notebook.cell.Cell(0, 'sage?', '', W)
            sage: C.introspect()
            False
            sage: C.evaluate(username='sage')
            sage: W.check_comp(9999)     # random output -- depends on computer speed
            ('d', Cell 0; in=sage?, out=)
            sage: C.introspect()
            [u'sage?', '']
            sage: C.unset_introspect()
            sage: C.introspect()
            False
            sage: W.quit()
            sage: nb.delete()
        """
        self.__introspect = False

    def set_introspect(self, before_prompt, after_prompt):
        """
        Set this compute cell's introspection text.

        INPUT:

        - ``before_prompt`` - a string

        - ``after_prompt`` - a string

        EXAMPLES::

            sage: C = sagenb.notebook.cell.Cell(0, '2+3', '5', None)
            sage: C.set_introspect("a", "b")
            sage: C.introspect()
            ['a', 'b']
        """
        self.__introspect = [before_prompt, after_prompt]

    def evaluate(self, introspect=False, time=None, username=None):
        r"""
        Evaluates this compute cell.

        INPUT:

        - ``introspect`` - a pair [``before_cursor``,
           ``after_cursor``] of strings (default: False)

        - ``time`` - a boolean (default: None); whether to return the
          time the computation takes

        - ``username`` - a string (default: None); name of user doing
           the evaluation

        EXAMPLES:

        We create a notebook, worksheet, and cell and evaluate it
        in order to compute `3^5`::

            sage: nb = sagenb.notebook.notebook.load_notebook(tmp_dir()+'.sagenb')
            sage: nb.add_user('sage','sage','sage@sagemath.org',force=True)
            sage: W = nb.create_new_worksheet('Test', 'sage')
            sage: W.edit_save('{{{\n3^5\n}}}')
            sage: C = W.cell_list()[0]; C
            Cell 0; in=3^5, out=
            sage: C.evaluate(username='sage')
            sage: W.check_comp(wait=9999)     # random output -- depends on computer speed
            ('d', Cell 0; in=3^5, out=
            243
            )
            sage: C     # random output -- depends on computer speed
            Cell 0; in=3^5, out=
            243
            sage: W.quit()
            sage: nb.delete()
        """
        if introspect:
            self.eval_method = 'introspect' # Run through TAB-introspection
        else:
            self.eval_method = 'eval' # Run through S-Enter, evaluate link, etc.
        self.__interrupted = False
        self.__evaluated = True
        if time is not None:
            self.__time = time
        self.__introspect = introspect
        self.__worksheet.enqueue(self, username=username)
        self.__type = 'wrap'
        dir = self.directory()
        for D in os.listdir(dir):
            F = os.path.join(dir, D)
            try:
                os.unlink(F)
            except OSError:
                try:
                    shutil.rmtree(F)
                except:
                    pass

    def version(self):
        """
        Returns this compute cell's version number.

        OUTPUT:

        - an integer

        EXAMPLES::

            sage: C = sagenb.notebook.cell.Cell(0, '2+3', '5', None)
            sage: C.version()
            0
            sage: C.set_input_text('2+3')
            sage: C.version()
            1
        """
        try:
            return self.__version
        except AttributeError:
            self.__version = 0
            return self.__version

    def time(self):
        r"""
        Returns whether to print timing information about the
        evaluation of this compute cell.

        OUTPUT:

        - a boolean

        EXAMPLES::

            sage: C = sagenb.notebook.cell.Cell(0, '2+3', '5', None)
            sage: C.time()
            False
            sage: C = sagenb.notebook.cell.Cell(0, '%time\n2+3', '5', None)
            sage: C.time()
            True
        """
        return ('time' in self.percent_directives() or
                'timeit' in self.percent_directives() or
                getattr(self, '__time', False))

    def doc_html(self, wrap=None, div_wrap=True, do_print=False):
        """
        Returns HTML for a doc browser cell.  This is a modified
        version of :meth:``html``.

        This is a hack and needs to be improved.  The problem is how
        to get the documentation HTML to display nicely between the
        example cells.  The type setting (jsMath formatting) needs
        attention too.

        TODO: Remove this hack (:meth:`doc_html`)

        INPUT:

        - ``wrap`` - an integer (default: None); the number of word
          wrap columns

        - ``div_wrap`` - a boolean (default: True); whether to wrap
          the output in outer div elements

        - ``do_print`` - a boolean (default: False); whether to return
          output suitable for printing

        OUTPUT:

        - a string
        """
        self.evaluate()
        return self.html(wrap, div_wrap, do_print)

    def html(self, wrap=None, div_wrap=True, do_print=False):
        r"""
        Returns the HTML for this compute cell.

        INPUT:

        - ``wrap`` - an integer (default: None); the number of word
          wrap columns

        - ``div_wrap`` - a boolean (default: True); whether to wrap
          the output in outer div elements

        - ``do_print`` - a boolean (default: False); whether to return
          output suitable for printing

        OUTPUT:

        - a string

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.load_notebook(tmp_dir()+'.sagenb')
            sage: nb.add_user('sage','sage','sage@sagemath.org',force=True)
            sage: W = nb.create_new_worksheet('Test', 'sage')
            sage: C = sagenb.notebook.cell.Cell(0, '2+3', '5', W)
            sage: C.html()
            u'...cell_outer_0...2+3...5...'
        """
        from template import template

        if wrap is None:
            wrap = self.notebook().conf()['word_wrap_cols']

        return template(os.path.join('html', 'notebook', 'cell.html'),
                        cell=self, wrap=wrap,
                        div_wrap=div_wrap, do_print=do_print)

    def url_to_self(self):
        """
        Returns a notebook URL for this compute cell.

        OUTPUT:

        - a string

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(tmp_dir()+'.sagenb')
            sage: nb.add_user('sage','sage','sage@sagemath.org',force=True)
            sage: W = nb.create_new_worksheet('Test', 'sage')
            sage: C = sagenb.notebook.cell.Cell(0, '2+3', '5', W)
            sage: C.url_to_self()
            '/home/sage/0/cells/0'
        """
        try:
            return self.__url_to_self
        except AttributeError:
            self.__url_to_self = '/home/%s/cells/%s'%(self.worksheet_filename(), self.id())
            return self.__url_to_self

    def files(self):
        """
        Returns a list of all the files in this compute cell's
        directory.

        OUTPUT:

        - a list of strings

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(tmp_dir()+'.sagenb')
            sage: nb.add_user('sage','sage','sage@sagemath.org',force=True)
            sage: W = nb.create_new_worksheet('Test', 'sage')
            sage: C = sagenb.notebook.cell.Cell(0, 'plot(sin(x),0,5)', '', W)
            sage: C.evaluate()
            sage: W.check_comp(wait=9999)     # random output -- depends on computer speed
            ('d', Cell 0; in=plot(sin(x),0,5), out=
            <html><font color='black'><img src='cell://sage0.png'></font></html>
            <BLANKLINE>
            )
            sage: C.files()     # random output -- depends on computer speed
            ['sage0.png']
            sage: W.quit()
            sage: nb.delete()
        """
        dir = self.directory()
        D = os.listdir(dir)
        return D

    def delete_files(self):
        """
        Deletes all of the files associated with this compute cell.

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(tmp_dir()+'.sagenb')
            sage: nb.add_user('sage','sage','sage@sagemath.org',force=True)
            sage: W = nb.create_new_worksheet('Test', 'sage')
            sage: C = sagenb.notebook.cell.Cell(0, 'plot(sin(x),0,5)', '', W)
            sage: C.evaluate()
            sage: W.check_comp(wait=9999)     # random output -- depends on computer speed
            ('d', Cell 0; in=plot(sin(x),0,5), out=
            <html><font color='black'><img src='cell://sage0.png'></font></html>
            <BLANKLINE>
            )
            sage: C.files()     # random output -- depends on computer speed
            ['sage0.png']
            sage: C.delete_files()
            sage: C.files()
            []
            sage: W.quit()
            sage: nb.delete()
        """
        try:
            dir = self._directory_name()
        except AttributeError:
            return
        if os.path.exists(dir):
            shutil.rmtree(dir, ignore_errors=True)

    def files_html(self, out):
        """
        Returns HTML to display the files in this compute cell's
        directory.

        INPUT:

        - ``out`` - a string; files to exclude.  To exclude bar, foo,
          ..., use the format ``'cell://bar cell://foo ...'``

        OUTPUT:

        - a string

        EXAMPLES::

            sage: nb = sagenb.notebook.notebook.Notebook(tmp_dir()+'.sagenb')
            sage: nb.add_user('sage','sage','sage@sagemath.org',force=True)
            sage: W = nb.create_new_worksheet('Test', 'sage')
            sage: C = sagenb.notebook.cell.Cell(0, 'plot(sin(x),0,5)', '', W)
            sage: C.evaluate()
            sage: W.check_comp(wait=9999)     # random output -- depends on computer speed
            ('d', Cell 0; in=plot(sin(x),0,5), out=
            <html><font color='black'><img src='cell://sage0.png'></font></html>
            <BLANKLINE>
            )
            sage: C.files_html('')     # random output -- depends on computer speed
            '<img src="/home/sage/0/cells/0/sage0.png?...">'
            sage: W.quit()
            sage: nb.delete()
        """
        import time
        D = self.files()
        D.sort()
        if len(D) == 0:
            return ''
        images = []
        files  = []

        from worksheet import CODE_PY
        # The question mark trick here is so that images will be reloaded when
        # the async request requests the output text for a computation.
        # This is inspired by http://www.irt.org/script/416.htm/.
        for F in D:
            if os.path.split(F)[-1] == CODE_PY or 'cell://%s'%F in out:
                continue
            url = os.path.join(self.url_to_self(), F)
            if F.endswith('.png') or F.endswith('.bmp') or \
                    F.endswith('.jpg') or F.endswith('.gif'):
                images.append('<img src="%s?%d">'%(url, time.time()))
            elif F.endswith('.obj'):
                images.append("""<a href="javascript:sage3d_show('%s', '%s_%s', '%s');">Click for interactive view.</a>"""%(url, self.__id, F, F[:-4]))
            elif F.endswith('.mtl') or F.endswith(".objmeta"):
                pass # obj data
            elif F.endswith('.svg'):
                images.append('<embed src="%s" type="image/svg+xml" name="emap">'%url)
            elif F.endswith('.jmol'):
                # If F ends in -size500.jmol then we make the viewer applet with size 500.
                i = F.rfind('-size')
                if i != -1:
                    size = F[i+5:-5]
                else:
                    size = 500

                if self.worksheet().docbrowser():
                    jmol_name = os.path.join(self.directory(), F)
                    jmol_file = open(jmol_name, 'r')
                    jmol_script = jmol_file.read()
                    jmol_file.close()

                    jmol_script = jmol_script.replace('defaultdirectory "', 'defaultdirectory "' + self.url_to_self() + '/')

                    jmol_file = open(jmol_name, 'w')
                    jmol_file.write(jmol_script)
                    jmol_file.close()

                script = '<div><script>jmol_applet(%s, "%s?%d");</script></div>' % (size, url, time.time())
                images.append(script)
            elif F.endswith('.jmol.zip'):
                pass # jmol data
            elif F.endswith('.canvas3d'):
                script = '<div><script>canvas3d.viewer("%s");</script></div>' % url
                images.append(script)
            else:
                link_text = str(F)
                if len(link_text) > 40:
                    link_text = link_text[:10] + '...' + link_text[-20:]
                files.append('<a target="_new" href="%s" class="file_link">%s</a>'%(url, link_text))
        if len(images) == 0:
            images = ''
        else:
            images = "%s"%'<br>'.join(images)
        if len(files)  == 0:
            files  = ''
        else:
            files  = ('&nbsp'*3).join(files)

        files = unicode_str(files)
        images = unicode_str(images)

        return images + files


# Alias
ComputeCell = Cell


#####################
# Utility functions #
#####################
def format_exception(s0, ncols):
    r"""
    Formats exceptions so they do not appear expanded by default.

    INPUT:

    - ``s0`` - a string

    - ``ncols`` - an integer; number of word wrap columns

    OUTPUT:

    - a string

    If ``s0`` contains "notracebacks," this function simply returns
    ``s0``.

    EXAMPLES::

        sage: sagenb.notebook.cell.format_exception(sagenb.notebook.cell.TRACEBACK,80)
        '\nTraceback (click to the left of this block for traceback)\n...\nTraceback (most recent call last):'
        sage: sagenb.notebook.cell.format_exception(sagenb.notebook.cell.TRACEBACK + "notracebacks",80)
        'Traceback (most recent call last):notracebacks'
    """
    s = s0.lstrip()
    # Add a notracebacks option -- if it is in the string then
    # tracebacks aren't shrunk.  This is currently used by the
    # sage.server.support.help command.
    if TRACEBACK not in s or 'notracebacks' in s:
        return s0
    if ncols > 0:
        s = s.strip()
        w = s.splitlines()
        for k in range(len(w)):
            if TRACEBACK in w[k]:
                break
        s = '\n'.join(w[:k]) + '\nTraceback (click to the left of this block for traceback)' + '\n...\n' + w[-1]
    else:
        s = s.replace("exec compile(ur'","")
        s = s.replace("' + '\\n', '', 'single')", "")
    return s

def number_of_rows(txt, ncols):
    r"""
    Returns the number of rows needed to display a string, given a
    maximum number of columns per row.

    INPUT:

    - ``txt`` - a string; the text to "wrap"

    - ``ncols`` - an integer; the number of word wrap columns

    OUTPUT:

    - an integer

    EXAMPLES::

        sage: from sagenb.notebook.cell import number_of_rows
        sage: s = "asdfasdf\nasdfasdf\n"
        sage: number_of_rows(s, 8)
        2
        sage: number_of_rows(s, 5)
        4
        sage: number_of_rows(s, 4)
        4
    """
    rows = txt.splitlines()
    nrows = len(rows)
    for i in range(nrows):
        nrows += int((len(rows[i])-1)/ncols)
    return nrows
