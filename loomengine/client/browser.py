#!/usr/bin/env python
import webbrowser
import os
import sys

if __name__ == "__main__" and __package__ is None:
    rootdir=os.path.abspath('../..')
    sys.path.append(rootdir)

import argparse
    
from loomengine.client import server
from loomengine.client.common import get_server_url, verify_server_is_running
from loomengine.client.exceptions import *


class Browser:
    """Sets up and executes commands under "browser"" on the main parser.
    """

    def __init__(self, args=None):

        # Args may be given as an input argument for testing purposes.
        # Otherwise get them from the parser.
        if args is None:
            args = self._get_args()
        self.args = args
        self.master_url = get_server_url()
        verify_server_is_running()
        
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
        try:
            webbrowser.open(self.master_url)
        except webbrowser.Error:
            print 'Unable to open browser. To open the Loom webserver, please launch a browser and go to this url: %s' % self.master_url


if __name__=='__main__':
    response = Browser().run()
