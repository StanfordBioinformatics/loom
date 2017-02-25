#!/usr/bin/env python

import argparse
from datetime import datetime
import dateutil.parser
import json
import os
import sys
import yaml
from loomengine.client.common import get_server_url, verify_server_is_running, \
    verify_has_connection_settings

from loomengine.client.exceptions import *
from loomengine.utils.connection import Connection


DATETIME_FORMAT = '%b %d, %Y %-I:%M:%S %p'

class AbstractShow(object):
    """Common functions for the various subcommands under 'show'
    """

    def __init__(self, args):
        """Common init tasks for all Show classes
        """
        self.args = args
        verify_has_connection_settings()
        server_url = get_server_url()
        verify_server_is_running(url=server_url)
        self.connection = Connection(server_url)

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
        self.files = self.connection.get_file_data_object_index(
            self.args.file_id)

    def _show_files(self):
        print '[showing %s files]' % len(self.files)
        for file_data_object in self.files:
            text = self._render_file(file_data_object)
            if text is not None:
                print text

    def _render_file(self, file_data_object):
        try:
            file_identifier = '%s@%s' % (
                file_data_object['filename'], file_data_object['uuid'])
        except TypeError:
            file_identifier = '@%s' % file_data_object['uuid']
        if self.args.detail:
            text = '---------------------------------------\n'
            text += 'File: %s\n' % file_identifier
            try:
                text += '  - Imported: %s\n' % format(
                    dateutil.parser.parse(
                        file_data_object['datetime_created']), DATETIME_FORMAT)
                text += '  - md5: %s\n' % file_data_object['md5']
                if file_data_object.get('file_import'):
                    if file_data_object['file_import'].get('source_url'):
                        text += '  - Source URL: %s\n' % \
                                file_data_object['file_import']['source_url']
                        if file_data_object['file_import'].get('note'):
                            text += '  - Import note: %s\n' % \
                                    file_data_object['file_import']['note']
            except TypeError:
                pass
        else:
            text = 'File: %s' % file_identifier
        return text


class ShowTemplate(AbstractShow):

    @classmethod
    def get_parser(cls, parser):
        parser.add_argument(
            'template_id',
            nargs='?',
            metavar='TEMPLATE_IDENTIFIER',
            help='Name or ID of template(s) to show.')
        parser.add_argument(
            '--detail',
            action='store_true',
            help='Show detailed view of templates')
        parser = super(ShowTemplate, cls).get_parser(parser)
        return parser

    def run(self):
        self._get_templates()
        self._show_templates()

    def _get_templates(self):
        self.templates = self.connection.get_template_index(self.args.template_id)

    def _show_templates(self):
        print '[showing %s templates]' % len(self.templates)
        for template in self.templates:
            print self._render_template(template)

    def _render_template(self, template):
        template_identifier = '%s@%s' % (template['name'], template['uuid'])
        if self.args.detail:
            text = '---------------------------------------\n'
            text += 'Template: %s\n' % template_identifier
            text += '  - Imported: %s\n' % format(dateutil.parser.parse(template['datetime_created']), DATETIME_FORMAT)
            if template.get('inputs'):
                text += '  - Inputs\n'
                for input in template['inputs']:
                    text += '    - %s\n' % input['channel']
            if template.get('outputs'):
                text += '  - Outputs\n'
                for output in template['outputs']:
                    text += '    - %s\n' % output['channel']
            if template.get('steps'):
                text += '  - Steps\n'
                for step in template['steps']:
                    text += '    - %s@%s\n' % (step['name'], step['uuid'])
            if template.get('command'):
                text += '  - Command: %s\n' % template['command']
        else:
            text = 'Template: %s' % template_identifier
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
        return self.connection.get_run_index(self.args.run_id)

    def _show_runs(self, runs):
        print '[showing %s runs]' % len(runs)
        for run in runs:
            print self._render_run(run)

    def _render_run(self, run):
        run_identifier = '%s@%s' % (run['template']['name'], run['uuid'])
        if self.args.detail:
            text = '---------------------------------------\n'
            text += 'Run: %s\n' % run_identifier
            text += '  - Created: %s\n' % format(dateutil.parser.parse(run['datetime_created']), DATETIME_FORMAT)
            text += '  - Status: %s\n' % self._render_status(run)
            if run.get('steps'):
                text += '  - Steps:\n'
                for step in run['steps']:
                    text += '    - %s@%s \n' % (step['name'], step['uuid'])
        else:
            text = 'Run: %s' % run_identifier
        return text
    def _render_status(self, run):
        if run.get('status_is_failed'):
            return 'failed'
        elif run.get('status_is_killed'):
            return 'killed'
        elif run.get('status_is_running'):
            return 'running'
        elif run.get('status_is_finished'):
            return 'finished'
        else:
            return 'unknown'


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

        subparsers = parser.add_subparsers(help='select the type of object to  show', metavar='{file,template,run}')

        file_subparser = subparsers.add_parser('file', help='show files')
        ShowFile.get_parser(file_subparser)
        file_subparser.set_defaults(SubSubcommandClass=ShowFile)

        hidden_file_subparser = subparsers.add_parser('files')
        ShowFile.get_parser(hidden_file_subparser)
        hidden_file_subparser.set_defaults(SubSubcommandClass=ShowFile)

        template_subparser = subparsers.add_parser('template', help='show templates')
        ShowTemplate.get_parser(template_subparser)
        template_subparser.set_defaults(SubSubcommandClass=ShowTemplate)

        hidden_template_subparser = subparsers.add_parser('templates')
        ShowTemplate.get_parser(hidden_template_subparser)
        hidden_template_subparser.set_defaults(SubSubcommandClass=ShowTemplate)

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
