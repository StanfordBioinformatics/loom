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
from loom.client.common import \
    get_settings_manager, \
    add_settings_options_to_parser
from loom.client.exceptions import *
from loom.common import filehandler
from loom.common.helper import get_stdout_logger


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
            metavar='FILE_PATHS', nargs='+', help='File(s) to be uploaded.')
        parser.add_argument(
            '--rename',
            nargs='+',
            metavar='NEW_FILE_NAMES',
            help='Rename the uploaded file(s). The number of names must be '\
            'equal to the number of files matched by FILE_PATHS. (File names '\
            'do not have to be unique since files will be given a unique ID.)')
        parser.add_argument(
            '--source_record',
            metavar='SOURCE_RECORD',
            help='Text file containing a complete description of the data '\
            'source. Provide enough detail to ensure traceability.')
        parser.add_argument(
            '--skip_source_record',
            help='Do not prompt for source record.',
            action='store_true')
        return parser

    def run(self):
        terminal = get_stdout_logger()
        self._get_local_paths()
        self._get_file_names()
        self._get_filehandler()
        self._get_source_record_text()
        self._upload_files(terminal)

    def _get_local_paths(self):
        """Get all local file paths that match glob patterns
        given by the user.
        """
        paths = []
        for pattern in self.args.file_paths:
            paths.extend(glob.glob(
                os.path.expanduser(pattern)))
        self.local_paths = self._remove_dirs(paths)
        if len(self.local_paths) == 0:
            raise NoFilesFoundError("No files found for upload")
        
    def _remove_dirs(self, paths):
        """Verify that paths are for existing files
        """
        paths_minus_dirs = []
        for path in paths:
            if os.path.isdir(path):
                print "Skipping directory %s" % path
            else:
                paths_minus_dirs.append(path)
        return paths_minus_dirs

    def _get_file_names(self):
        """If --rename is used, process the list of file names. Otherwise use
        current file names.
        """
        self.file_names = []
        if self.args.rename is None:
            for path in self.local_paths:
                self.file_names.append(os.path.basename(path))
        else:
            self.file_names = self.args.rename
        self._validate_file_names()

    def _validate_file_names(self):
        for name in self.file_names:
            if not re.match(r'^[0-9a-zA-Z_\.]+[0-9a-zA-Z_\-\.]*$', name):
                raise InvalidFileNameError(
                    'The file name "%s" is not valid. Filenames must contain '\
                    ' only alphanumerics, ".", "-", or "_", and may not start '\
                    'with "-".' % name)

    def _get_filehandler(self):
        self.filehandler = filehandler.FileHandler(self.master_url)

    def _get_source_record_text(self):
        if self.args.skip_source_record:
            if self.args.source_record:
                raise ArgumentError(
                    'Setting both --source_record and --skip_source_record is not allowed')
            else:
                self.source_record_text = ''
                return
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
            'Provide enough detail to ensure traceability.\n'\
            'Press [enter] to skip.\n> '
        )

    def _upload_files(self, terminal):
        self.filehandler.upload_files_from_local_paths(
            self.local_paths,
            file_names=self.file_names,
            source_record=self.source_record_text,
            logger=terminal
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
