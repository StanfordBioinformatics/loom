#!/usr/bin/env python

import argparse
import os
import sys

if __name__ == "__main__" and __package__ is None:
    rootdir=os.path.abspath('../..')
    sys.path.append(rootdir)

from loom.client import browser
from loom.client import config
from loom.client import exporter
from loom.client import importer
from loom.client import run
from loom.client import server
from loom.client import show
from loom.client import test_runner
from loom.client import version


class Main(object):

    def __init__(self, args=None):
        if args is None:
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

        import_subparser = subparsers.add_parser('import', help='import files or other data to the Loom server')
        importer.Importer.get_parser(import_subparser)
        import_subparser.set_defaults(SubcommandClass=importer.Importer)

        export_subparser = subparsers.add_parser('export', help='export files or other data from the Loom server')
        exporter.Exporter.get_parser(export_subparser)
        export_subparser.set_defaults(SubcommandClass=exporter.Exporter)

        show_subparser = subparsers.add_parser('show', help='query and show data objects from the Loom server')
        show.Show.get_parser(show_subparser)
        show_subparser.set_defaults(SubcommandClass=show.Show)

        config_subparser = subparsers.add_parser('config', help='configure the Loom server')
        config.Config.get_parser(config_subparser)
        config_subparser.set_defaults(SubcommandClass=config.Config)

        browser_subparser = subparsers.add_parser('browser', help='launch the Loom web browser')
        browser.Browser.get_parser(browser_subparser)
        browser_subparser.set_defaults(SubcommandClass=browser.Browser)

        test_subparser = subparsers.add_parser('test', help='run all unit tests')
        test_runner.TestRunner.get_parser(test_subparser)
        test_subparser.set_defaults(SubcommandClass=test_runner.TestRunner)

        version_subparser = subparsers.add_parser('version', help='display current version of Loom')
        version.Version.get_parser(version_subparser)
        version_subparser.set_defaults(SubcommandClass=version.Version)

        return parser

    def run(self):
        self.args.SubcommandClass(self.args).run()

# pip entrypoint requires a function with no arguments 
def main():
    Main().run()

if __name__=='__main__':
    main()
