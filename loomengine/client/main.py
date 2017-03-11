#!/usr/bin/env python

import argparse
import os
import sys

from loomengine.client.common import get_server_url, has_connection_settings, is_server_running
import loomengine.utils.version
from loomengine.utils.connection import Connection

if __name__ == "__main__" and __package__ is None:
    rootdir=os.path.abspath('../..')
    sys.path.append(rootdir)

from loomengine.client import browser
from loomengine.client import exporter
from loomengine.client import importer
from loomengine.client import run
from loomengine.client import server
from loomengine.client import show
from loomengine.client import test_runner
from loomengine.client import version


class Version(argparse.Action):
    def __call__(self, parser, namespace, values, option_string):
        if not has_connection_settings():
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
        exit(0)

class Main(object):

    def __init__(self, args=None):
        if args is None:
            parser = self.get_parser()
            args = parser.parse_args()
        self.args = args

    def get_parser(cls):
        parser = argparse.ArgumentParser('loom')
        parser.add_argument('--version', '-v', nargs=0, action=Version)

        subparsers = parser.add_subparsers(help='select a subcommand')

        run_subparser = subparsers.add_parser('run', help='run a template')
        run.TemplateRunner.get_parser(run_subparser)
        run_subparser.set_defaults(SubcommandClass=run.TemplateRunner)

        server_subparser = subparsers.add_parser('server', help='manage the Loom server')
        server.get_parser(server_subparser)
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

        browser_subparser = subparsers.add_parser('browser', help='launch the Loom web browser')
        browser.Browser.get_parser(browser_subparser)
        browser_subparser.set_defaults(SubcommandClass=browser.Browser)

        test_subparser = subparsers.add_parser('test', help='run tests')
        test_runner.get_parser(test_subparser)
        test_subparser.set_defaults(SubcommandClass=test_runner.TestRunner)

        return parser

    def run(self):
        return self.args.SubcommandClass(self.args).run()

# pip entrypoint requires a function with no arguments 
def main():
    return Main().run()

if __name__=='__main__':
    main()
