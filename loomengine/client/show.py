#!/usr/bin/env python

import argparse
from datetime import datetime
import dateutil.parser
from dateutil import tz
import json
import os
import sys
import yaml
from loomengine.client.common import get_server_url, verify_server_is_running, \
    verify_has_connection_settings

from loomengine.client.exceptions import *
from loomengine.utils.connection import Connection


DATETIME_FORMAT = '%b %d, %Y %-I:%M:%S %p'

def render_time(timestr):
    time_gmt = dateutil.parser.parse(timestr)
    time_local = time_gmt.astimezone(tz.tzlocal())
    return format(time_local, DATETIME_FORMAT)

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
        parser.add_argument(
            '--type',
            choices=['imported', 'result', 'log', 'all'],
            default='imported',
            help='Show only files of the specified type. '\
            '(ignored when FILE_IDENTIFIER is given)')

        parser = super(ShowFile, cls).get_parser(parser)
        return parser

    def run(self):
        self._get_files()
        self._show_files()

    def _get_files(self):
        if self.args.file_id:
            source_type=None
        else:
            source_type=self.args.type
        self.files = self.connection.get_data_object_index(
            query_string=self.args.file_id, source_type=source_type, type='file')

    def _show_files(self):
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
        parser.add_argument(
            '--all',
            action='store_true',
            help='Show all templates, including nested children. '\
            '(ignored when TEMPLATE_IDENTIFIER is given)')
        parser = super(ShowTemplate, cls).get_parser(parser)
        return parser

    def run(self):
        self._get_templates()
        self._show_templates()

    def _get_templates(self):
        if self.args.template_id:
            imported = False
        else:
            imported = not self.args.all
        self.templates = self.connection.get_template_index(
            query_string=self.args.template_id,
            imported=imported)

    def _show_templates(self):
        print '[showing %s templates]' % len(self.templates)
        for template in self.templates:
            print self._render_template(template)

    def _render_template(self, template):
        template_identifier = '%s@%s' % (template['name'], template['uuid'])
        if self.args.detail:
            text = '---------------------------------------\n'
            text += 'Template: %s\n' % template_identifier
            text += '  - md5: %s\n' % template.get('md5')
            text += '  - Imported: %s\n' % \
                    render_time(template['datetime_created'])
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
        parser.add_argument(
            '--all',
            action='store_true',
            help='Show all runs, including nested children '\
            '(ignored when RUN_IDENTIFIER is given)')
        parser = super(ShowRun, cls).get_parser(parser)
        return parser

    def run(self):
        runs = self._get_runs()
        self._show_runs(runs)

    def _get_runs(self):
        if self.args.run_id:
            parent_only = False
        else:
            parent_only = not self.args.all
        return self.connection.get_run_index(query_string=self.args.run_id,
                                             parent_only=parent_only)

    def _show_runs(self, runs):
        print '[showing %s runs]' % len(runs)
        for run in runs:
            print self._render_run(run)

    def _render_run(self, run):
        run_identifier = '%s@%s' % (run['template']['name'], run['uuid'])
        if self.args.detail:
            text = '---------------------------------------\n'
            text += 'Run: %s\n' % run_identifier
            text += '  - Created: %s\n' % render_time(run['datetime_created'])
            text += '  - Status: %s\n' % run.get('status')
            if run.get('steps'):
                text += '  - Steps:\n'
                for step in run['steps']:
                    text += '    - %s@%s (%s)\n' % (
                        step['name'], step['uuid'], step.get('status'))
        else:
            text = "Run: %s (%s)" % (run_identifier, run.get('status'))
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
