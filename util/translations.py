#!/usr/bin/env python

# -*- coding: utf-8 -*-
"""
    The sage notebook translation maintenance utility.

    When used as a command, this application is intended to extract
    translatable messages from source and to update the translations of the
    Sage notebook.

    This can be used as a module for other project by subclassing `Paths`,
    `LocalData`, and `TranslationFrontend`, overiding `Paths.get_paths()`,
    and `LocalData.get_data()` and `TranslationFrontend.parser` and by
    adding methods and attributes as neccesary to the three classes.

    :copyright: (c) 2014 by J. Miguel Farto
    :license: GPL, see http://www.gnu.org/licenses/
"""

import os
import os.path as pth
import shutil
import logging
import argparse
from datetime import datetime

from babel.core import Locale, UnknownLocaleError
from babel.messages.pofile import read_po, write_po
from babel.messages.mofile import write_mo
from babel.messages.catalog import Catalog
from babel.messages.extract import extract_from_dir


def restore(file_path):
    """Restores a file from a backup file of the same name ended by `~`.

    :param file_path: the absolute path of the file to restore.
    """
    backup_path = '{}~'.format(file_path)
    if pth.isfile(backup_path):
        shutil.copyfile(backup_path, file_path)


def clear(file_path):
    """Clears a backup file.

    :param file_path: the absolute path of the file whose backup ends by `~`.
    """
    backup_path = '{}~'.format(file_path)
    if pth.isfile(backup_path):
        os.remove(backup_path)


class Paths(object):
    """This class stores some paths in the source tree. You can subclass this
    and override the `get_paths` method accordingly with the source tree of
    your project.
    """
    def __init__(self):
        self.get_paths()

    def get_paths(self):
        """
        Defines some paths in the source tree as attributes for the Sage
        notebook. It must be overridden if subclassing for another project.
        Mandatory attributes that must be defined by this method:

        :attribute command_name: the file name of this script.
        :attribute src: the base path of the source tree.
        :attribute trans: the base path where translations are.
        :attribute pot: the messages template file of the project.
        """
        #: Some paths in the sage notebook source tree. This paths are obtained
        #: from the location of this file, so it must not be moved or copied
        #: and executed from other location. Symlinking is fine.
        self.command_name = pth.basename(__file__)
        self.src = pth.dirname(pth.dirname(pth.realpath(__file__)))
        self.trans = pth.join(self.src, 'sagenb', 'translations')
        self.pot = pth.join(self.src, 'sagenb', 'message.pot')

    def lang(self, lang_id):
        """Returns the path of the language `lang_id` in the source tree.

        :param lang_id: language identifier of the form xx_XX.
        """
        return pth.join(self.trans, lang_id, 'LC_MESSAGES', 'messages.po')


