#!/usr/bin/env python

# -*- coding: utf-8 -*-
import argparse
import shutil
import os
import os.path as pth
import logging

from babel.core import Locale
from babel.messages.pofile import read_po, write_po
from babel.messages.mofile import write_mo
from babel.messages.catalog import Catalog
from babel.messages.extract import extract_from_dir

KEYWORDS = {
    '_': None,
    'gettext': None,
    'ngettext': (1, 2),
    'ugettext': None,
    'ungettext': (1, 2),
    'dgettext': (2,),
    'dngettext': (2, 3),
    'N_': None,
    'pgettext': ((1, 'c'), 2)
}
METHOD_MAP = [
    ('**/notebook/**.py', 'python'),
    ('**/flask_version/**.py', 'python'),
    ('**/data/sage/html/**.html', 'jinja2'),
    ('**/data/sage/js/**.js', 'jinja2')]
OPTIONS_MAP = {
    '**/data/sage/html/**.html': {
        'encoding':'utf-8',
        'extensions': 'jinja2.ext.autoescape,jinja2.ext.with_'},
    '**/data/sage/js/**.js': {
        'encoding': 'utf-8',
        'extensions': 'jinja2.ext.autoescape,jinja2.ext.with_'},
    '**/flask_version/**.py': {},
    '**/notebook/**.py': {}}
CHARSET='utf-8',
SORT_BY_FILE=True
WIDTH = 76

src_path =pth.dirname(pth.dirname(pth.realpath(__file__)))
nb_path = pth.join(src_path, 'sagenb')
trans_path = pth.join(nb_path, 'translations')
nb_pot_path = pth.join(nb_path, 'message.pot')

LANGS = os.listdir(trans_path)
LANGS.sort()

def lang_path(lang_id):
    return pth.join(trans_path, lang_id, 'LC_MESSAGES', 'messages.po')

def restore(file_path):
    backup_path = '{}~'.format(file_path)
    if pth.isfile(backup_path):
        shutil.copyfile(backup_path, file_path)

def clean(file_path):
    backup_path = '{}~'.format(file_path)
    if pth.isfile(backup_path):
        os.remove(backup_path)


class Pot(object):
    def __init__(self, charset=CHARSET):
        self.catalog = Catalog(charset=charset)
        self.path = None
        
    def extract(self, dirnames, base_path=src_path, method_map=METHOD_MAP,
                options_map=OPTIONS_MAP, keywords=KEYWORDS, charset=CHARSET,
                **kwargs):
        self.catalog = Catalog(charset=charset)
        for dirname in dirnames:
            real_path = pth.normpath(pth.join(base_path, dirname))
            if not pth.isdir(real_path):
                raise IOError('{} is not a directory'.format(real_path))

            extracted = extract_from_dir(real_path, method_map=method_map,
                                         options_map=options_map,
                                         keywords=keywords, **kwargs)
            for filename, lineno, message, comments, context in extracted:
                file_path = pth.normpath(pth.join(dirname, filename))
                self.catalog.add(message, None, [(file_path, lineno)],
                                 auto_comments=comments, context=context)

    def from_file(self, file_path, **kwargs):
        with open(file_path, 'rt') as f:
            self.catalog = read_po(f, **kwargs)
        self.path = file_path

    def to_file(self, file_path=None, backup=True, warn=False, width=WIDTH,
                sort_by_file=SORT_BY_FILE, **kwargs):
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
                if message.fuzzy:
                    fuzzy += 1
                if not message.string:
                    untrans += 1
            if fuzzy:
                logging.warning('There are {} fuzzy messages in {}.\n'.format(
                    fuzzy, self.path))
            if untrans:
                logging.warning('There are {} untranslated messages'
                'in {}.\n'.format(untrans, self.path))
            if obsolete:
                logging.warning('There are {} obsolete  messages'
                'in {}.\n'.format(obsolete, self.path))
        else:
            logging.basicConfig(level=logging.INFO)

        with open(file_path, 'wb') as f:
            write_po(f, self.catalog, width=width,
                        sort_by_file=sort_by_file, **kwargs)

    def update(self, template_po, *args, **kwargs):
        self.catalog.update(template_po.catalog, *args, **kwargs)




