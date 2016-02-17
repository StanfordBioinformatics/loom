#!/usr/bin/env python
import argparse
import os
import sys

if __name__ == "__main__" and __package__ is None:
    rootdir=os.path.abspath('../..')
    sys.path.append(rootdir)
    
from loom.client import settings_manager
from loom.client.common import get_settings_manager, \
    add_settings_options_to_parser
from loom.client.exceptions import *
from loom.common import filehandler
from loom.common.helper import get_stdout_logger


class AbstractDownloader(object):
    """Common functions for the various subcommands under 'download'
    """
    
    def __init__(self, args):
        """Common init tasks for all Download classes
        """
        self.args = args
        self.settings_manager = get_settings_manager(self.args)
        self.master_url = self.settings_manager.get_server_url_for_client()

    @classmethod
    def get_parser(cls, parser):
        parser = add_settings_options_to_parser(parser)
        return parser


class FileDownloader(AbstractDownloader):

    @classmethod
    def get_parser(cls, parser):
        parser = super(FileDownloader, cls).get_parser(parser)
        parser.add_argument(
            'file_id',
            metavar='FILE_ID', help='File or file array to be downloaded.')
        parser.add_argument(
            '--rename',
            nargs='+',
            metavar='NEW_FILE_NAMES',
            help='Rename the downloaded file(s). For a file array, the number '\
            'of names must be equal to the number of files in the array')
        parser.add_argument(
            '--directory',
            metavar='DIRECTORY',
            help='Destination directory for downloads')
        return parser

    def run(self):
        terminal = get_stdout_logger()
        self._get_file_id()
        self._get_renames()
        self._get_filehandler()
        self._download_files(terminal)

    def _get_filehandler(self):
        self.filehandler = filehandler.FileHandler(self.master_url)

    def _get_file_id(self):
        self.file_id = self.args.file_id

    def _get_renames(self):
        self.renames = None
        if self.args.rename is not None:
            self.renames = self.args.rename

    def _download_files(self, terminal):
        self.filehandler.download_file_or_array(
            self.file_id,
            local_names=self.renames,
            target_directory=self.args.directory,
            logger=terminal
        )


class Downloader:
    """Sets up and executes commands under "download" on the main parser.
    """

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
        if parser == None:
            parser = argparse.ArgumentParser(__file__)

        subparsers = parser.add_subparsers(help='select a data type to download')
        file_subparser = subparsers.add_parser('file', help='download a file or an array of files')
        FileDownloader.get_parser(file_subparser)
        file_subparser.set_defaults(SubSubcommandClass=FileDownloader)

        return parser

    def run(self):
        self.args.SubSubcommandClass(self.args).run()


if __name__=='__main__':
    response = Downloader().run()