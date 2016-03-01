#!/usr/bin/env python
import webbrowser
import os
import sys

if __name__ == "__main__" and __package__ is None:
    rootdir=os.path.abspath('../..')
    sys.path.append(rootdir)

import argparse
    
from loom.client import settings_manager
from loom.client import server
from loom.client.common import get_settings_manager_from_parsed_args
from loom.client.common import add_settings_options_to_parser
from loom.client.exceptions import *
                

class Browser:
    """Sets up and executes commands under "browser"" on the main parser.
    """

    def __init__(self, args=None):

        # Args may be given as an input argument for testing purposes.
        # Otherwise get them from the parser.
        if args is None:
            args = self._get_args()
        self.args = args
        self.settings_manager = get_settings_manager_from_parsed_args(self.args)
        self.master_url = self.settings_manager.get_server_url_for_client()
        
    def _get_args(self):
        parser = self.get_parser()
        return parser.parse_args()

    @classmethod
    def get_parser(cls, parser=None):

        # If called from main, use the subparser provided.
        # Otherwise create a top-level parser here.
        if parser is None:
            parser = argparse.ArgumentParser(__file__)

        parser = add_settings_options_to_parser(parser)
        return parser

    def run(self):
        if server.is_server_running(master_url = self.master_url):
            try:
                webbrowser.open(self.master_url)
            except webbrowser.Error:
                print 'Unable to open browser. To open the Loom webserver, please launch a browser and go to this url: %s' % self.master_url
        else:
            print 'The Loom server is not currently running at %s. Try launching the web server with "loom server start".' % self.master_url


if __name__=='__main__':
    response = Browser().run()
