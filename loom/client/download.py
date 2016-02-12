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
            metavar='NEW_FILE_NAMES',
            help='Rename the downloaded file(s). For a file array, use a '\
            'Comma-separated list with no spaces. Must be equal in length '\
            'to the number of files in the array')
        parser.add_argument(
            '--directory',
            metavar='DIRECTORY',
            help='Destination directory for downloads')
        return parser

    def run(self):
        self._get_file_id()
        self._get_renames()
        self._get_filehandler()
        self._download_files()

    def _get_filehandler(self):
        self.filehandler = filehandler.FileHandler(self.master_url)

    def _get_file_id(self):
        self.file_id = self.args.file_id

    def _get_renames(self):
        self.renames = None
        if self.args.rename is not None:
            relative_path_renames = []
            for name in self.args.rename.strip(',').split(','):
                relative_path_renames.append(os.path.expanduser(name))
            self.renames = self._prepend_directory(relative_path_renames)
            self._validate_renames()

    def _prepend_directory(self, renames):
        if self.args.directory is None:
            return renames
        absolute_path_renames = []
        for name in renames:
            if name.startswith('/'):
                absolute_path_renames.append(
                    os.path.join(self.args.directory, name)
                )
            else:
                absolute_path_renames.append(name)
        return absolute_path_renames

    def _validate_renames(self):
        for name in self.renames:
            dirname = os.path.dirname(name)
            if dirname:
                if not os.path.isdir(dirname):
                    raise DestinationDirectoryNotFoundError(
                        'No directory found for download to %s' % name)

    def _download_files(self):
        self.filehandler.download_file_or_array(
            self.file_id,
            local_paths=self.renames
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
