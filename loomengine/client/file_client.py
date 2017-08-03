#!/usr/bin/env python

import argparse
import glob
import os
import sys

from loomengine.client.common import verify_server_is_running, get_server_url, \
    verify_has_connection_settings, parse_as_json_or_yaml
from loomengine.client.file_tag import FileTag
from loomengine.client.file_label import FileLabel
from loomengine.utils.filemanager import FileManager
from loomengine.utils.connection import Connection
from loomengine.utils.exceptions import DuplicateFileError, DuplicateTemplateError


class FileImport(object):

    def __init__(self, args):
        """Common init tasks for all Importer classes
        """
        self.args = args
        verify_has_connection_settings()
        server_url = get_server_url()
        verify_server_is_running(url=server_url)
        self.filemanager = FileManager(server_url)
        self.connection = Connection(server_url)

    @classmethod
    def get_parser(cls, parser):
        parser.add_argument(
            'files',
            metavar='FILE', nargs='+', help='File path or Google Storage URL '\
            'of file(s) to be imported. Wildcards are allowed.')
        parser.add_argument(
            '-c', '--comments',
            metavar='COMMENTS',
            help='Comments. '\
            'Give enough detail for traceability.')
        parser.add_argument('-d', '--force-duplicates', action='store_true',
                            default=False,
                            help='Force upload even if another file with '\
                            'the same name and md5 exists')
        parser.add_argument('-o', '--original-copy', action='store_true',
                            default=False,
                            help='Use existing copy instead of copying to storage '\
                            'managed by Loom')
        parser.add_argument('-r', '--retry', action='store_true',
                            default=False,
                            help='Allow retries if there is a failure '\
                            'connecting to storage')
        parser.add_argument('-t', '--tag', metavar='TAG', action='append',
                            help='Tag the file when it is created')
        parser.add_argument('-l', '--label', metavar='LABEL', action='append',
                            help='Label the file when it is created')
            
        return parser

    def run(self):
        try:
            files_imported = self.filemanager.import_from_patterns(
                self.args.files,
                self.args.comments,
                original_copy=self.args.original_copy,
                force_duplicates=self.args.force_duplicates,
                retry=self.args.retry,
            )
        except DuplicateFileError as e:
            raise SystemExit(e.message)
        if len(files_imported) == 0:
            raise SystemExit('ERROR! Did not find any files matching "%s"'
                             % '", "'.join(self.args.files))
        self.apply_tags(files_imported)
        self.apply_labels(files_imported)
        return files_imported

    def _apply_tags(files_imported):
        if self.args.tag:
            if len(files_imported) > 1:
                print ('WARNING! No tags were applied, because tags '\
                       'must be unique but multiple files were imported.')
                return
            else:
                target = '@'+files_imported[0]['uuid']
                tag_data = {
                    'target': target,
                    'name': self.args.tag
                }
                tag = self.connection.post_tag(tag_data)
                print 'File "%s@%s" has been tagged as "%s"' % \
                    (tag['target']['value'].get('filename'),
                     tag['target'].get('uuid'),
                     tag.get('name'))

    def _apply_labels(files_imported):
        for label in self.args.label:
            for file_imported in files_imported:
                target = '@'+file_imported['uuid']
                label_data = {
                    'target': target,
                    'name': label
                }
                label = self.connection.post_label(label_data)
                print 'File "%s@%s" has been labeled as "%s"' % \
                    (label['target']['value'].get('filename'),
                     label['target'].get('uuid'),
                     label.get('name'))


class FileExport(object):

    def __init__(self, args):
        self.args = args
        verify_has_connection_settings()
        server_url = get_server_url()
        verify_server_is_running()
        self.connection = Connection(server_url)
        self.filemanager = FileManager(server_url)

    @classmethod
    def get_parser(cls, parser):
        parser.add_argument(
            'file_ids',
            nargs='+',
            metavar='FILE_ID',
            help='File or list of files to be exported')
        parser.add_argument(
            '--destination',
            metavar='DESTINATION',
            help='Destination filename or directory')
        parser.add_argument(
            '-r', '--retry', action='store_true',
            default=False,
            help='Allow retries if there is a failure '\
            'connecting to storage')
        return parser

    def run(self):
        self.filemanager.export_files(
            self.args.file_ids,
            destination_url=self.args.destination,
            retry=self.args.retry,
        )


