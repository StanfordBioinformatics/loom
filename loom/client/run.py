#!/usr/bin/env python

import argparse
import os
import warnings
import sys

if __name__ == "__main__" and __package__ is None:
    rootdir=os.path.abspath('../..')
    sys.path.append(rootdir)

from loom.client.common import get_settings_manager
from loom.client.common import add_settings_options_to_parser
from loom.client.common import read_as_json_or_yaml
from loom.client.exceptions import *
from loom.client.upload import WorkflowUploader, FileUploader
from loom.common.filehandler import FileHandler
from loom.common.helper import get_stdout_logger
from loom.common.objecthandler import ObjectHandler


class AbstractInputProcessor(object):

    def __init__(self, objecthandler, filehandler):
        self.objecthandler = objecthandler
        self.filehandler = filehandler

    def _list_to_single(self, input_id_list):
        if len(input_id_list) != 1:
            raise Exception('Expected 1 input but found %s: "%s"'\
                            % (len(input_id_list), input_id_list))
        return input_id_list[0]

    def _create_array(self, data_objects):
        return self.objecthandler.post_data_object_array(
            {
                'data_objects': data_objects
            }
        )

    
class FileInputProcessor(AbstractInputProcessor):

    def load_data_object(self, input_id_list, convert_from_list=True):
        if convert_from_list:
            input_id = self._list_to_single(input_id_list)
        else:
            input_id = input_id_list
        return self._get_input(input_id)

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
        data_object = self.filehandler.upload_file_from_local_path(input_file, source_record=source_record_text)
        return data_object

    def _get_input_from_server(self, input_id):
        data_object_list = self.objecthandler.get_file_data_object_index(query_string=input_id, max=1)
        if len(data_object_list) == 0:
            return None
        else:
            return data_object_list[0]

    def _get_input_file(self, raw_input_id):
        """If input_id is the path to a file, return that path. Otherwise None.
        """
        input_id = os.path.expanduser(raw_input_id)
        if os.path.isfile(input_id):
            return input_id
        else:
            return None

    def prompt_for_input(self, input_name, prompt):
        input_id = None
        while not input_id:
            input_id = raw_input(
                '\n"%s": "%s"\nThis input is required. Enter a file path or data identifier.\n> ' % (input_name, prompt)
            )
        data_object = self._get_input(input_id)
        return data_object

class FileArrayInputProcessor(FileInputProcessor):

    #Override
    def load_data_object(self, input_id_list, convert_from_list=True):
        file_data_objects = []
        for input_id in input_id_list:
            file_data_objects.append(self._get_input(input_id))
        file_array_data_object = self._create_array(file_data_objects)
        return file_array_data_object

    def prompt_for_input(self, input_name, prompt):
        input_id_list = None
        while not input_id_list:
            input_id_list = raw_input(
                '\n"%s": "%s"\nThis input is required. Enter a space-separated list of file paths or data identifiers.\n> ' % (input_name, prompt)
            )
        input_ids = input_id_list.split(' ')
        file_data_objects = []
        for input_id in input_ids:
            file_data_objects.append(self._get_input(input_id))
        file_array_data_object = self._create_array(file_data_objects)
        return file_array_data_object

class DatabaseObjectMixin(object):

    def load_data_object(self, value_list, convert_from_list=None):
        if convert_from_list:
            value = self._list_to_single(value_list)
        else:
            value = value_list
        return self._get_input(value)

    def prompt_for_input(self, input_name, prompt):
        value = None
        while not value:
            value = raw_input(
                '\n"%s": "%s"\nThis input is required. Enter a %s value.\n> ' % (input_name, prompt, self.human_readable_type_lc)
            )
        data_object = self._get_input(value)
        return data_object

    
