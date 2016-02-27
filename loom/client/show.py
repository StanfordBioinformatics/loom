#!/usr/bin/env python

import argparse
import json
import os
import sys
import yaml
    
from loom.client import settings_manager
from loom.client.common import get_settings_manager
from loom.client.common import add_settings_options_to_parser
from loom.client.exceptions import *
from loom.common import filehandler, objecthandler


class AbstractShowHandler(object):
    """Common functions for the various subcommands under 'show'
    """
    
    def __init__(self, args):
        """Common init tasks for all Show classes
        """
        self.args = args
        self.settings_manager = get_settings_manager(self.args)
        self.master_url = self.settings_manager.get_server_url_for_client()

    @classmethod
    def get_parser(cls, parser):
        parser = add_settings_options_to_parser(parser)
        return parser


class ShowFileHandler(AbstractShowHandler):

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
        parser = super(ShowFileHandler, cls).get_parser(parser)
        return parser

    def run(self):
        self._get_objecthandler()
        self._get_files()
        self._show_files()

    def _get_objecthandler(self):
        self.objecthandler = objecthandler.ObjectHandler(self.master_url)

    def _get_files(self):
        self.files = self.objecthandler.get_file_data_object_index(self.args.file_id)

    def _show_files(self):
        for file in self.files:
            print self._render_file(file)

    def _render_file(self, file):
        file_identifier = file['file_name'] + '@' + file['_id']
        if self.args.detail:
            text = '---------------------------------------\n'
            text += 'File: %s\n' % file_identifier
            text += ' - Hash: %s\n' % (file['file_contents']['hash_function'] + '$' + file['file_contents']['hash_value'])
            source_records = self.objecthandler.get_source_records_by_file(file['_id'])
            for source_record in source_records:
                text += ' - Source Record: ' + source_record['source_description'] + '\n'
        else:
            text = 'File: %s' % file_identifier
        return text


class ShowWorkflowHandler(AbstractShowHandler):

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
        parser = super(ShowWorkflowHandler, cls).get_parser(parser)
        return parser

    def run(self):
        self._get_objecthandler()
        self._get_workflows()
        self._show_workflows()

    def _get_objecthandler(self):
        self.objecthandler = objecthandler.ObjectHandler(self.master_url)

    def _get_workflows(self):
        self.workflows = self.objecthandler.get_workflow_index(self.args.workflow_id)

    def _show_workflows(self):
        for workflow in self.workflows:
            print self._render_workflow(workflow)

    def _render_workflow(self, workflow):
        workflow_identifier = workflow['workflow_name'] + '@' + workflow['_id']
        if self.args.detail:
            text = '---------------------------------------\n'
            text += 'Workflow: %s\n' % workflow_identifier
            text += ' - Contents: %s' % (workflow)
        else:
            text = 'Workflow: %s' % workflow_identifier
        return text


class ShowWorkflowRunHandler(AbstractShowHandler):

    @classmethod
    def get_parser(cls, parser):
        parser.add_argument(
            'workflow_run_id',
            nargs='?',
            metavar='WORKFLOW_RUN_IDENTIFIER',
            help='Name or ID of workflow run(s) to show.')
        parser.add_argument(
            '--detail',
            action='store_true',
            help='Show detailed view of workflow runs')
        parser = super(ShowWorkflowRunHandler, cls).get_parser(parser)
        return parser

    def run(self):
        self._get_objecthandler()
        self._get_workflow_runs()
        self._show_workflow_runs()

    def _get_objecthandler(self):
        self.objecthandler = objecthandler.ObjectHandler(self.master_url)

    def _get_workflow_runs(self):
        self.workflow_runs = self.objecthandler.get_workflow_run_index(self.args.workflow_run_id)

    def _show_workflow_runs(self):
        for workflow_run in self.workflow_runs:
            print self._render_workflow_run(workflow_run)

    def _render_workflow_run(self, workflow_run):
        workflow_run_identifier = workflow_run['workflow']['workflow_name'] + '@' + workflow_run['_id']
        if self.args.detail:
            text = '---------------------------------------\n'
            text += 'Workflow Run: %s\n' % workflow_run_identifier
            text += ' - Contents: %s' % (workflow_run)
        else:
            text = 'Workflow Run: %s' % workflow_run_identifier
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

        subparsers = parser.add_subparsers(help='select the type of object to  show')

        file_subparser = subparsers.add_parser('file', help='show files')
        ShowFileHandler.get_parser(file_subparser)
        file_subparser.set_defaults(SubSubcommandClass=ShowFileHandler)

        workflow_subparser = subparsers.add_parser('workflow', help='show workflows')
        ShowWorkflowHandler.get_parser(workflow_subparser)
        workflow_subparser.set_defaults(SubSubcommandClass=ShowWorkflowHandler)

        workflow_run_subparser = subparsers.add_parser('run', help='show workflow runs')
        ShowWorkflowRunHandler.get_parser(workflow_run_subparser)
        workflow_run_subparser.set_defaults(SubSubcommandClass=ShowWorkflowRunHandler)

        return parser

    def run(self):
        self.args.SubSubcommandClass(self.args).run()


if __name__=='__main__':
    response = Show().run()