class Po(Pot):
    def __init__(self, lang_id, trans_path=trans_path):
        self.lang_id = lang_id
        self.path = lang_path(self.lang_id)
        self.from_file(self.path)
        self.name = Locale(*lang_id.split('_')).display_name

    def compile(self, file_path=None, backup=True, **kwargs):
        if file_path is None:
            file_path = self.path
        if file_path is not None:
            file_path = file_path[:-2] + 'mo'
        if pth.isfile(file_path) and backup:
            shutil.copy(file_path, '{}~'.format(file_path))
        with open(file_path, 'wb') as f:
            write_mo(f, self.catalog, **kwargs)


class LangsAction(argparse.Action):
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

class TranslationFrontend(argparse.ArgumentParser):
    def __init__(self, **kwargs):
        super(self.__class__, self).__init__(
            formatter_class=argparse.RawTextHelpFormatter,
            description='Localization management for sage notebook', **kwargs)
        self.add_argument(
            'action',
            choices=['update', 'restore', 'clean', 'compile'],
            metavar = 'ACTION',
            help='Actions: update - updates pot and po files\n'
                 '         restore - restores pot and po files backed-up\n'
                 '         clean - deletes backup pot and po files\n'
                 '         compile - generate mo files from po files\n',
            )
        self.add_argument(
            '--pot',
            dest='pot',
            action='store_true',
            help='Perform ACTION on sage message.pot file\n'
                 'This option has no efect on compile Action',
            )
        self.add_argument(
            '--langs', '--nolangs',
            dest='langs',
            action=LangsAction,
            nargs='*',
            choices=LANGS,
            default=set(),
            metavar=('xx_XX', 'yy_YY'),
            help='--langs - add all available lang\n'
                 '--langs xx_XX ... - add selected langs\n'
                 '--nolangs - remove all langs processing\n'
                 '--nolangs xx_XX ... - remove selected langs\n'
                 'By default no lenguage is processed.\n'
                 'Examples:\n'
                 '  To process only spanish and french:\n'
                 '    translations.py ACTION --langs es_ES fr_FR\n'
                 '  To process all but spanish and french:\n'
                 '    translations.py ACTION --langs --nolangs es_ES fr_FR\n'
            )
        self.add_argument(
            '--nobackup',
            dest='backup',
            action='store_false',
            help='Deactivate backup of pot and po files\n',
            )
        self.add_argument(
            '--nowarn',
            dest='warn',
            action='store_false',
            help='Prevent warning about fuzzy, untranslated and\n'
                 'obsolete messages to be printed',
            )
        self.add_argument(
            '--fuzzy',
            dest='nofuzzy',
            action='store_false',
            help='Fuzzy matching of message IDs\n',
            )
        self.args = self.parse_args()
        
    def __call__(self):
        getattr(self, self.args.action)()

    def update(self):
        pot_new = Pot()
        pot_new.extract(['sagenb'])
        if self.args.pot:
            pot_old = Pot()
            pot_old.from_file(nb_pot_path)
            pot_old.update(pot_new, no_fuzzy_matching=self.args.nofuzzy)
            pot_old.to_file(backup=self.args.backup, warn=self.args.warn)
        for lang in self.args.langs.difference(('en_US',)):
            po = Po(lang)
            po.update(pot_new, no_fuzzy_matching=self.args.nofuzzy)
            po.to_file(backup=self.args.backup, warn=self.args.warn)

    def restore(self):
        if self.args.pot:
            restore(nb_pot_path)
        for lang in self.args.langs:
            po_path = lang_path(lang)
            mo_path = po_path[:-2] + 'mo'
            restore(po_path)
            restore(mo_path)

    def clean(self):
        if self.args.pot:
            clean(nb_pot_path)
        for lang in self.args.langs:
            po_path = lang_path(lang)
            mo_path = po_path[:-2] + 'mo'
            clean(po_path)
            clean(mo_path)

    def compile(self):
        for lang in self.args.langs:
            po = Po(lang)
            po.compile()


if __name__ == '__main__':
    frontend = TranslationFrontend()
    frontend()





