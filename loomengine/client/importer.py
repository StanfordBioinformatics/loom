#!/usr/bin/env python

import argparse
import glob
import os
from loomengine.client.common import verify_server_is_running, get_server_url, \
    verify_has_connection_settings, parse_as_json_or_yaml
from loomengine.utils.filemanager import FileManager
from loomengine.utils.connection import Connection
from loomengine.utils.exceptions import DuplicateFileError, DuplicateTemplateError

class AbstractImporter(object):
    """Common functions for the various subcommands under 'loom import'
    """
    
    def __init__(self, args):
        """Common init tasks for all Importer classes
        """

        self.args = args
        verify_has_connection_settings()
        server_url = get_server_url()
        verify_server_is_running(url=server_url)
        self.filemanager = FileManager(server_url)
        self.connection = Connection(server_url)


class FileImporter(AbstractImporter):

    @classmethod
    def get_parser(cls, parser):
        parser.add_argument(
            'files',
            metavar='FILE', nargs='+', help='File path or Google Storage URL of file(s) to be imported. Wildcards are allowed.')
        parser.add_argument(
            '--comment',
            metavar='COMMENTS',
            help='Comments. '\
            'Give enough detail for traceability.')
        return parser

    def run(self):
        try:
            files_imported = self.filemanager.import_from_patterns(
                self.args.files,
                self.args.comment,
                force_duplicates=self.args.force_duplicates,
            )
        except DuplicateFileError as e:
            raise SystemExit(e.message)
        if len(files_imported) == 0:
            raise SystemExit('ERROR! Did not find any files matching "%s"'
                             % '", "'.join(self.args.files))


class TemplateImporter(AbstractImporter):

    @classmethod
    def get_parser(cls, parser):
        parser.add_argument(
            'template',
            metavar='TEMPLATE_FILE', help='Template to be imported, in YAML or JSON format.')
        parser.add_argument(
            '--comments',
            metavar='COMMENTS',
            help='Comments. '\
            'Give enough detail for traceability.')
        return parser

    def run(self):
        return self.import_template(self.args.template,
                                    self.args.comments,
                                    self.filemanager,
                                    self.connection,
                                    self.args.force_duplicates)

    @classmethod
    def import_template(cls, template_file, comments,
                        filemanager, connection, force_duplicates=False):
        print 'Importing template from "%s".' % filemanager.normalize_url(
            template_file)
        (template, source_url) = cls._get_template(template_file, filemanager)
        if not force_duplicates:
            try:
                filemanager.verify_no_template_duplicates(template)
            except DuplicateTemplateError as e:
                raise SystemExit(e.message)
        if comments:
            template.update({'import_comments': comments})
        if source_url:
            template.update({'imported_from_url': source_url})

        cls._warn_for_fixed_inputs(template)

        template_from_server = connection.post_template(template)
        print 'Imported template "%s@%s".' % (
            template_from_server['name'],
            template_from_server['uuid'])
        return template_from_server

    @classmethod
    def _warn_for_fixed_inputs(cls, template):
        if isinstance(template, (str, unicode)):
            return
        if template.get('fixed_inputs'):
            import warnings
            FIXED_INPUTS_DEPRECATED = '\nFIXED INPUTS ARE DEPRECATED and will '\
                                      'be removed in a future release. Use '\
                                      'a standard input with a "data" field instead.'
            warnings.warn(FIXED_INPUTS_DEPRECATED)
            return
        for step in template.get('steps', []):
            cls._warn_for_fixed_inputs(step)

    @classmethod
    def _get_template(cls, template_file, filemanager):
        md5 = filemanager.calculate_md5(template_file)
        try:
            (template_text, source_url) = filemanager.read_file(template_file)
        except Exception as e:
            raise SystemExit('ERROR! Unable to read file "%s". %s'
                            % (template_file, str(e)))
        template = parse_as_json_or_yaml(template_text)
        try:
            template.update({'md5': md5})
        except AttributeError:
            raise SystemExit(
                'ERROR! Template at "%s" could not be parsed into a dict.'
                % os.path.abspath(template_file))
        return template, source_url


class Importer:
    """Configures and executes subcommands under "import" on the main parser.
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

        subparsers = parser.add_subparsers(help='select a data type to import', metavar='{file,template}')

        file_subparser = subparsers.add_parser('file', help='import a file or list files')
        FileImporter.get_parser(file_subparser)
        file_subparser.set_defaults(SubSubcommandClass=FileImporter)
        file_subparser.add_argument('-d', '--force-duplicates', action='store_true',
                                    default=False,
                                    help='Force upload even if another file with '\
                                    'the same name and md5 exists')

        hidden_file_subparser = subparsers.add_parser('files')
        FileImporter.get_parser(hidden_file_subparser)
        hidden_file_subparser.set_defaults(SubSubcommandClass=FileImporter)
        hidden_file_subparser.add_argument('--force-duplicates', '-d',
                                           action='store_true', default=False)

        template_subparser = subparsers.add_parser('template', help='import a template')
        template_subparser.add_argument('-d', '--force-duplicates', action='store_true',
                                    default=False,
                                    help='Force upload even if another template with '\
                                    'the same name and md5 exists')

        TemplateImporter.get_parser(template_subparser)
        template_subparser.set_defaults(SubSubcommandClass=TemplateImporter)

        hidden_template_subparser = subparsers.add_parser('templates')
        TemplateImporter.get_parser(hidden_template_subparser)
        hidden_template_subparser.set_defaults(SubSubcommandClass=TemplateImporter)
        hidden_template_subparser.add_argument('--force-duplicates', '-d',
                                           action='store_true', default=False)

        return parser

    def run(self):
        self.args.SubSubcommandClass(self.args).run()


if __name__=='__main__':
    response = Importer().run()
