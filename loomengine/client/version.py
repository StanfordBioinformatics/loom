#!/usr/bin/env python
    
import argparse
from loomengine.client.common import get_server_url
import loomengine.utils.version
from loomengine.utils.objecthandler import ObjectHandler


class Version:
    """Shows the Loom version."""

    def __init__(self, args=None):

        # Args may be given as an input argument for testing purposes.
        # Otherwise get them from the parser.
        if args is None:
            args = self._get_args()
        self.args = args
        self.objecthandler = self._get_objecthandler()

    def _get_objecthandler(self):
        master_url = get_server_url()
        return  ObjectHandler(master_url)

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
        server_version = self.get_server_version()
        if not server_version:
            server_version = 'unavailable'
        print "client version: %s" % loomengine.utils.version.version()
        print "server version: %s" % server_version

    def get_server_version(self):
        return self.objecthandler.get_version()

if __name__=='__main__':
    response = Version().run()
