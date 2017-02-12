#!/usr/bin/env python

import argparse
import os

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
        run_request = self.connection.post_run_request(run_request_data)

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
                               {'contents': input_id}
                           })
        return inputs


if __name__=='__main__':
    TemplateRunner().run()
