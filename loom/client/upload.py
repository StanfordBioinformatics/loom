#!/usr/bin/env python
import argparse
import glob
import os
import re
import sys

if __name__ == "__main__" and __package__ is None:
    rootdir=os.path.abspath('../..')
    sys.path.append(rootdir)
    
from loom.client import settings_manager
from loom.client.common import get_settings_manager, \
    add_settings_options_to_parser
from loom.client.exceptions import *
from loom.common import filehandler


class AbstractUploader(object):
    """Common functions for the various subcommands under 'upload'
    """
    
    def __init__(self, args):
        """Common init tasks for all Uploader classes
        """
        self.args = args
        self.settings_manager = get_settings_manager(self.args)
        self.master_url = self.settings_manager.get_server_url_for_client()

    @classmethod
    def get_parser(cls, parser):
        parser = add_settings_options_to_parser(parser)
        return parser


class FileUploader(AbstractUploader):

    @classmethod
    def get_parser(cls, parser):
        parser = super(FileUploader, cls).get_parser(parser)
        parser.add_argument(
            'file_paths',
            metavar='FILE_PATHS', help='File(s) to be uploaded. '\
            'Comma-separated list with no spaces. Wildcards are allowed. '\
            'Quotes may be needed to protect wildcards.')
        parser.add_argument(
            '--rename',
            metavar='NEW_FILE_NAMES',
            help='Rename the uploaded file(s). Comma-separated list with no '\
            'spaces. Must be equal in length to the number of files matched '\
            'by FILE_PATHS.')
        parser.add_argument(
            '--source_record',
            metavar='SOURCE_RECORD',
            help='Text file containing a complete description of the data '\
            'source. Provide enough detail to ensure traceability.')
        return parser

    def run(self):
        self._get_local_paths()
        self._get_file_names()
        self._get_filehandler()
        self._get_source_record_text()
        self._upload_files()

    def _get_local_paths(self):
        """Get all local file paths that match glob patterns
        given by the user.
        """
        self.local_paths = []
        for pattern in self.args.file_paths.strip(',').split(','):
            self.local_paths.extend(glob.glob(
                os.path.expanduser(pattern)))
        self._validate_local_paths()

    def _validate_local_paths(self):
        """Verify that paths are for existing files
        """
        for path in self.local_paths:
            if not os.path.isfile(path):
                raise NotAFileError(
                    '"%s" is not a file. Only files can be uploaded.' % path)
        if len(self.local_paths) == 0:
            raise NoFilesFoundError("No files found for upload")

    def _get_file_names(self):
        """If --rename is used, process the list of file names. Otherwise use
        current file names.
        """
        self.file_names = []
        if self.args.rename is None:
            for path in self.local_paths:
                self.file_names.append(os.path.basename(path))
        else:
            self.file_names = self.args.rename.strip(',').split(',')
        self._validate_file_names()

    def _validate_file_names(self):
        for name in self.file_names:
            if not re.match(r'^[0-9a-zA-Z_\.]+[0-9a-zA-Z_\-\.]*$', name):
                raise InvalidFileNameError(
                    'The file name "%s" is not valid. Filenames must contain '\
                    ' only alphanumerics, ".", "-", or "_", and may not start '\
                    'with "-".' % name)
        if not len(self.file_names) == len(self.local_paths):
            raise WrongRenameLengthError(
                '%s file names were given, but %s files were selected '\
                'for upload.' % (len(self.file_names), len(self.local_paths)))

    def _get_filehandler(self):
        self.filehandler = filehandler.FileHandler(self.master_url)

    def _get_source_record_text(self):
        if self.args.source_record is not None:
            source_record_file = self.args.source_record
            if not os.path.isfile(source_record_file):
                raise NotAFileError(
                    '"%s" is not a file. A source record must be a text file.' \
                    % source_record_file)
            with open(source_record_file) as f:
                self.source_record_text = f.read()
        else:
            self.source_record_text = self._prompt_for_source_record_text()

    def _prompt_for_source_record_text(self):
        return raw_input(
            'Enter a complete description of the data source. '\
            'Provide enough detail to ensure traceability.\n> '
        )

    def _upload_files(self):
        self.filehandler.upload_files_from_local_paths(
            self.local_paths,
            file_names=self.file_names,
            source_record=self.source_record_text
        )


class Uploader:
    """Sets up and executes commands under "upload" on the main parser.
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

        subparsers = parser.add_subparsers(help='select a data type to upload')
        file_subparser = subparsers.add_parser('file', help='upload a file or an array of files')
        FileUploader.get_parser(file_subparser)
        file_subparser.set_defaults(SubSubcommandClass=FileUploader)

        return parser

    def run(self):
        self.args.SubSubcommandClass(self.args).run()


if __name__=='__main__':
    response = Uploader().run()
