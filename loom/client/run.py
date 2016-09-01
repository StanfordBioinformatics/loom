#!/usr/bin/env python

import argparse
import os

from loom.client.importer import WorkflowImporter
from loom.client.common import get_server_url, read_as_json_or_yaml
from loom.client.exceptions import *
from loom.common.helper import get_console_logger
from loom.common.filehandler import FileHandler
from loom.common.objecthandler import ObjectHandler


class WorkflowRunner(object):
    """Run a workflow on the server.
    """

    def __init__(self, args=None, logger=None):
        if args is None:
            args = self._get_args()
        self.args = args
        self.master_url = get_server_url()
        if logger is None:
            logger = get_console_logger(name=__file__)
        self.logger = logger
        self.objecthandler = ObjectHandler(self.master_url)
        self.filehandler = FileHandler(self.master_url, logger=self.logger)

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
        parser.add_argument('workflow', metavar='WORKFLOW', help='ID of workflow to run')
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
        run_request = self.objecthandler.post_run_request(
            {
                'template': self.args.workflow,
                'inputs': self._get_inputs()
            }
        )

        self.logger.info('Created run request %s@%s' \
            % (run_request['name'],
               run_request['id']
            ))
        return run_request

    def _get_inputs(self):
        """Converts command line args into a list of workflow inputs
        """
        inputs = []
        if self.args.inputs:
            for kv_pair in self.args.inputs:
                (channel, input_id) = kv_pair.split('=')
                inputs.append({'channel': channel, 'value': input_id})
        return inputs


if __name__=='__main__':
    WorkflowRunner().run()
