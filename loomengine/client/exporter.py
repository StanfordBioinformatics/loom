#!/usr/bin/env python

import argparse
import json
import os
import sys
import yaml
from loomengine.client.common import get_server_url, verify_server_is_running, \
    verify_has_connection_settings
from loomengine.client.file_client import FileExport
from loomengine.client.template import TemplateExport
from loomengine.utils.filemanager import FileManager
from loomengine.utils.connection import Connection


class Exporter:
    """Sets up and executes commands under "download" on the main parser.
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
        if parser is None:
            parser = argparse.ArgumentParser(__file__)

        subparsers = parser.add_subparsers(help='select a data type to download', metavar='{file,template}')

        file_subparser = subparsers.add_parser('file', help='download a file or an array of files')
        FileExport.get_parser(file_subparser)
        file_subparser.set_defaults(SubSubcommandClass=FileExport)

        hidden_file_subparser = subparsers.add_parser('files')
        FileExport.get_parser(hidden_file_subparser)
        hidden_file_subparser.set_defaults(SubSubcommandClass=FileExport)

        template_subparser = subparsers.add_parser('template', help='download a template')
        TemplateExport.get_parser(template_subparser)
        template_subparser.set_defaults(SubSubcommandClass=TemplateExport)

        hidden_template_subparser = subparsers.add_parser('templates')
        TemplateExport.get_parser(hidden_template_subparser)
        hidden_template_subparser.set_defaults(SubSubcommandClass=TemplateExport)

        return parser

    def run(self):
        import warnings
        LOOM_EXPORT_DEPRECATED = '\n THE "LOOM EXPORT" COMMAND IS DEPRECATED and '\
                                 'will be removed in a future release. Use "loom '\
                                 'file export" and "loom template export" instead.'
        warnings.warn(LOOM_EXPORT_DEPRECATED)
        self.args.SubSubcommandClass(self.args).run()


if __name__=='__main__':
    response = Exporter().run()
