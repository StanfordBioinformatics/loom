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
    """Run a workflow, either from a local file or from the server.
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
        parser.add_argument('workflow', metavar='WORKFLOW', help='Workflow ID or file path')
        parser.add_argument('inputs', metavar='INPUT_NAME=DATA_ID', nargs='*', help='Data object ID or file path for inputs')
        parser.add_argument(
            '--note',
            metavar='SOURCE_NOTE',
            help='Description of the data source for any new inputs. '\
            'Give enough detail for traceability.')
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
        self.workflow = self._get_workflow(self.args.workflow)
        inputs = self._get_inputs()
        run_request = self.objecthandler.post_run_request(
            {
                'template': self.workflow,
                'inputs': inputs
            }
        )

        self.logger.info('Created run request %s@%s' \
            % (run_request['template']['name'],
               run_request['_id']
            ))
        return run_request

    def _get_workflow(self, workflow_id):
        if os.path.isfile(workflow_id):
            workflow = self._get_workflow_from_file(workflow_id)
        else:
            workflow = self._get_workflow_from_server(workflow_id)
        self._validate_inputs(workflow)
        return workflow

    def _validate_inputs(self, workflow):
        """Check to make sure user-provided inputs match inputs in the workflow,
        because server side validation won't happen until after inputs are uploaded.
        """
        inputs_given = []
        if self.args.inputs:
            for kv_pair in self.args.inputs:
                (channel, input_id) = kv_pair.split('=')
                inputs_given.append(channel)

        inputs_needed = []
        for input in workflow.get('inputs'):
            inputs_needed.append(input['channel'])

        for input in inputs_needed:
            if input not in inputs_given:
                raise Exception('Missing workflow input "%s"' % input)

        for input in inputs_given:
            if input not in inputs_needed:
                raise Exception('Input "%s" was given but is not needed by workflow' % input)
            
        if len(set(inputs_given)) < len(inputs_given):
            raise Exception('One or more inputs were given more than once. Inputs: %s' % ', '.join(inputs_given))

        
    def _get_workflow_from_file(self, workflow_filename):
        return WorkflowImporter.import_workflow(workflow_filename, self.filehandler, self.objecthandler, self.logger)

    def _get_workflow_from_server(self, workflow_id):
        workflows = self.objecthandler.get_abstract_workflow_index(query_string=workflow_id, raise_for_status=False)

        if len(workflows) < 1:
            raise Exception('Could not find workflow that matches "%s"' % workflow_id)
        elif len(workflows) > 1:
            raise Exception('Multiple workflows on the server matched "%s". Try using the full id. \n%s' %
                            (workflow_id, '\n'.join(
                                [workflow['workflow_name']+'@'+workflow['_id'][:12] for workflow in workflows]
                            )))
        else:
            return workflows[0]

    def _get_inputs(self):
        """Converts command line args into a list of workflow inputs
        """
        inputs = []
        if self.args.inputs:
            for kv_pair in self.args.inputs:
                (channel, input_id) = kv_pair.split('=')
                inputs.append(self._get_input(channel, input_id))
        return inputs

    def _get_input(self, channel, value):
        """If input type is 'file' and value is a local file path, upload it.
        Otherwise let the server try to resolve the input_id.
        """
        if self._get_input_type(channel) == 'file':
            if os.path.isfile(value):
                value = self._get_input_from_file(value)
        return {'channel': channel, 'value': value}

    def _get_input_type(self, channel):
        workflow_inputs = [input for input in self.workflow['inputs'] if input['channel']==channel]
        if len(workflow_inputs) == 0:
            raise Exception('Input %s not found in workflow' % channel)
        elif len(workflow_inputs) > 1:
            raise Exception('Multiple matches for input %s were found in workflow' % channel)
        return input.get('type')

    def _get_input_from_file(self, input_filename):
        file_data_object = self.filehandler.import_file(
            input_filename,
            self.args.note
        )
        return "%s@%s" % (file_data_object['file_content']['filename'],
                          file_data_object['_id'])


if __name__=='__main__':
    WorkflowRunner().run()
