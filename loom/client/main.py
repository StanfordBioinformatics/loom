#!/usr/bin/env python

import argparse
import os
import sys

if __name__ == "__main__" and __package__ is None:
    rootdir=os.path.abspath('../..')
    sys.path.append(rootdir)

from loom.client import config
from loom.client import download
from loom.client import run
from loom.client import server
from loom.client import upload
from loom.client import test_runner


class Main(object):

    def __init__(self, args=None):
        if args == None:
            parser = self.get_parser()
            args = parser.parse_args()
        self.args = args

    def get_parser(cls):
        parser = argparse.ArgumentParser('loom')
        subparsers = parser.add_subparsers(help='select a subcommand')

        run_subparser = subparsers.add_parser('run', help='run a workflow')
        run.WorkflowRunner.get_parser(run_subparser)
        run_subparser.set_defaults(SubcommandClass=run.WorkflowRunner)

        server_subparser = subparsers.add_parser('server', help='manage the Loom server')
        server.ServerControls.get_parser(server_subparser)
        server_subparser.set_defaults(SubcommandClass=server.ServerControls)

        upload_subparser = subparsers.add_parser('upload', help='upload files or other data to the Loom server')
        upload.Uploader.get_parser(upload_subparser)
        upload_subparser.set_defaults(SubcommandClass=upload.Uploader)

        download_subparser = subparsers.add_parser('download', help='download files or other data from the Loom server')
        download.Downloader.get_parser(download_subparser)
        download_subparser.set_defaults(SubcommandClass=download.Downloader)
        
        config_subparser = subparsers.add_parser('config', help='configure the Loom server')
        config.Config.get_parser(config_subparser)
        config_subparser.set_defaults(SubcommandClass=config.Config)

        test_subparser = subparsers.add_parser('test', help='run all unit tests')
        test_runner.TestRunner.get_parser(test_subparser)
        test_subparser.set_defaults(SubcommandClass=test_runner.TestRunner)

        return parser

    def run(self):
        self.args.SubcommandClass(self.args).run()

# pip entrypoint requires a function with no arguments 
def main():
    Main().run()

if __name__=='__main__':
    main()