class LocalData(object):
    """Stores information about the sage notebook. You can subclass
    this and override the `get_data` method accordingly with the source tree of
    your project.

    :attribute path: a Path instance. It is available before `get_data()` is
                     called
    :attribute extract: a dictionary with kwargs for `Pot.extract`. Must be
                        overridden for other projects. Implemented as
                        @property.
    :attribute to_file: a dictionary with kwargs for `Pot.to_file`. Must be
                        overridden for other projects. Implemented as
                        @property.
    """
    def __init__(self):
        self.path = Paths()
        self.get_data()

    def get_data(self):
        """
        Defines some attributes for the Sage notebook localization system.
        It must be overridden if subclassing for another project.
        Mandatory attributes that must be defined by this method:

        :attribute keywords: the file name of this script.
        :attribute method_map: files with localizable messages in the sources.
                                (see
                                `babel.messages.extract.extract_from_dir()
                                documentation)
        :attribute options_map: options for every class of localizable files,
                                (see
                                `babel.messages.extract.extract_from_dir()
                                documentation)
        :attribute charset: charset for `babel.messages.catalog.Catalog`.
        :attribute sort_by_file: message ordering for po and pot files. This
                                 option keeps changes in po and pot files small
                                 when changes in notebook sources are small.
        :attribute width: max line length for po and pot files. This option
                          contributes to keep changes in po and pot files small
                          when changes in notebook sources are small.
        :attribute langs: list of identifiers for available localizations in
                          the notebook.
        :attribute lang_names: localized names of available localizations.
        """
        #: function names surrounding translatable strings
        self.keywords = {
            '_': None,
            'gettext': None,
            'ngettext': (1, 2),
            'ugettext': None,
            'ungettext': (1, 2),
            'dgettext': (2,),
            'dngettext': (2, 3),
            'N_': None,
            'pgettext': ((1, 'c'), 2),
            'npgettext': ((1, 'c'), 2, 3),
            'lazy_gettext': None,
            'lazy_pgettext': ((1, 'c'), 2),
        }
        #: Source files to extract messages
        self.method_map = [
            ('sagenb/notebook/**.py', 'python'),
            ('sagenb/flask_version/**.py', 'python'),
            ('sagenb/data/sage/html/**.html', 'jinja2'),
            ('sagenb/data/sage/js/**.js', 'jinja2')]
        #: Some configuration for each type of file
        self.options_map = {
            'sagenb/data/sage/html/**.html': {
                'encoding': 'utf-8',
                'extensions': 'jinja2.ext.autoescape,jinja2.ext.with_'},
            'sagenb/data/sage/js/**.js': {
                'encoding': 'utf-8',
                'extensions': 'jinja2.ext.autoescape,jinja2.ext.with_'},
            'sagenb/flask_version/**.py': {},
            'sagenb/notebook/**.py': {}}

        #: Some defaults for babel package
        self.charset = 'utf-8'
        self.sort_by_file = True
        self.width = 76

        #: Available translations in the source tree
        names = os.listdir(self.path.trans)
        self.langs = []
        self.lang_names = []
        for name in names:
            try:
                locale = Locale.parse(name)
            except UnknownLocaleError:
                pass
            else:
                self.langs.append(name)
                self.lang_names.append(locale.display_name)

    @property
    def extract(self):
        """A dictionary with kwargs for `Pot.extract`. Must be overridden for
        other projects.
        """
        return {
            'src_path': self.path.src,
            'method_map': self.method_map,
            'options_map': self.options_map,
            'keywords': self.keywords,
            'charset': self.charset,
            }

    @property
    def to_file(self):
        """A dictionary with kwargs for `Pot.to_file`. Must be overridden for
        other projects.
        """
        return {
            'width': self.width,
            'sort_by_file': self.sort_by_file
            }


class Pot(object):
    """This class encapsulates file operations and update from sources
    for a po or pot file. It uses the public API of the `babel` package.

    :param file_path: if is not `None`, the catalog is read from this file.
                      the catalog in empty in other case. Default is `None`.
    :attribute catalog: the catalog with the messages of the po/pot object.
                        It is a `babel.messages.catalog.Catalog`
    :attribute path: contains the path of the file associated if any. It is
                     `None` in other case.
    """
    def __init__(self, file_path=None, **kwargs):
        self.path = file_path
        if self.path is not None:
            self.from_file(self.path, **kwargs)
        else:
            self.catalog = Catalog(**kwargs)

    def extract(self, src_path='.', charset='utf-8', locale=None, **kwargs):
        """Extracts translatable messages from sources. This function is based
        on the extract function of the `pybabel` command, which is not part of
        the public API of `babel`. Only the public API of `babel` is used here.

        :param src_path: base path of the source tree, default is the current
                         path.
        :param charset: see the `babel.messages.catalog.Catalog` docs. Default
                        is `utf-8`.
        :param locale: see the `babel.messages.catalog.Catalog` docs. Default
                        is `None`.

        Other optional keyword parameters are passed to
        `babel.messages.extract.extract_from_dir` see `babel` public API docs.
        """
        #: This is the babel.messages.catalog.Catalog to contain the
        #: extracted messages
        self.catalog = Catalog(charset=charset, locale=locale)

        if not pth.isdir(src_path):
            raise IOError('{} is not a directory'.format(src_path))

        #: Extracts the data from source in a low level format. This is
        #: the only way present in babel's public API.
        extracted = extract_from_dir(src_path, **kwargs)

        #: Constructs the catalog from the raw extracted data.
        #: Based on the source code of pybabel:
        #: babel.messages.frontend.extract_messages.run
        for filename, lineno, message, comments, context in extracted:
            self.catalog.add(message, None, [(filename, lineno)],
                             auto_comments=comments, context=context)

    def from_file(self, file_path, **kwargs):
        """Reads the message's catalog from a file

        :param file_path: a path to a po/pot file. A exception is raised if the
        file does not exist. The `path` attribute is updated with this value.

        Other optional keyword parameters are passed to
        `babel.messages.pofile.read_po()` see `babel` public API docs.
        """
        with open(file_path, 'rt') as f:
            self.catalog = read_po(f, **kwargs)
        self.path = file_path

    def to_file(self, file_path=None, backup=True, warn=False, **kwargs):
        """Writes the catalog to a file.

        :param file_path: if the `file_path` attribute is  `None`, `path` is
                          taken as the output file and `file_path` parameter is
                          discarded. If `file_path` is not `None`, the output
                          file is `file_path` and `path` is not updated.
                          Default is `None`.
        :param backup: if `True` and the output file exists, a backup is made
                       prior to overwrite the file. Further backups overwrite
                       the previous.
        :param warn: if `True` warnings about fuzzy, untranslated and obsolete
                     messages are issued.

        Other optional keyword parameters are passed to
        `babel.messages.pofile.write_po()` see `babel` public API docs.
        """
        if file_path is None:
            file_path = self.path
        if pth.isfile(file_path) and backup:
            shutil.copy(file_path, '{}~'.format(file_path))

        if warn:
            logging.basicConfig(level=logging.WARNING)
            fuzzy = 0
            untrans = 0
            obsolete = len(self.catalog.obsolete)
            for message in self.catalog:
                if message.fuzzy and message.id:
                    fuzzy += 1
                if not message.string:
                    untrans += 1
            if fuzzy:
                logging.warning('There are {} fuzzy messages in {}.\n'.format(
                    fuzzy, file_path))
            if untrans:
                logging.warning('There are {} untranslated messages '
                                'in {}.\n'.format(untrans, file_path))
            if obsolete:
                logging.warning('There are {} obsolete  messages '
                                'in {}.\n'.format(obsolete, file_path))
        else:
            logging.basicConfig(level=logging.INFO)

        with open(file_path, 'wb') as f:
            write_po(f, self.catalog, **kwargs)

    def update(self, template_po, *args, **kwargs):
        """updates the catalog from a pot.

        :param template_po: a pot with a message template catalog. See
        `babel.messages.catalog.Catalog()`
        """
        self.catalog.update(template_po.catalog, *args, **kwargs)


