#!/usr/bin/env python

import argparse
import glob
import os
from loomengine.client.common import verify_server_is_running, get_server_url, \
    verify_has_connection_settings, parse_as_json_or_yaml
from loomengine.utils.filemanager import FileManager
from loomengine.utils.connection import Connection


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
            '--note',
            metavar='SOURCE_NOTE',
            help='Description of the data source. '\
            'Give enough detail for traceability.')
        return parser

    def run(self):
        files_imported = self.filemanager.import_from_patterns(
            self.args.files,
            self.args.note
        )
        if len(files_imported) == 0:
            raise Exception('No files found')


class TemplateImporter(AbstractImporter):

    @classmethod
    def get_parser(cls, parser):
        parser.add_argument(
            'template',
            metavar='TEMPLATE_FILE', help='Template to be imported, in YAML or JSON format.')
        parser.add_argument(
            '--note',
            metavar='SOURCE_NOTE',
            help='Description of the template source. '\
            'Give enough detail for traceability.')
        return parser

    def run(self):
        return self.import_template(self.args.template,
                                    self.args.note,
                                    self.filemanager,
                                    self.connection)
    @classmethod
    def import_template(cls, template_file, note, filemanager, connection):
        print 'Importing template from "%s".' % filemanager.normalize_url(
            template_file)
        (template, source_url) = cls._get_template(template_file, filemanager)
        template.update({
            'template_import': {
                'note': note,
                'source_url': source_url,
            }})
            
        template_from_server = connection.post_template(template)
        print 'Imported template "%s@%s".' % (
            template_from_server['name'],
            template_from_server['uuid'])
        return template_from_server

    @classmethod
    def _get_template(cls, template_file, filemanager):
        try:
            (template_text, source_url) = filemanager.read_file(template_file)
        except Exception as e:
            raise SystemExit('ERROR! Unable to read file "%s". %s'
                            % (template_file, str(e)))
        template = parse_as_json_or_yaml(template_text)
        try:
            template.update
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

        hidden_file_subparser = subparsers.add_parser('files')
        FileImporter.get_parser(hidden_file_subparser)
        hidden_file_subparser.set_defaults(SubSubcommandClass=FileImporter)

        template_subparser = subparsers.add_parser('template', help='import a template')
        TemplateImporter.get_parser(template_subparser)
        template_subparser.set_defaults(SubSubcommandClass=TemplateImporter)

        hidden_template_subparser = subparsers.add_parser('templates')
        TemplateImporter.get_parser(hidden_template_subparser)
        hidden_template_subparser.set_defaults(SubSubcommandClass=TemplateImporter)

        return parser

    def run(self):
        self.args.SubSubcommandClass(self.args).run()


if __name__=='__main__':
    response = Importer().run()