class DatabaseObjectArrayMixin(object):

    # override
    def load_data_object(self, value_list, convert_from_list=None):
        data_objects = []
        for value in value_list:
            data_objects.append(self._get_input(value))
        data_object_array = self._create_array(data_objects)
        return data_object_array

    def prompt_for_input(self, input_name, prompt):
        value_list = None
        while not value_list:
            value_list = raw_input(
                '\n"%s": "%s"\nThis input is required. Enter a space-separated list of %s values.\n> ' % (input_name, prompt, self.human_readable_type_lc)
            )
        values = value_list.split(' ')
        data_objects = []
        for value in values:
            data_objects.append(self._get_input(value))
        data_object_array = self._create_array(data_objects)
        return data_object_array

    
class StringInputProcessor(DatabaseObjectMixin, AbstractInputProcessor):

    human_readable_type_lc = "string"

    def _get_input(self, string):
        return self.objecthandler.post_data_object(
            {
                'string_value': string
            }
        )


class StringArrayInputProcessor(DatabaseObjectArrayMixin, StringInputProcessor):

    pass
"""
class BooleanInputProcessor(DatabaseObjectMixin, AbstractInputProcessor):

    human_readable_type_lc = "boolean"

    def _get_input(self, boolean):
        return self.objecthandler.post_data_object(
            {
                'boolean_value': self._to_bool(boolean)
            }
        )

    def _to_bool(self, value):
        if value.lower() == 'true' or \
           value.lower() == 't' or \
           value.lower() == 'yes' or \
           value.lower() == 'y':
            return True
        if value.lower() == 'false' or \
           value.lower() == 'f' or \
           value.lower() == 'no' or \
           value.lower() == 'n':
            return False
        else:
            raise Exception('Couldn\'t convert "%s" to a boolean. Value should be "true" or "false".')

class BooleanArrayInputProcessor(DatabaseObjectArrayMixin, BooleanInputProcessor):

    pass
"""
class IntegerInputProcessor(DatabaseObjectMixin, AbstractInputProcessor):

    human_readable_type_lc = "integer"

    def _get_input(self, integer):
        return self.objecthandler.post_data_object(
            {
                'integer_value': int(integer)
            }
        )


class IntegerArrayInputProcessor(DatabaseObjectArrayMixin, IntegerInputProcessor):

    pass