class Po(Pot):
    """a class specific for actual localizations, not templates (po files).
    It is like Pot, but with .mo ouput capabilities.
    """

    def compile(self, file_path=None, backup=True, **kwargs):
        """
        :param file_path: if the `file_path` attribute is  `None`, `path` is
                          taken as the output file and `file_path` parameter is
                          discarded. If `file_path` is not `None`, the output
                          file is `file_path` and `path` is not updated.
                          Default is `None`. File extension is supposed
                          to be '.po' and is changed to `.mo` before writing.
        :param backup: if `True` and the output file exists, a backup is made
                       prior to overwrite the file. Further backups overwrite
                       the previous.

        Other optional keyword parameters are passed to
        `babel.messages.mofile.write_mo()` see `babel` public API docs.
        """
        if file_path is None:
            file_path = self.path
        if file_path is not None:
            file_path = file_path[:-2] + 'mo'
        if pth.isfile(file_path) and backup:
            shutil.copy(file_path, '{}~'.format(file_path))
        with open(file_path, 'wb') as f:
            write_mo(f, self.catalog, **kwargs)


class LangsAction(argparse.Action):
    """action for the --langs/--nolangs option
            --langs - add all available langs
            --langs xx_XX ... - add selected langs
            --nolangs - remove all langs processing
            --nolangs xx_XX ... - remove selected langs
            no language is processed by default
            Examples:
              To process only spanish and french:
                translations.py ACTION --langs es_ES fr_FR
              To process all but spanish and french'
                translations.py ACTION --langs --nolangs es_ES fr_FR
    """
    def __call__(self, parser, namespace, values, option_string=None):
        old_values = getattr(namespace, self.dest)
        if option_string == '--langs':
            values = set(values) if values else set(self.choices)
            values.update(old_values)
        elif option_string == '--nolangs':
            values = set(values) if values else set(self.choices)
            values = old_values.difference(values)
        else:
            values = old_values
        setattr(namespace, self.dest, values)


class NoList(list):
    """A tuned list whichs lies about membership. Used by the parser.
    """
    def __contains__(self, item):
        return not super(self.__class__, self).__contains__(item)


