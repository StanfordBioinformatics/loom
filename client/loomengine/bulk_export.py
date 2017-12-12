#!/usr/bin/env python
import os
import sys

if __name__ == "__main__" and __package__ is None:
    rootdir=os.path.abspath('../..')
    sys.path.append(rootdir)

import argparse
    
from loomengine import server
from loomengine.common import verify_has_connection_settings, get_server_url, \
    verify_server_is_running
from loomengine.exceptions import *


class BulkExport(object):

    def __init__(self, args=None):

        # Args may be given as an input argument for testing purposes.
        # Otherwise get them from the parser.
        if args is None:
            args = self._get_args()
        self.args = args
        verify_has_connection_settings()
        self.server_url = get_server_url()
        verify_server_is_running(url=self.server_url)

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
            '-d', '--destination',
            metavar='DESTINATION',
            help='destination directory')
        parser.add_argument(
            '-k', '--link-files', action='store_true',
            default=False,
            help='do not export files, just metadata with link to original file')
        parser.add_argument(
            '-r', '--retry', action='store_true',
            default=False,
            help='allow retries if there is a failure')
        return parser

    def run(self):
        pass

if __name__=='__main__':
    response = BulkExport().run()
