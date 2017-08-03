#!/usr/bin/env python

import argparse
from datetime import datetime
import dateutil.parser
from dateutil import tz
import json
import os
import sys
import yaml
from loomengine.client.common import get_server_url, verify_server_is_running, \
    verify_has_connection_settings
from loomengine.client.file_client import FileList
from loomengine.client.template import TemplateList
from loomengine.client.run import RunList

from loomengine.client.exceptions import *
from loomengine.utils.connection import Connection


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
        if parser is None:
            parser = argparse.ArgumentParser(__file__)

        subparsers = parser.add_subparsers(help='select the type of object to  show', metavar='{file,template,run}')

        file_subparser = subparsers.add_parser('file', help='show files')
        FileList.get_parser(file_subparser)
        file_subparser.set_defaults(SubSubcommandClass=FileList)

        hidden_file_subparser = subparsers.add_parser('files')
        FileList.get_parser(hidden_file_subparser)
        hidden_file_subparser.set_defaults(SubSubcommandClass=FileList)

        template_subparser = subparsers.add_parser('template', help='show templates')
        TemplateList.get_parser(template_subparser)
        template_subparser.set_defaults(SubSubcommandClass=TemplateList)

        hidden_template_subparser = subparsers.add_parser('templates')
        TemplateList.get_parser(hidden_template_subparser)
        hidden_template_subparser.set_defaults(SubSubcommandClass=TemplateList)

        run_subparser = subparsers.add_parser('run', help='show runs')
        RunList.get_parser(run_subparser)
        run_subparser.set_defaults(SubSubcommandClass=RunList)

        hidden_run_subparser = subparsers.add_parser('runs')
        RunList.get_parser(hidden_run_subparser)
        hidden_run_subparser.set_defaults(SubSubcommandClass=RunList)

        return parser

    def run(self):
        import warnings
        LOOM_SHOW_DEPRECATED = '\n THE "LOOM SHOW" COMMAND IS DEPRECATED and '\
                               'will be removed in a future release. Use "loom '\
                               'file list", "loom template list", and "loom run '\
                               'list" instead.'
        warnings.warn(LOOM_SHOW_DEPRECATED)

        self.args.SubSubcommandClass(self.args).run()


if __name__=='__main__':
    response = Show().run()
