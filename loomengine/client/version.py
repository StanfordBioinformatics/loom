#!/usr/bin/env python
    
import argparse
from loomengine.client.common import get_server_url, has_server_file, is_server_running
import loomengine.utils.version
from loomengine.utils.connection import Connection


class Version:
    """Shows the Loom version."""

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
        return parser

    def run(self):
        if not has_server_file():
            server_version = 'not connected'
        else:
            url = get_server_url()
            if not is_server_running(url=url):
                server_version = 'no response'
            else:
                connection = Connection(url)
                server_version = connection.get_version()

        print "client version: %s" % loomengine.utils.version.version()
        print "server version: %s" % server_version


if __name__=='__main__':
    response = Version().run()
