#!/usr/bin/env python

import argparse
import os
import re
import requests.exceptions

from loomengine import _render_time
from loomengine.common import get_server_url, read_as_json_or_yaml, \
    verify_has_connection_settings, verify_server_is_running, get_token
from loomengine.run_tag import RunTag
from loomengine.run_label import RunLabel
from loomengine.exceptions import *
from loomengine_utils.filemanager import FileManager
from loomengine_utils.connection import Connection


class RunStart(object):
    """Run a template.
    """

    def __init__(self, args=None):
        if args is None:
            args = self._get_args()
        self.args = args
        verify_has_connection_settings()
        server_url = get_server_url()
        verify_server_is_running(url=server_url)
        token = get_token()
        self.connection = Connection(server_url, token=token)
        self.filemanager = FileManager(server_url, token=token)

    @classmethod
    def _get_args(cls):
        parser = cls.get_parser()
        args = parser.parse_args()
        self._validate_args(args)
        return args

    @classmethod
    def get_parser(cls, parser=None):
        if parser is None:
            parser = argparse.ArgumentParser(__file__)
        parser.add_argument('template', metavar='TEMPLATE', help='ID of template to run')
        parser.add_argument('inputs', metavar='INPUT_NAME=DATA_ID', nargs='*',
                            help='ID or value of data inputs')
        parser.add_argument('-n', '--name', metavar='RUN_NAME',
                            help='run name (default is template name)')
        parser.add_argument('-e', '--notify', action='append',
                            metavar='EMAIL/URL',
                            help='recipients of completed run notifications')
        parser.add_argument('-t', '--tag', metavar='TAG', action='append',
                            help='tag the run when it is started')
        parser.add_argument('-l', '--label', metavar='LABEL', action='append',
                            help='label the run when it is started')
        return parser

    @classmethod
    def _validate_args(cls, args):
        if not args.inputs:
            return
        for input in arg.inputs:
            vals = input.split('=')
            if not len(vals) == 2 or vals[0] == '':
                raise InvalidInputError('Invalid input key-value pair "%s". Must be of the form key=value or key=value1,value2,...' % input)

    def run(self):
        run_data = {
            'template': self.args.template,
            'user_inputs': self._get_inputs(),
            'notification_addresses': self.args.notify,}
        if self.args.name:
            run_data['name'] = self.args.name
        try:
            run = self.connection.post_run(run_data)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code >= 400:
                try:
                    message = e.response.json()
                except:
                    message = e.response.text
                if isinstance(message, list):
                    message = '; '.join(message)
                raise SystemExit(message)
            else:
                raise e

        print 'Created run %s@%s' % (
            run['name'],
            run['uuid'])
        self._apply_tags(run)
        self._apply_labels(run)
        return run

    def _get_inputs(self):
        """Converts command line args into a list of template inputs
        """
        inputs = []
        if self.args.inputs:
            for kv_pair in self.args.inputs:
                (channel, input_id) = kv_pair.split('=')
                inputs.append({
                    'channel': channel,
                    'data': {
                        'contents':
                        self._parse_string_to_nested_lists(input_id)}
                })
        return inputs

    def _apply_tags(self, run):
        if not self.args.tag:
            return
        for tagname in self.args.tag:
            tag_data = {'tag': tagname}
            tag = self.connection.post_run_tag(run.get('uuid'), tag_data)
            print 'Run "%s@%s" has been tagged as "%s"' % \
	        (run.get('name'),
                 run.get('uuid'),
                 tag.get('tag'))

    def _apply_labels(self, run):
        if not self.args.label:
            return
        for labelname in self.args.label:
            label_data = {'label': labelname}
            label = self.connection.post_run_label(
                run.get('uuid'), label_data)
            print 'Run "%s@%s" has been labeled as "%s"' % \
	        (run.get('name'),
                 run.get('uuid'),
                 label.get('label'))

    def _parse_string_to_nested_lists(self, value):
        """e.g., convert "[[a,b,c],[d,e],[f,g]]" 
        into [["a","b","c"],["d","e"],["f","g"]]
        """
        if not re.match('\[.*\]', value.strip()):
            if '[' in value or ']' in value or ',' in value:
                raise Exception('Missing outer brace')
            elif len(value.strip()) == 0:
                raise Exception('Missing value')
            else:
                terms = value.split(',')
                terms = [term.strip() for term in terms]
                if len(terms) == 1:
                    return terms[0]
                else:
                    return terms
                
        # remove outer braces
        value = value[1:-1]
        terms = []
        depth = 0
        leftmost = 0
        first_open_brace = None
        break_on_commas = False
        for i in range(len(value)):
            if value[i] == ',' and depth == 0:
                terms.append(
                    self._parse_string_to_nested_lists(value[leftmost:i]))
                leftmost = i+1
            if value[i] == '[':
                if first_open_brace is None:
                    first_open_brace = i
                depth += 1
            if value[i] == ']':
                depth -= 1
                if depth < 0:
                    raise Exception('Unbalanced close brace')
            i += i
        if depth > 0:
            raise Exception('Expected "]"')
        terms.append(
            self._parse_string_to_nested_lists(value[leftmost:len(value)]))
        return terms


