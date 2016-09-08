#!/usr/bin/env python

import argparse
import json
import os
import sys
import yaml
from loomengine.client.common import get_server_url
from loomengine.client.exceptions import *
from loomengine.utils.filehandler import FileHandler
from loomengine.utils.objecthandler import ObjectHandler
from loomengine.utils.helper import get_console_logger


class AbstractExporter(object):
    """Common functions for the various subcommands under 'export'
    """
    
    def __init__(self, args, logger=None):
        """Common init tasks for all Export classes
        """
        self.args = args

        if logger is None:
            logger = get_console_logger()
        self.logger = logger
        
        master_url = get_server_url_for_client()
        self.objecthandler = ObjectHandler(master_url)
        self.filehandler = FileHandler(master_url, logger=self.logger)


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
        self.filehandler.export_files(
            self.args.file_ids,
            destination_url=self.args.destination
        )


class WorkflowExporter(AbstractExporter):

    @classmethod
    def get_parser(cls, parser):
        parser.add_argument(
            'workflow_id',
            metavar='WORKFLOW_ID', help='Workflow to be downloaded.')
        parser.add_argument(
            '--destination',
            metavar='DESTINATION',
            help='Destination filename or directory')
        parser.add_argument(
            '--format',
            choices=['json', 'yaml'],
            default='json',
            help='Data format for downloaded workflow')
        return parser

    def run(self):
        workflow = self.objecthandler.get_abstract_workflow_index(query_string=self.args.workflow_id, min=1, max=1)[0]
        destination_url = self._get_destination_url(workflow)
        self._save_workflow(workflow, destination_url)

    def _get_destination_url(self, workflow):
        default_name = '%s.%s' % (workflow['name'], self.args.format)
        return self.filehandler.get_destination_file_url(self.args.destination, default_name)

    def _save_workflow(self, workflow, destination):
        self.logger.info('Exporting workflow %s@%s to %s...' % (workflow.get('name'), workflow.get('_id'), destination))
        if self.args.format == 'json':
            workflow_text = json.dumps(workflow)
        elif self.args.format == 'yaml':
            workflow_text = yaml.safe_dump(workflow)
        else:
            raise Exception('Invalid format type %s' % self.args.format)
        self.filehandler.write_to_file(destination, workflow_text)
        self.logger.info('...finished exporting workflow')

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

        subparsers = parser.add_subparsers(help='select a data type to download', metavar='{file,workflow}')

        file_subparser = subparsers.add_parser('file', help='download a file or an array of files')
        FileExporter.get_parser(file_subparser)
        file_subparser.set_defaults(SubSubcommandClass=FileExporter)

        hidden_file_subparser = subparsers.add_parser('files')
        FileExporter.get_parser(hidden_file_subparser)
        hidden_file_subparser.set_defaults(SubSubcommandClass=FileExporter)

        workflow_subparser = subparsers.add_parser('workflow', help='download a workflow')
        WorkflowExporter.get_parser(workflow_subparser)
        workflow_subparser.set_defaults(SubSubcommandClass=WorkflowExporter)

        hidden_workflow_subparser = subparsers.add_parser('workflows')
        WorkflowExporter.get_parser(hidden_workflow_subparser)
        hidden_workflow_subparser.set_defaults(SubSubcommandClass=WorkflowExporter)

        return parser

    def run(self):
        self.args.SubSubcommandClass(self.args).run()


if __name__=='__main__':
    response = Exporter().run()
