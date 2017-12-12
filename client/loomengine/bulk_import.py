#!/usr/bin/env python
import os
import sys

if __name__ == "__main__" and __package__ is None:
    rootdir=os.path.abspath('../..')
    sys.path.append(rootdir)

import argparse
    
from loomengine import server
from loomengine.common import verify_has_connection_settings, get_server_url, \
    verify_server_is_running, get_token
from loomengine.exceptions import *
from loomengine_utils.connection import Connection
from loomengine_utils.import_manager import ImportManager


class BulkImport(object):

    def __init__(self, args=None):

        # Args may be given as an input argument for testing purposes.
        # Otherwise get them from the parser.
        if args is None:
            args = self._get_args()
        self.args = args
        verify_has_connection_settings()
        server_url = get_server_url()
        verify_server_is_running(url=server_url)
        token = get_token()
        self.connection = Connection(server_url, token=token)
        self.import_manager = ImportManager(
            connection=self.connection)

    def _get_args(self):
        parser = self.get_parser()
        return parser.parse_args()

    @classmethod
    def get_parser(cls, parser=None):
        # If called from main, use the subparser provided.
        # Otherwise create a top-level parser here.
        if parser is None:
            parser = argparse.ArgumentParser(__file__)
        parser.add_argument(
            'directory', metavar='DIRECTORY',
            help='directory to import data from'
        )
        parser.add_argument(
            '-k', '--link-files', action='store_true',
            default=False,
            help='link to existing files instead of copying to storage '\
            'managed by Loom')
        parser.add_argument(
            '-r', '--retry', action='store_true',
            default=False,
            help='allow retries if there is a failure')
        return parser

    def run(self):
        self.import_manager.bulk_import(
            self.args.directory,
            link_files=self.args.link_files,
            retry=self.args.retry)


if __name__=='__main__':
    response = BulkImport().run()
