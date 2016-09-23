#!/usr/bin/env python

import argparse
import glob
import os
from loomengine.client.common import get_server_url
from loomengine.client.common import parse_as_json_or_yaml
from loomengine.client.exceptions import *
from loomengine.utils import exceptions as common_exceptions
from loomengine.utils.filemanager import FileManager, Source
from loomengine.utils.helper import get_console_logger
from loomengine.utils.connection import Connection


class AbstractImporter(object):
    """Common functions for the various subcommands under 'loom import'
    """
    
    def __init__(self, args, logger=None):
        """Common init tasks for all Importer classes
        """

        self.args = args

        master_url = get_server_url()
        
        # Log to console unless another logger is given
        # (e.g. by unittests to prevent terminal output)
        if logger is None:
            logger = get_console_logger(name=__file__)
        self.logger = logger

        self.filemanager = FileManager(master_url, logger=self.logger)
        self.connection = Connection(master_url)


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
        return self.filemanager.import_from_patterns(
            self.args.files,
            self.args.note
        )


class WorkflowImporter(AbstractImporter):

    @classmethod
    def get_parser(cls, parser):
        parser.add_argument(
            'workflow',
            metavar='WORKFLOW_FILE', help='Workflow to be imported, in YAML or JSON format.')
        parser.add_argument(
            '--note',
            metavar='SOURCE_NOTE',
            help='Description of the workflow source. '\
            'Give enough detail for traceability.')
        return parser

    def run(self):
        return self.import_workflow(self.args.workflow, self.args.note, self.filemanager, self.connection, self.logger)

    @classmethod
    def import_workflow(cls, workflow_file, note, filemanager, connection, logger):
        logger.info('Importing workflow from %s...' % filemanager.normalize_url(workflow_file))
        (workflow, source_url) = cls._get_workflow(workflow_file, filemanager)
        workflow.update({
            'workflow_import': {
                'note': note,
                'source_url': source_url,
            }})
        workflow_from_server = connection.post_abstract_workflow(workflow)
        logger.info('   imported workflow %s@%s' % \
            (workflow_from_server['name'],
             workflow_from_server['id'],
            ))        
        return workflow_from_server

    @classmethod
    def _get_workflow(cls, workflow_file, filemanager):
        (workflow_text, source_url) = filemanager.read_file(workflow_file)
        workflow = parse_as_json_or_yaml(workflow_text)
        return workflow, source_url


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

        subparsers = parser.add_subparsers(help='select a data type to import', metavar='{file,workflow}')

        file_subparser = subparsers.add_parser('file', help='import a file or list files')
        FileImporter.get_parser(file_subparser)
        file_subparser.set_defaults(SubSubcommandClass=FileImporter)

        hidden_file_subparser = subparsers.add_parser('files')
        FileImporter.get_parser(hidden_file_subparser)
        hidden_file_subparser.set_defaults(SubSubcommandClass=FileImporter)

        workflow_subparser = subparsers.add_parser('workflow', help='import a workflow')
        WorkflowImporter.get_parser(workflow_subparser)
        workflow_subparser.set_defaults(SubSubcommandClass=WorkflowImporter)

        hidden_workflow_subparser = subparsers.add_parser('workflows')
        WorkflowImporter.get_parser(hidden_workflow_subparser)
        hidden_workflow_subparser.set_defaults(SubSubcommandClass=WorkflowImporter)

        return parser

    def run(self):
        self.args.SubSubcommandClass(self.args).run()


if __name__=='__main__':
    response = Importer().run()
