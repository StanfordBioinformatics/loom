#!/usr/bin/env python

import argparse
import json
import os
import sys
import yaml
from loomengine.client.common import get_server_url, verify_server_is_running, \
    verify_has_connection_settings
from loomengine.utils.filemanager import FileManager
from loomengine.utils.connection import Connection


class AbstractExporter(object):
    """Common functions for the various subcommands under 'export'
    """
    
    def __init__(self, args):
        """Common init tasks for all Export classes
        """
        self.args = args
        verify_has_connection_settings()
        server_url = get_server_url()
        verify_server_is_running()
        self.connection = Connection(server_url)
        self.filemanager = FileManager(server_url)


class FileExporter(AbstractExporter):

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
        return parser

    def run(self):
        self.filemanager.export_files(
            self.args.file_ids,
            destination_url=self.args.destination
        )


class TemplateExporter(AbstractExporter):

    @classmethod
    def get_parser(cls, parser):
        parser.add_argument(
            'template_id',
            metavar='TEMPLATE_ID', help='Template to be downloaded.')
        parser.add_argument(
            '--destination',
            metavar='DESTINATION',
            help='Destination filename or directory')
        parser.add_argument(
            '--format',
            choices=['json', 'yaml'],
            default='yaml',
            help='Data format for downloaded template')
        return parser

    def run(self):
        template = self.connection.get_template_index(query_string=self.args.template_id, min=1, max=1)[0]
        destination_url = self._get_destination_url(template)
        self._save_template(template, destination_url)

    def _get_destination_url(self, template):
        default_name = '%s.%s' % (template['name'], self.args.format)
        return self.filemanager.get_destination_file_url(self.args.destination, default_name)

    def _save_template(self, template, destination):
        print 'Exporting template %s@%s to %s...' % (template.get('name'), template.get('_id'), destination)
        if self.args.format == 'json':
            template_text = json.dumps(template, indent=4, separators=(',', ': '))
        elif self.args.format == 'yaml':
            template_text = yaml.safe_dump(template, default_flow_style=False)
        else:
            raise Exception('Invalid format type %s' % self.args.format)
        self.filemanager.write_to_file(destination, template_text)
        print '...finished exporting template'

class Exporter:
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
        if parser is None:
            parser = argparse.ArgumentParser(__file__)

        subparsers = parser.add_subparsers(help='select a data type to download', metavar='{file,template}')

        file_subparser = subparsers.add_parser('file', help='download a file or an array of files')
        FileExporter.get_parser(file_subparser)
        file_subparser.set_defaults(SubSubcommandClass=FileExporter)

        hidden_file_subparser = subparsers.add_parser('files')
        FileExporter.get_parser(hidden_file_subparser)
        hidden_file_subparser.set_defaults(SubSubcommandClass=FileExporter)

        template_subparser = subparsers.add_parser('template', help='download a template')
        TemplateExporter.get_parser(template_subparser)
        template_subparser.set_defaults(SubSubcommandClass=TemplateExporter)

        hidden_template_subparser = subparsers.add_parser('templates')
        TemplateExporter.get_parser(hidden_template_subparser)
        hidden_template_subparser.set_defaults(SubSubcommandClass=TemplateExporter)

        return parser

    def run(self):
        self.args.SubSubcommandClass(self.args).run()


if __name__=='__main__':
    response = Exporter().run()