class TranslationFrontend(object):
    """Frontend for this module when used as a command. Issue
    `nb_src_path/util/translations.py -h` to obtain detailed help.

    Examples:

        `translations.py update --pot --langs`
            updates message.pot and messages.po for all the localizations
            from messages from the source tree. obsolete, fuzzy and
            untranslated messages must be edited by hand in every file. This
            command makes backups of all the files.

        `translations.py update --langs es_ES pt_BR`
            the same, but only for the listed localizations.

        `translations.py update --langs --nolangs fr_FR --nobackupi --fuzzy`
            the same, but for all the localizations except french and no
            backups are done. Fuzzy update is performed.

        `translations.py update --pot --nowarn`
            updates only the templates message.pot and no warnings about fuzzy,
            obsolete and untranslated messages are issued (for a template file
            all messages are untranslated).

        `translations.py restore --pot --langs`
            restores all backups present.

        `translations.py clear --pot --langs`
            clears all backups present (including backup for .mo files).

        `translations.py compile --langs`
            generate .mo files from .po for all the localizations.

        `translations.py extract`
            generates a new template file (message.pot) and backup the
            existing.

        `translations.py init zh_CN`
            creates the mandarin chinese localization infrastructure to start
            the actual task with the .po file.
    """
    def __init__(self, **kwargs):
        self.data = LocalData()
        self.args = self.parser.parse_args()

    @property
    def parser(self):
        """the `argparse` parser
        """
        parser = argparse.ArgumentParser(
            description='Localization management for sage notebook',
            epilog='This command does nothing without additional options.\n'
                   'To see options available for every subcommand, type:\n'
                   '    {} SUBCOMMAND -h'.format(self.data.path.command_name),
            )
        pot_parser = argparse.ArgumentParser(add_help=False)
        pot_parser.add_argument(
            '--pot',
            dest='pot',
            action='store_true',
            help='Perform ACTION on sage message.pot file\n',
            )

        langs_parser = argparse.ArgumentParser(add_help=False)
        langs_parser.add_argument(
            '--langs', '--nolangs',
            dest='langs',
            action=LangsAction,
            nargs='*',
            choices=self.data.langs,
            default=set(),
            metavar=('xx_XX', 'yy_YY'),
            help='--langs - add all available langs\n'
                 '--langs xx_XX ... - add selected langs\n'
                 '--nolangs - remove all langs processing\n'
                 '--nolangs xx_XX ... - remove selected langs\n'
                 'no language is processed by default.\n'
                 'Examples:\n'
                 '  To process only spanish and french:\n'
                 '    translations.py ACTION --langs es_ES fr_FR\n'
                 '  To process all but spanish and french:\n'
                 '    translations.py ACTION --langs --nolangs es_ES fr_FR\n'
            )

        backup_parser = argparse.ArgumentParser(add_help=False)
        backup_parser.add_argument(
            '--nobackup',
            dest='backup',
            action='store_false',
            help='Deactivate backup for processed files\n',
            )

        subparsers = parser.add_subparsers(
            metavar='SUBCOMMAND',
            title='subcommands',
            description='',
            help='is one of:',
            )

        parser_update = subparsers.add_parser(
            'update', parents=(pot_parser, langs_parser, backup_parser),
            help='updates pot and/or po files from sources',
            description='updates pot and/or po files from source tree',
            epilog='Warning: If backup is active, previous backup files '
                   'are overwritten',
            formatter_class=argparse.RawTextHelpFormatter,
            )
        parser_update.add_argument(
            '--nowarn',
            dest='warn',
            action='store_false',
            help='Prevent warning about fuzzy, untranslated and\n'
                 'obsolete messages to be printed',
            )
        parser_update.add_argument(
            '--fuzzy',
            dest='nofuzzy',
            action='store_false',
            help='Fuzzy matching of message IDs\n',
            )
        parser_update.set_defaults(func=self.update)

        parser_extract = subparsers.add_parser(
            'extract', parents=(backup_parser,),
            help='extract a new pot file from sources',
            description='extract a new message.pot template file from sources',
            epilog='Warning: If backup is active, previous backup files '
                   'are overwritten',
            formatter_class=argparse.RawTextHelpFormatter,
            )
        parser_extract.set_defaults(func=self.extract)

        parser_restore = subparsers.add_parser(
            'restore', parents=(pot_parser, langs_parser),
            help='restores pot and/or po from backup files',
            description='restores pot and/or po from backup files if exist',
            epilog='Warning: If a particular backup file is not present, '
                   'the corresponding file\n'
                   '         is not restored',
            formatter_class=argparse.RawTextHelpFormatter,
            )
        parser_restore.set_defaults(func=self.restore)

        parser_clear = subparsers.add_parser(
            'clear', parents=(pot_parser, langs_parser),
            help='clear pot and/or po backup files',
            description='clear pot and/or po backup files',
            epilog='Warning: Backups for the corresponding mo files are also '
                   'cleared',
            formatter_class=argparse.RawTextHelpFormatter,
            )
        parser_clear.set_defaults(func=self.clear)

        parser_compile = subparsers.add_parser(
            'compile', parents=(langs_parser, backup_parser),
            help='generate mo files from po files',
            description='generate mo files from po files',
            epilog='Warning: Previous mo files are overwritten.\n'
                   '         If backup is active, previous backup files '
                   'are overwritten',
            formatter_class=argparse.RawTextHelpFormatter,
            )
        parser_compile.set_defaults(func=self.compile)

        parser_init = subparsers.add_parser(
            'init',
            help='generate a new localization from source tree messages',
            description='generate a new localization from source tree '
                        'messages',
            epilog='Warning: Existing localizations or incorrect identifiers '
                   'not allowed',
            formatter_class=argparse.RawTextHelpFormatter,
            )
        parser_init.add_argument(
            'lang',
            choices=NoList(self.data.langs),
            help='locale identifier',
            metavar='xx_XX',
            )
        parser_init.set_defaults(func=self.init)

        return parser

    def __call__(self):
        self.args.func()

    def update(self):
        """Action function for the `update` subcommand
        """
        pot_new = Pot()
        pot_new.extract(**self.data.extract)

        if self.args.pot:
            pot_old = Pot(self.data.path.pot)
            pot_old.update(pot_new, no_fuzzy_matching=self.args.nofuzzy)
            pot_old.to_file(backup=self.args.backup, warn=self.args.warn,
                            **self.data.to_file)

        for lang in self.args.langs.difference(('en_US',)):
            po = Po(self.data.path.lang(lang), locale=lang)
            po.update(pot_new, no_fuzzy_matching=self.args.nofuzzy)
            for lang in self.data.langs:
                po.catalog.obsolete.pop(lang, None)
            self.complete_update(po)
        if 'en_US' in self.args.langs:
            po = Po(self.data.path.lang('en_US'), locale='en_US')
            self.complete_update(po)

    def complete_update(self, po):
        for lang, name in zip(self.data.langs, self.data.lang_names):
            po.catalog.add(lang, name)
        po.to_file(backup=self.args.backup, warn=self.args.warn,
                   **self.data.to_file)

    def extract(self):
        """Action function for the `extract` subcommand
        """
        pot = Pot()
        pot.extract(**self.data.extract)
        pot.path = self.data.path.pot
        pot.to_file(backup=self.args.backup, warn=False, **self.data.to_file)

    def restore(self):
        """Action function for the `restore` subcommand
        """
        if self.args.pot:
            restore(self.data.path.pot)
        for lang in self.args.langs:
            po_path = self.data.path.lang(lang)
            mo_path = po_path[:-2] + 'mo'
            restore(po_path)
            restore(mo_path)

    def clear(self):
        """Action function for the `clear` subcommand
        """
        if self.args.pot:
            clear(self.data.path.pot)
        for lang in self.args.langs:
            po_path = self.data.path.lang(lang)
            mo_path = po_path[:-2] + 'mo'
            clear(po_path)
            clear(mo_path)

    def compile(self):
        """Action function for the `compile` subcommand
        """
        for lang in self.args.langs:
            po = Po(self.data.path.lang(lang))
            po.compile(backup=self.args.backup)

    def init(self):
        """action function for the `init` subcommand
        """
        po = Po()
        po.extract(locale=self.args.lang, **self.data.extract)
        po.path = self.data.path.lang(self.args.lang)

        #: Based on the source code of pybabel:
        #: babel.messages.frontend
        po.catalog.revision_date = datetime.now()
        po.catalog.fuzzy = False

        os.makedirs(pth.dirname(po.path))
        self.args.backup = False
        self.args.warn = False
        self.complete_update(po)


if __name__ == '__main__':
    frontend = TranslationFrontend()
    frontend()
