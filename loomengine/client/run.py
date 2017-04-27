#!/usr/bin/env python

import argparse
import os
import re
import requests.exceptions

from loomengine.client.importer import TemplateImporter
from loomengine.client.common import get_server_url, read_as_json_or_yaml, \
    verify_has_connection_settings, verify_server_is_running
from loomengine.client.exceptions import *
from loomengine.utils.filemanager import FileManager
from loomengine.utils.connection import Connection


class TemplateRunner(object):
    """Run a workflow on the server.
    """

    def __init__(self, args=None):
        if args is None:
            args = self._get_args()
        self.args = args
        verify_has_connection_settings()
        server_url = get_server_url()
        verify_server_is_running(url=server_url)
        self.connection = Connection(server_url)
        self.filemanager = FileManager(server_url)

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
        parser.add_argument('inputs', metavar='INPUT_NAME=DATA_ID', nargs='*', help='ID of data inputs')
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
        run_request_data = {
            'template': self.args.template,
            'inputs': self._get_inputs()}
        try:
            run_request = self.connection.post_run_request(run_request_data)
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
            run_request['template']['name'],
            run_request['uuid'])

    def _get_inputs(self):
        """Converts command line args into a list of template inputs
        """
        inputs = []
        if self.args.inputs:
            for kv_pair in self.args.inputs:
                (channel, input_id) = kv_pair.split('=')
                inputs.append({'channel': channel, 'data': 
                               {'contents':
                                self._parse_string_to_nested_lists(input_id)}
                           })
        return inputs

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

if __name__=='__main__':
    TemplateRunner().run()
