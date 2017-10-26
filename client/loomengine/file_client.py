#!/usr/bin/env python

import argparse
import glob
import os
import sys

from loomengine import _render_time
from loomengine.common import verify_server_is_running, get_server_url, \
    verify_has_connection_settings, parse_as_json_or_yaml, get_token
from loomengine.file_tag import FileTag
from loomengine.file_label import FileLabel
from loomengine_utils.filemanager import FileManager
from loomengine_utils.connection import Connection


class FileImport(object):

    def __init__(self, args):
        """Common init tasks for all Importer classes
        """
        self.args = args
        verify_has_connection_settings()
        server_url = get_server_url()
        verify_server_is_running(url=server_url)
        token = get_token()
        self.filemanager = FileManager(server_url, token=token)
        self.connection = Connection(server_url, token=token)

    @classmethod
    def get_parser(cls, parser):
        parser.add_argument(
            'files',
            metavar='FILE', nargs='+', help='file path or Google Storage URL '\
            'of file(s) to be imported. Wildcards are allowed')
        parser.add_argument(
            '-c', '--comments',
            metavar='COMMENTS',
            help='comments. '\
            'Give enough detail for traceability.')
        parser.add_argument('-d', '--force-duplicates', action='store_true',
                            default=False,
                            help='force upload even if another file with '\
                            'the same name and md5 exists')
        parser.add_argument('-o', '--original-copy', action='store_true',
                            default=False,
                            help='use existing copy instead of copying to storage '\
                            'managed by Loom')
        parser.add_argument('-r', '--retry', action='store_true',
                            default=False,
                            help='allow retries if there is a failure '\
                            'connecting to storage')
        parser.add_argument('-t', '--tag', metavar='TAG', action='append',
                            help='tag the file when it is created')
        parser.add_argument('-l', '--label', metavar='LABEL', action='append',
                            help='label the file when it is created')
            
        return parser

    def run(self):
        files_imported = self.filemanager.import_from_patterns(
            self.args.files,
            self.args.comments,
            original_copy=self.args.original_copy,
            force_duplicates=self.args.force_duplicates,
            retry=self.args.retry
        )
        if len(files_imported) == 0:
            raise SystemExit('ERROR! Did not find any files matching "%s"'
                             % '", "'.join(self.args.files))
        self._apply_tags(files_imported)
        self._apply_labels(files_imported)
        return files_imported

    def _apply_tags(self, files_imported):
        if not self.args.tag:
            return
        if len(files_imported) > 1:
            print ('WARNING! No tags were applied, because tags '\
                   'must be unique but multiple files were imported.')
            return
        else:
            for tagname in self.args.tag:
                tag_data = {'tag': tagname}
                tag = self.connection.post_data_tag(
                    files_imported[0].get('uuid'), tag_data)
                print 'File "%s@%s" has been tagged as "%s"' % \
                    (files_imported[0]['value'].get('filename'),
                     files_imported[0].get('uuid'),
                     tag.get('tag'))

    def _apply_labels(self, files_imported):
        if not self.args.label:
            return
        for labelname in self.args.label:
            for file_imported in files_imported:
                label_data = {'label': labelname}
                label = self.connection.post_data_label(
                    file_imported.get('uuid'), label_data)
                print 'File "%s@%s" has been labeled as "%s"' % \
                    (file_imported['value'].get('filename'),
                     file_imported.get('uuid'),
                     label.get('label'))


class FileExport(object):

    def __init__(self, args):
        self.args = args
        verify_has_connection_settings()
        server_url = get_server_url()
        verify_server_is_running()
        token = get_token()
        self.connection = Connection(server_url, token=token)
        self.filemanager = FileManager(server_url, token=token)

    @classmethod
    def get_parser(cls, parser):
        parser.add_argument(
            'file_ids',
            nargs='+',
            metavar='FILE_ID',
            help='file or list of files to be exported')
        parser.add_argument(
            '--destination',
            metavar='DESTINATION',
            help='destination filename or directory')
        parser.add_argument(
            '-r', '--retry', action='store_true',
            default=False,
            help='allow retries if there is a failure '\
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
        self.connection = Connection(server_url, token=get_token())

    @classmethod
    def get_parser(cls, parser):
        parser.add_argument(
            'file_id',
            nargs='?',
            metavar='FILE_IDENTIFIER',
            help='Name or ID of file(s) to list.')
        parser.add_argument(
            '-d', '--detail',
            action='store_true',
            help='Show detailed view of files')
        parser.add_argument(
            '-t', '--type',
            choices=['imported', 'result', 'log', 'all'],
            default='imported',
            help='List only files of the specified type. '\
            '(ignored when FILE_IDENTIFIER is given)')
        parser.add_argument('-l', '--label', metavar='LABEL', action='append',
                            help='Filter by label')

        return parser

    def run(self):
        if self.args.file_id:
            source_type=None
        else:
            source_type=self.args.type
        offset=0
        limit=10
        while True:
            data = self.connection.get_data_object_index_with_limit(
                limit=limit, offset=offset,
                query_string=self.args.file_id, source_type=source_type,
                labels=self.args.label, type='file')
            if offset == 0:
                print '[showing %s files]' % data.get('count')
            self._list_files(data['results'])
            if data.get('next'):
                offset += limit
            else:
                break

    def _list_files(self, files):
        for file_data_object in files:
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
                        _render_time(file_data_object['datetime_created'])
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


class FileClient(object):
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

        subparsers = parser.add_subparsers()

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

        tag_subparser = subparsers.add_parser('tag', help='manage file tags')
        FileTag.get_parser(tag_subparser)
        tag_subparser.set_defaults(SubSubcommandClass=FileTag)

        label_subparser = subparsers.add_parser('label', help='manage file labels')
        FileLabel.get_parser(label_subparser)
        label_subparser.set_defaults(SubSubcommandClass=FileLabel)

        return parser

    def run(self):
        self.args.SubSubcommandClass(self.args).run()


if __name__=='__main__':
    response = FileClient().run()
