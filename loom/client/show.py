#!/usr/bin/env python
import argparse
import json
import os
import sys
import yaml

if __name__ == "__main__" and __package__ is None:
    rootdir=os.path.abspath('../..')
    sys.path.append(rootdir)
    
from loom.client import settings_manager
from loom.client.common import get_settings_manager
from loom.client.common import add_settings_options_to_parser
from loom.client.exceptions import *
from loom.common import filehandler, objecthandler
from loom.common.helper import get_stdout_logger


class AbstractShowHandler(object):
    """Common functions for the various subcommands under 'show'
    """
    
    def __init__(self, args):
        """Common init tasks for all Show classes
        """
        self.args = args
        self.settings_manager = get_settings_manager(self.args)
        self.master_url = self.settings_manager.get_server_url_for_client()

    @classmethod
    def get_parser(cls, parser):
        parser = add_settings_options_to_parser(parser)
        return parser


class ShowFileHandler(AbstractShowHandler):

    @classmethod
    def get_parser(cls, parser):
        parser.add_argument(
            'file_id',
            nargs='?',
            metavar='FILE_IDENTIFIER',
            help='Name or ID of file(s) to show.')
        parser.add_argument(
            '--detail',
            action='store_true',
            help='Show detailed view of files')
        parser = super(ShowFileHandler, cls).get_parser(parser)
        return parser

    def run(self):
        self._get_objecthandler()
        self._get_files()
        self._show_files()

    def _get_objecthandler(self):
        self.objecthandler = objecthandler.ObjectHandler(self.master_url)

    def _get_files(self):
        self.files = self.objecthandler.get_file_data_object_index(self.args.file_id)

    def _show_files(self):
        for file in self.files:
            print self._render_file(file)

    def _render_file(self, file):
        file_identifier = file['file_name'] + '@' + file['_id']
        if self.args.detail:
            text = '---------------------------------------\n'
            text += 'File: %s\n' % file_identifier
            text += ' - Hash: %s\n' % (file['file_contents']['hash_function'] + '$' + file['file_contents']['hash_value'])
            source_records = self.objecthandler.get_source_records_by_file(file['_id'])
            for source_record in source_records:
                text += ' - Source Record: ' + source_record['source_description'] + '\n'
        else:
            text = 'File: %s' % file_identifier
        return text
    

class Show:
    """Sets up and executes commands under "show" on the main parser
    """

    def __init__(self, args=None):

        # Args may be given as an input argument for testing purposes.
        # Otherwise get them from the parser.
        if args is None:
            args = self._get_args()
        self.args = args

    def _get_args(self):
        parser = self.get_parser()
        return parser.parse_args()

    @classmethod
    def get_parser(cls, parser=None):

        # If called from main, use the subparser provided.
        # Otherwise create a top-level parser here.
        if parser == None:
            parser = argparse.ArgumentParser(__file__)

        subparsers = parser.add_subparsers(help='select the type of object to  show')

        show_subparser = subparsers.add_parser('file', help='show a file or an array of files')
        ShowFileHandler.get_parser(show_subparser)
        show_subparser.set_defaults(SubSubcommandClass=ShowFileHandler)

        return parser

    def run(self):
        self.args.SubSubcommandClass(self.args).run()


if __name__=='__main__':
    response = Show().run()
