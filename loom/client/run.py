#!/usr/bin/env python

import argparse
import os
import warnings

from loom.client.common import get_settings_manager
from loom.client.common import add_settings_options_to_parser
from loom.client.exceptions import *
from loom.client.upload import WorkflowUploader, FileUploader
from loom.common.filehandler import FileHandler
from loom.common.helper import get_stdout_logger
from loom.common.objecthandler import ObjectHandler

class WorkflowRunner(object):
    """Run a workflow, either from a local file or from the server.
    Prompt for inputs if needed.
    """

    def __init__(self, args=None):
        if args == None:
            args = self._get_args()
        self.args = args
        self.settings_manager = get_settings_manager(self.args)
        self.master_url = self.settings_manager.get_server_url_for_client()

    def _get_args(self):
        parser = self.get_parser()
        args = parser.parse_args()
        self._validate_inputs(args.inputs)
        return args

    @classmethod
    def get_parser(cls, parser=None):
        if parser == None:
            parser = argparse.ArgumentParser(__file__)
        parser.add_argument('workflow', metavar='WORKFLOW', help='Workflow ID or file path')
        parser.add_argument('inputs', metavar='INPUT_NAME=DATA_ID',  nargs='*', help='Data object ID or file path for inputs')
        parser = add_settings_options_to_parser(parser)
        return parser

    def run(self):
        self.terminal = get_stdout_logger()
        self._get_objecthandler()
        self._get_filehandler()
        self._get_workflow()
        self._initialize_workflow_run_request()
        self._get_inputs_required()
        self._get_inputs_provided()
        self._prompt_for_missing_inputs()
        self._create_workflow_run_request()

    def _validate_inputs(self, inputs):
        if not inputs:
            return
        for input in inputs:
            vals = input.split('=')
            if not len(vals) == 2:
                self._raise_validate_inputs_error(input)
            elif vals[0] == '':
                self._raise_validate_inputs_error(input)

    def _raise_validate_inputs_error(self, input):
        raise InvalidInputError('Invalid input key-value pair "%s". Must be of the form key=value' % input)

    def _get_objecthandler(self):
        self.objecthandler = ObjectHandler(self.master_url)

    def _get_filehandler(self):
        self.filehandler = FileHandler(self.master_url)

    def _get_workflow(self):
        workflow_from_server = self._get_workflow_from_server()
        workflow_from_file = self._get_workflow_from_file()
        if not (workflow_from_server or workflow_from_file):
            raise Exception('Could not find workflow that matches "%s"' % self.args.workflow)
        if workflow_from_server and not workflow_from_file:
            self.workflow = workflow_from_server
            return
        if workflow_from_server and workflow_from_file:
            warnings.warn('The workflow name "%s" matches both a local file and a workflow on the server. '\
                          'Using the local file.')
        # Workflow is from local source, not server. Post it now.
        workflow_from_file['workflow_name'] = self._get_workflow_name(workflow_from_file, self.args.workflow)
        self.workflow = self.objecthandler.post_workflow(workflow_from_file)

    def _get_workflow_name(self, workflow, workflow_path):
        if workflow.get('workflow_name') is not None:
            return workflow.get('workflow_name')
        else:
            return os.path.basename(workflow_path)
                    
    def _get_workflow_from_server(self):
        return self.objecthandler.get_workflow(self.args.workflow)

    def _get_workflow_from_file(self):
        try:
            return WorkflowUploader.get_workflow(self.args.workflow)
        except NoFileError:
            return None
        except InvalidFormatError:
            return None

    def _initialize_workflow_run_request(self):
        self.workflow_run_request = {
            'workflow': self.workflow,
            'inputs': []
        }

    def _get_inputs_required(self):
        self.inputs_required = {}
        for input in self.workflow['workflow_inputs']:
            if self._is_indefinite_input(input):
                self.inputs_required[input['input_name']] = input

    def _is_indefinite_input(self, input):
        return input.get('input_name') is not None

    def _get_inputs_provided(self):
        self.inputs_provided = {}
        if not self.args.inputs:
            return
        else:
            for input in self.args.inputs:
                (name, val) = input.split('=')
                self.inputs_provided[name] = val
                if name not in self.inputs_required.keys():
                    raise UnmatchedInputError('Unmatched input "%s" is not in workflow' % name)
        for (input_name, input_id) in self.inputs_provided.iteritems():
            data_object = self._get_input(input_id)
            self._add_input(input_name, data_object)

    def _get_input(self, input_id):
        input_from_server = self._get_input_from_server(input_id)
        input_file = self._get_input_file(input_id)
        if not (input_from_server or input_file):
            raise Exception('Could not find input that matches "%s"' % input_id)
        if input_from_server and not input_file:
            data_object = input_from_server
            return data_object
        if input_from_server and input_file:
            warnings.warn('The input name "%s" matches both a local file and a file on the server. '\
                          'Using the local file.')
        # Input is from local source, not server. Upload it now.
        source_record_text = FileUploader.prompt_for_source_record_text(input_file)
        data_object = self.filehandler.upload_file_from_local_path(input_file, source_record=source_record_text, logger=self.terminal)
        return data_object

    def _get_input_from_server(self, input_id):
        return self.objecthandler.get_file_data_object(input_id)

    def _get_input_file(self, raw_input_id):
        """If input_id is the path to a file, return that path. Otherwise None.
        """
        input_id = os.path.expanduser(raw_input_id)
        if os.path.isfile(input_id):
            return input_id
        else:
            return None

    def _add_input(self, input_name, data_object):
        self.workflow_run_request['inputs'].append({
            'input_name': input_name,
            'data_object': data_object
        })

    def _prompt_for_missing_inputs(self):
        """For any users that are required but were not provided at the command line, prompt the
        user
        """
        for (input_name, input) in self.inputs_required.iteritems():
            if not input_name in self.inputs_provided.keys():
                self._prompt_for_input(input_name)

    def _prompt_for_input(self, input_name):
        input_id = None
        while not input_id:
            input_id = raw_input(
                'The input "%s" is required. Enter a file path or data identifier.\n>' % input_name
            )
        data_object = self._get_input(input_id)
        self._add_input(input_name, data_object)
        
    def _create_workflow_run_request(self):
        workflow_run_request_from_server = self.objecthandler.post_workflow_run_request(self.workflow_run_request)
        print 'Created run request %s for workflow "%s"' \
            % (workflow_run_request_from_server['_id'],
               self.workflow['workflow_name'])

if __name__=='__main__':
    WorkflowRunner().run()