class FileList(object):

    def __init__(self, args):
        self.args = args
        verify_has_connection_settings()
        server_url = get_server_url()
        verify_server_is_running(url=server_url)
        self.connection = Connection(server_url)

    @classmethod
    def get_parser(cls, parser):
        parser.add_argument(
            'file_id',
            nargs='?',
            metavar='FILE_IDENTIFIER',
            help='Name or ID of file(s) to list.')
        parser.add_argument(
            '--detail',
            action='store_true',
            help='Show detailed view of files')
        parser.add_argument(
            '--type',
            choices=['imported', 'result', 'log', 'all'],
            default='imported',
            help='List only files of the specified type. '\
            '(ignored when FILE_IDENTIFIER is given)')
        parser.add_argument('-l', '--label', metavar='LABEL', action='append',
                            help='Filter by label')

        return parser

    def run(self):
        self._get_files()
        self._list_files()

    def _get_files(self):
        if self.args.file_id:
            source_type=None
        else:
            source_type=self.args.type
        self.files = self.connection.get_data_object_index(
            query_string=self.args.file_id, source_type=source_type,
            labels=self.args.label, type='file')

    def _list_files(self):
        print '[showing %s files]' % len(self.files)
        for file_data_object in self.files:
            text = self._render_file(file_data_object)
            if text is not None:
                print text

    def _render_file(self, file_data_object):
        try:
            file_identifier = '%s@%s' % (
                file_data_object['value'].get('filename'), file_data_object['uuid'])
        except TypeError:
            file_identifier = '@%s' % file_data_object['uuid']
        if self.args.detail:
            text = '---------------------------------------\n'
            text += 'File: %s\n' % file_identifier
            try:
                text += '  - Imported: %s\n' % \
                        render_time(file_data_object['datetime_created'])
                text += '  - md5: %s\n' % file_data_object['value'].get('md5')
                if file_data_object['value'].get('imported_from_url'):
                    text += '  - Source URL: %s\n' % \
                            file_data_object['value'].get('imported_from_url')
                if file_data_object['value'].get('import_comments'):
                    text += '  - Import note: %s\n' % \
                            file_data_object['value']['import_comments']
            except TypeError:
                pass
        else:
            text = 'File: %s' % file_identifier
        return text


class FileClient:
    """Configures and executes subcommands under "file" on the main parser.
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

        # If called from main, a subparser should be provided.
        # Otherwise we create a top-level parser here.
        if parser is None:
            parser = argparse.ArgumentParser(__file__)

        subparsers = parser.add_subparsers(help='select an action')

        import_subparser = subparsers.add_parser(
            'import', help='import a file or list files')
        FileImport.get_parser(import_subparser)
        import_subparser.set_defaults(SubSubcommandClass=FileImport)

        export_subparser = subparsers.add_parser(
            'export', help='export a file or list files')
        FileExport.get_parser(export_subparser)
        export_subparser.set_defaults(SubSubcommandClass=FileExport)

        list_subparser = subparsers.add_parser(
            'list', help='list files')
        FileList.get_parser(list_subparser)
        list_subparser.set_defaults(SubSubcommandClass=FileList)

        tag_subparser = subparsers.add_parser('tag', help='manage tags')
        FileTag.get_parser(tag_subparser)
        tag_subparser.set_defaults(SubSubcommandClass=FileTag)

        label_subparser = subparsers.add_parser('label', help='manage labels')
        FileLabel.get_parser(label_subparser)
        label_subparser.set_defaults(SubSubcommandClass=FileLabel)

        return parser

    def run(self):
        self.args.SubSubcommandClass(self.args).run()


if __name__=='__main__':
    response = FileClient().run()
