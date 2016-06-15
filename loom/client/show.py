#!/usr/bin/env python

import argparse
import json
import os
import sys
import yaml
from loom.client.common import get_server_url

from loom.client.exceptions import *
from loom.common.objecthandler import ObjectHandler


class AbstractShow(object):
    """Common functions for the various subcommands under 'show'
    """

    def __init__(self, args):
        """Common init tasks for all Show classes
        """
        self.args = args
        self.master_url = get_server_url()

    @classmethod
    def get_parser(cls, parser):
        return parser


class ShowFile(AbstractShow):

    @classmethod
    def get_parser(cls, parser):
        parser.add_argument(
            'file_id',
            nargs='?',
            metavar='FILE_IDENTIFIER',
            help='Name or ID of file(s) to show.')
        parser.add_argument(
            '--detail',
            action='store_true',
            help='Show detailed view of files')
        parser = super(ShowFile, cls).get_parser(parser)
        return parser

    def run(self):
        self._get_files()
        self._show_files()

    def _get_files(self):
        self.files = self.objecthandler.get_file_data_object_index(self.args.file_id, raise_for_status=False)

    def _show_files(self):
        for file_data_object in self.files:
            print self._render_file(file_data_object)

    def _render_file(self, file_data_object):
        file_identifier = '%s@%s' % (file_data_object['file_content']['filename'], file_data_object['_id'])
        if self.args.detail:
            text = '---------------------------------------\n'
            text += 'File: %s\n' % file_identifier
            text += '  - Hash: %s$%s\n' % (file_data_object['file_content']['unnamed_file_content']['hash_function'],
                                           file_data_object['file_content']['unnamed_file_content']['hash_value'])
            file_imports = self.objecthandler.get_file_imports_by_file(file_data_object['_id'], raise_for_status=False)
            for file_import in file_imports:
                text += '    - Imported: %s from %s\n' % (file_import['datetime_created'], file_import['source_url'])
                if file_import.get('note'):
                    text += '      With note: %s\n' % file_import['note']
        else:
            text = 'File: %s' % file_identifier
        return text


class ShowWorkflow(AbstractShow):

    @classmethod
    def get_parser(cls, parser):
        parser.add_argument(
            'workflow_id',
            nargs='?',
            metavar='WORKFLOW_IDENTIFIER',
            help='Name or ID of workflow(s) to show.')
        parser.add_argument(
            '--detail',
            action='store_true',
            help='Show detailed view of workflows')
        parser = super(ShowWorkflow, cls).get_parser(parser)
        return parser

    def run(self):
        self._get_workflows()
        self._show_workflows()

    def _get_workflows(self):
        self.workflows = self.objecthandler.get_abstract_workflow_index(self.args.workflow_id, raise_for_status=False)

    def _show_workflows(self):
        for workflow in self.workflows:
            print self._render_workflow(workflow)

    def _render_workflow(self, workflow):
        workflow_identifier = '%s@%s' % (workflow['name'], workflow['_id'])
        if self.args.detail:
            text = '---------------------------------------\n'
            text += 'Workflow: %s\n' % workflow_identifier
            if workflow.get('inputs'):
                text += '  - Inputs\n'
                for input in workflow['inputs']:
                    text += '    - %s\n' % input['channel']
            if workflow.get('outputs'):
                text += '  - Outputs\n'
                for output in workflow['outputs']:
                    text += '    - %s\n' % output['channel']
            if workflow.get('steps'):
                text += '  - Steps\n'
                for step in workflow['steps']:
                    text += '    - %s@%s\n' % (step['name'], step['_id'])
            if workflow.get('command'):
                text += '  - Command: %s\n' % workflow['command']

        else:
            text = 'Workflow: %s' % workflow_identifier
        return text


class ShowRun(AbstractShow):

    @classmethod
    def get_parser(cls, parser):
        parser.add_argument(
            'run_id',
            nargs='?',
            metavar='RUN_IDENTIFIER',
            help='Name or ID of run(s) to show.')
        parser.add_argument(
            '--detail',
            action='store_true',
            help='Show detailed view of runs')
        parser = super(ShowRun, cls).get_parser(parser)
        return parser

    def run(self):
        runs = self._get_runs()
        self._show_runs(runs)

    def _get_runs(self):
        return self.objecthandler.get_run_request_index(self.args.run_id, raise_for_status=False)

    def _show_runs(self, runs):
        for run in runs:
            print self._render_run(run)

    def _render_run(self, run):
        run_identifier = '%s@%s' % (run['workflow']['name'], run['_id'])
        if self.args.detail:
            text = '---------------------------------------\n'
            text += 'Run: %s\n' % run_identifier
            text += '  - Submitted: %s\n' % run['datetime_created']
        else:
            text = 'Run: %s' % run_identifier
        return text


class Show:
    """Sets up and executes commands under "show" on the main parser
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

        subparsers = parser.add_subparsers(help='select the type of object to  show', metavar='{file,workflow,run}')

        file_subparser = subparsers.add_parser('file', help='show files')
        ShowFile.get_parser(file_subparser)
        file_subparser.set_defaults(SubSubcommandClass=ShowFile)

        hidden_file_subparser = subparsers.add_parser('files')
        ShowFile.get_parser(hidden_file_subparser)
        hidden_file_subparser.set_defaults(SubSubcommandClass=ShowFile)

        workflow_subparser = subparsers.add_parser('workflow', help='show workflows')
        ShowWorkflow.get_parser(workflow_subparser)
        workflow_subparser.set_defaults(SubSubcommandClass=ShowWorkflow)

        hidden_workflow_subparser = subparsers.add_parser('workflows')
        ShowWorkflow.get_parser(hidden_workflow_subparser)
        hidden_workflow_subparser.set_defaults(SubSubcommandClass=ShowWorkflow)

        run_subparser = subparsers.add_parser('run', help='show runs')
        ShowRun.get_parser(run_subparser)
        run_subparser.set_defaults(SubSubcommandClass=ShowRun)

        hidden_run_subparser = subparsers.add_parser('runs')
        ShowRun.get_parser(hidden_run_subparser)
        hidden_run_subparser.set_defaults(SubSubcommandClass=ShowRun)

        return parser

    def run(self):
        self.args.SubSubcommandClass(self.args).run()


if __name__=='__main__':
    response = Show().run()
