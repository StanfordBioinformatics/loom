#!/usr/bin/env python
import os
import sys

if __name__ == "__main__" and __package__ is None:
    rootdir=os.path.abspath('../..')
    sys.path.append(rootdir)

import argparse
    
from loomengine.client import server
from loomengine.client.common import verify_has_connection_settings, get_server_url, \
    verify_server_is_running
from loomengine.client.exceptions import *
from loomengine.utils.connection import Connection


class Tag:
    """Sets up and executes commands under "tag"" on the main parser.
    """

    def __init__(self, args=None):

        # Args may be given as an input argument for testing purposes
        # or from the main parser.
        # Otherwise get them from the parser.
        if args is None:
            args = self._get_args()
        self.args = args
        verify_has_connection_settings()
        server_url = get_server_url()
        verify_server_is_running(url=server_url)
        self.connection = Connection(server_url)

    def _get_args(self):
        self.parser = self.get_parser()
        return self.parser.parse_args()

    @classmethod
    def get_parser(cls, parser=None):
        # If called from main, use the subparser provided.
        # Otherwise create a top-level parser here.
        if parser is None:
            parser = argparse.ArgumentParser(__file__)

        parser.add_argument(
            'target',
            metavar='TARGET', nargs='?',
            help='Identifier for target object to be tagged')
        parser.add_argument(
            'tag',
            metavar='TAG', nargs='?', help='Tag name to be creted')
        parser.add_argument(
            '-d', '--delete',
            metavar='TAG',
            help='Tag to be deleted')

        return parser

    def run(self):
        if self.args.target and self.args.tag:
            if self.args.delete:
                self.parser.print_usage()
                print "%s: error: argument -d/--delete: "\
                    "not allowed with TARGET and TAG arguments" % self.parser.prog
                sys.exit(1)
            else:
                tag_data = {
                    'target': self.args.target,
                    'name': self.args.tag
                }
                tag = self.connection.post_tag(tag_data)
                if tag.get('type') == 'file':
                    name = tag['target']['value'].get('filename')
                else:
                    name = tag['target'].get('name')
                print 'Target "%s@%s" of type "%s" has been tagged as "%s"' % \
                    (name,
                     tag['target'].get('uuid'),
                     tag.get('type'),
                     tag.get('name'))

if __name__=='__main__':
    response = Tag().run()
