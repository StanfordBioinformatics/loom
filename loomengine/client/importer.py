#!/usr/bin/env python

import argparse
import glob
import os
import sys

from loomengine.client.common import verify_server_is_running, get_server_url, \
    verify_has_connection_settings, parse_as_json_or_yaml
from loomengine.client.file_client import FileImport
from loomengine.client.template import TemplateImport
from loomengine.utils.filemanager import FileManager
from loomengine.utils.connection import Connection
from loomengine.utils.exceptions import DuplicateFileError, DuplicateTemplateError


class Importer:
    """Configures and executes subcommands under "import" on the main parser.
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

        # If called from main, a subparser should be provided.
        # Otherwise we create a top-level parser here.
        if parser is None:
            parser = argparse.ArgumentParser(__file__)

        subparsers = parser.add_subparsers(
            help='select a data type to import', metavar='{file,template}')

        file_subparser = subparsers.add_parser(
            'file', help='import a file or list files')
                                               
        FileImport.get_parser(file_subparser)
        file_subparser.set_defaults(SubSubcommandClass=FileImport)

        hidden_file_subparser = subparsers.add_parser('files')
        FileImport.get_parser(hidden_file_subparser)
        hidden_file_subparser.set_defaults(SubSubcommandClass=FileImport)

        template_subparser = subparsers.add_parser(
            'template', help='import a template')

        TemplateImport.get_parser(template_subparser)
        template_subparser.set_defaults(SubSubcommandClass=TemplateImport)

        hidden_template_subparser = subparsers.add_parser('templates')
        TemplateImport.get_parser(hidden_template_subparser)
        hidden_template_subparser.set_defaults(SubSubcommandClass=TemplateImport)

        return parser

    def run(self):
        import warnings
        LOOM_IMPORT_DEPRECATED = '\n THE "LOOM IMPORT" COMMAND IS DEPRECATED and '\
                                 'will be removed in a future release. Use "loom '\
                                 'file import" and "loom template import" instead.'
        warnings.warn(LOOM_IMPORT_DEPRECATED)
        self.args.SubSubcommandClass(self.args).run()


if __name__=='__main__':
    response = Importer().run()