def InputProcessor(type, objecthandler, filehandler):
    """Factory method that returns the InputProcessor class for handling
    a given input type
    """

    INPUT_PROCESSORS = {
        'file': FileInputProcessor,
        'file_array': FileArrayInputProcessor,
        'string': StringInputProcessor,
        'string_array': StringArrayInputProcessor,
#        'boolean': BooleanInputProcessor,
#        'boolean_array': BooleanArrayInputProcessor,
        'integer': IntegerInputProcessor,
        'integer_array': IntegerArrayInputProcessor
    }

    return INPUT_PROCESSORS[type](
        objecthandler,
        filehandler
    )

    
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
        self._validate_args(args)
        return args

    @classmethod
    def get_parser(cls, parser=None):
        if parser == None:
            parser = argparse.ArgumentParser(__file__)
        parser.add_argument('workflow', metavar='WORKFLOW', help='Workflow ID or file path')
        parser.add_argument('input_values', metavar='INPUT_NAME=DATA_ID',  nargs='*', help='Data object ID or file path for inputs')
        parser.add_argument('--inputs', metavar='INPUT_FILE', help='File containing input values (JSON or YAML), an alternative to giving inputs as command line arguments')
        parser = add_settings_options_to_parser(parser)
        return parser

    def run(self):
        self._get_objecthandler()
        self._get_filehandler()
        self._get_workflow()
        self._initialize_workflow_run()
        self._get_inputs_required()
        self._get_inputs_provided()
        self._prompt_for_missing_inputs()
        self._create_workflow_run()

    def _validate_args(self, args):
        self._validate_input_source(args)
        self._validate_inputs(args.input_values)

    def _validate_input_source(self, args):
        if args.inputs and args.input_values:
            raise Exception('Provide inputs either in a separate file, using the "--inputs" flag, '\
                            'or with "INPUT=VALUE" command line arguments. '\
                            'You cannot use both forms simultaneously.')
        
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
        raise InvalidInputError('Invalid input key-value pair "%s". Must be of the form key=value or key=value1,value2,...' % input)

    def _get_objecthandler(self):
        self.objecthandler = ObjectHandler(self.master_url)

    def _get_filehandler(self):
        self.filehandler = FileHandler(self.master_url, logger=get_stdout_logger())

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
        workflow_id = self.args.workflow
        workflow_list = self.objecthandler.get_workflow_index(query_string=workflow_id, max=1)
        if len(workflow_list) == 0:
            return None
        else:
            return workflow_list[0]

    def _get_workflow_from_file(self):
        try:
            return WorkflowUploader.get_workflow(self.args.workflow)
        except NoFileError:
            return None
        except InvalidFormatError as e:
            raise InvalidFormatError('The file %s is not in a valid format for a workflow. %s' % (self.args.workflow, e.message))

    def _initialize_workflow_run(self):
        self.workflow_run = {
            'workflow': self.workflow,
            'inputs': []
        }

    def _get_inputs_required(self):
        """Produces a dict of inputs required by the workflow
        """
        self.inputs_required = {}
        for input in self.workflow['workflow_inputs']:
            if self._is_indefinite_input(input):
                self.inputs_required[input['input_name']] = input

    def _is_indefinite_input(self, input):
        """Used to identify inputs that will be provided at run time, in
        contrast to inputs that are  specified in the workflow
        """
        return input.get('input_name') is not None

    def _get_inputs_provided(self):
        """Produces a dict of inputs provided by the user, either 
        as command line arguments or in a file.
        """
        self.inputs_provided = {}
        if not self.args.input_values and not self.args.inputs:
            return
        if self.args.inputs:
            self._get_inputs_from_file()
        else:
            self._get_inputs_from_command_line()

    def _get_inputs_from_file(self):
        self.inputs_provided = read_as_json_or_yaml(self.args.inputs)
        if not isinstance(self.inputs_provided, dict):
            raise Exception('The input file "%s" should have the format {"input_name": <<value>>, "input2_name": <<value>>, ...}')
        for key, value in self.inputs_provided.iteritems():
            if key not in self.inputs_required.keys():
                raise UnmatchedInputError('Unmatched input "%s" in "%s" is not in the workflow' % (name, self.args.inputs))
            self._process_input(key, value, convert_from_list=False)

    def _get_inputs_from_command_line(self):
        for kv_pair in self.args.input_values:
            (name, values) = kv_pair.split('=')
            value_list = values.split(',')
            self.inputs_provided[name] = value_list
            if name not in self.inputs_required.keys():
                raise UnmatchedInputError('Unmatched input "%s" is not in workflow' % name)
            self._process_input(name, value_list, convert_from_list=True)

    def _process_input(self, name, value_list, convert_from_list=True):
        data_object = InputProcessor(
            self.inputs_required[name]['type'],
            objecthandler=self.objecthandler,
            filehandler=self.filehandler
        ).load_data_object(value_list, convert_from_list=convert_from_list)
        self._add_input_to_run_request(name, data_object)
        
    def _add_input_to_run_request(self, input_name, data_object):
        self.workflow_run['inputs'].append({
            'input_name': input_name,
            'data_object': data_object
        })

    def _prompt_for_missing_inputs(self):
        """For any users that are required but were not provided at the command line, prompt the
        user
        """
        for (input_name, input) in self.inputs_required.iteritems():
            if not input_name in self.inputs_provided.keys():
                data_object = InputProcessor(
                    self.inputs_required[input_name]['type'],
                    objecthandler=self.objecthandler,
                    filehandler=self.filehandler
                ).prompt_for_input(input_name, input['prompt'])
                self._add_input_to_run_request(input_name, data_object)

    def _create_workflow_run(self):
        workflow_run_from_server = self.objecthandler.post_workflow_run(self.workflow_run)
        print 'Created run request %s for workflow "%s"' \
            % (workflow_run_from_server['_id'],
               self.workflow['workflow_name'])

if __name__=='__main__':
    WorkflowRunner().run()