class RunList(object):

    def __init__(self, args):
        self.args = args
        verify_has_connection_settings()
        server_url = get_server_url()
        verify_server_is_running(url=server_url)
        self.connection = Connection(server_url, token=get_token())

    @classmethod
    def get_parser(cls, parser):
        parser.add_argument(
            'run_id',
            nargs='?',
            metavar='RUN_IDENTIFIER',
            help='name or ID of run(s) to list.')
        parser.add_argument(
            '-d', '--detail',
            action='store_true',
            help='show detailed view of runs')
        parser.add_argument(
            '-a', '--all',
            action='store_true',
            help='list all runs, including nested children '\
            '(ignored when RUN_IDENTIFIER is given)')
        parser.add_argument('-l', '--label', metavar='LABEL', action='append',
                            help='filter by label')
        return parser

    def run(self):
        if self.args.run_id:
            parent_only = False
        else:
            parent_only = not self.args.all
        offset=0
        limit=10
        while True:
            data = self.connection.get_run_index_with_limit(
                query_string=self.args.run_id,
                limit=limit, offset=offset,
                labels=self.args.label, parent_only=parent_only)
            if offset == 0:
                print '[showing %s runs]' % data.get('count')
            self._list_runs(data['results'])
            if data.get('next'):
                offset += limit
            else:
                break

    def _list_runs(self, runs):
        for run in runs:
            print self._render_run(run)

    def _render_run(self, run):
        run_identifier = '%s@%s' % (run['name'], run['uuid'])
        if self.args.detail:
            text = '---------------------------------------\n'
            text += 'Run: %s\n' % run_identifier
            text += '  - Created: %s\n' % _render_time(run['datetime_created'])
            text += '  - Status: %s\n' % run.get('status')
            if run.get('steps'):
                text += '  - Steps:\n'
                for step in run['steps']:
                    text += '    - %s@%s (%s)\n' % (
                        step['name'], step['uuid'], step.get('status'))
        else:
            text = "Run: %s (%s)" % (run_identifier, run.get('status'))
        return text


class RunClient(object):
    """Handles subcommands under "run" on the main parser
    """

    def __init__(self, args=None):
        if args is None:
            args = self._get_args()
        self.args = args

    def _get_args(self):
        parser = self.get_parser()
        return parser.parse_args()

    @classmethod
    def get_parser(cls, parser=None):
        if parser is None:
            parser = argparse.ArgumentParser(__file__)

        subparsers = parser.add_subparsers()

        start_subparser = subparsers.add_parser('start', help='start a new run')
        RunStart.get_parser(start_subparser)
        start_subparser.set_defaults(SubSubcommandClass=RunStart)

        list_subparser = subparsers.add_parser(
            'list', help='list runs')
        RunList.get_parser(list_subparser)
	list_subparser.set_defaults(SubSubcommandClass=RunList)

        tag_subparser = subparsers.add_parser('tag', help='manage run tags')
        RunTag.get_parser(tag_subparser)
        tag_subparser.set_defaults(SubSubcommandClass=RunTag)

        label_subparser = subparsers.add_parser('label', help='manage run labels')
        RunLabel.get_parser(label_subparser)
        label_subparser.set_defaults(SubSubcommandClass=RunLabel)

        return parser

    def run(self):
        self.args.SubSubcommandClass(self.args).run()
    
if __name__=='__main__':
    RunClient().run()
