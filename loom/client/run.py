#!/usr/bin/env python

import argparse
from collections import OrderedDict
import os
import warnings
import sys

from loom.client.common import get_settings_manager_from_parsed_args
from loom.client.common import add_settings_options_to_parser
from loom.client.common import read_as_json_or_yaml
from loom.client.exceptions import *
from loom.client.upload import WorkflowUploader, FileUploader
from loom.common.filehandler import FileHandler
from loom.common.helper import get_console_logger
from loom.common.objecthandler import ObjectHandler


class AbstractInputProcessor(object):
    """Process input values provided by the user when submitting a run,
    according to their type
    """

    def __init__(self, objecthandler, filehandler, logger):
        self.objecthandler = objecthandler
        self.filehandler = filehandler
        self.logger = logger

    def _list_to_single(self, input_id_list):
        if not isinstance(input_id_list, list):
            raise ValidationError('Expected list but got "%s"' % input_id_list)
        if len(input_id_list) != 1:
            raise ValidationError('Expected 1 input but found %s: "%s"'\
                            % (len(input_id_list), input_id_list))
        return input_id_list[0]

    def _create_array(self, data_objects):
        return self.objecthandler.post_data_object_array(
            {
                'data_objects': data_objects
            }
        )

    
class FileInputProcessor(AbstractInputProcessor):

    def load_data_object(self, input_id_list, value_is_list_format=True):
        if value_is_list_format:
            input_id = self._list_to_single(input_id_list)
        else:
            input_id = input_id_list
        return self._get_input(input_id)

    def _get_input(self, input_id):
        inputs_from_server = self._get_inputs_from_server(input_id)
        input_file = self._get_input_file(input_id)
        if not (inputs_from_server or input_file):
            raise UnmatchedInputError('Could not find input that matches "%s"' % input_id)
        if inputs_from_server and not input_file:
            # Return only if there is a single match for the input on the server.
            if len(inputs_from_server) > 1:
                input_list = [input['filename']+'@'+input['_id'][:7] for input in inputs_from_server]
                raise Exception('Multiple inputs on the server matched "%s". Try using the full id. \n%s' % (input_id, '\n'.join(input_list)))
            else:
                data_object = inputs_from_server[0]
            return data_object
        if inputs_from_server and input_file:
            # Local file matches input. Assume the user wants this rather than any matches on the server.
            self.logger.warn('The input "%s" matches both a local file and one or more files on the server. '\
                          'Using the local file.')
        # Input is from local source, not server. Upload it now.
        source_record_text = FileUploader.prompt_for_source_record_text(input_file)
        data_object = self.filehandler.import_file_from_local_path(input_file, source_record=source_record_text)
        return data_object

    def _get_inputs_from_server(self, input_id):
        data_object_list = self.objecthandler.get_file_data_object_index(query_string=input_id)
        return data_object_list

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
                '"%s": "%s"\nThis input is required. Enter a file path or identifier: ' % (input_name, prompt)
            )
        data_object = self._get_input(input_id)
        return data_object


class FileArrayInputProcessor(FileInputProcessor):

    #Override
    def load_data_object(self, input_id_list, value_is_list_format=True):
        file_data_objects = []
        for input_id in input_id_list:
            file_data_objects.append(self._get_input(input_id))
        file_array_data_object = self._create_array(file_data_objects)
        return file_array_data_object

    def prompt_for_input(self, input_name, prompt):
        input_ids = []
        input_id = None
        while input_id or not input_ids:
            # Continue until at least one value is provided
            # Then stop on the first blank
            if not input_ids:
                # No inputs yet. Hitting return will just bring up the prompt until they enter something.
                text = '\n"%s": "%s"\nThis input is required. \nEnter a list of file paths or identifiers, one per line. > ' % (input_name, prompt)
            else:
                text = 'Next value, or press [enter] to finish. > '
            input_id = raw_input(text)
            if not input_id:
                continue
            input_ids.append(input_id)
        file_data_objects = []
        for input_id in input_ids:
            file_data_objects.append(self._get_input(input_id))
        file_array_data_object = self._create_array(file_data_objects)
        return file_array_data_object


class DatabaseObjectMixin(object):

    def load_data_object(self, value_list, value_is_list_format=None):
        if value_is_list_format:
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
    def load_data_object(self, value_list, value_is_list_format=None):
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


class BooleanInputProcessor(DatabaseObjectMixin, AbstractInputProcessor):

    human_readable_type_lc = "boolean"

    def _get_input(self, boolean):
        return self.objecthandler.post_data_object(
            {
                'boolean_value': self._to_bool(boolean)
            }
        )

    def _to_bool(self, value):
        if value.lower() == 'true':
            return True
        elif value.lower() == 'false':
            return False
        else:
            raise Exception('Couldn\'t convert "%s" to a boolean. Value should be "true" or "false".')


class BooleanArrayInputProcessor(DatabaseObjectArrayMixin, BooleanInputProcessor):

    pass

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


def InputProcessor(type, objecthandler, filehandler, logger):
    """Factory method that returns the InputProcessor class for handling
    a given input type
    """

    INPUT_PROCESSORS = {
        'file': FileInputProcessor,
        'file_array': FileArrayInputProcessor,
        'string': StringInputProcessor,
        'string_array': StringArrayInputProcessor,
        'boolean': BooleanInputProcessor,
        'boolean_array': BooleanArrayInputProcessor,
        'integer': IntegerInputProcessor,
        'integer_array': IntegerArrayInputProcessor
    }

    return INPUT_PROCESSORS[type](
        objecthandler,
        filehandler,
        logger
    )

    
class WorkflowRunner(object):
    """Run a workflow, either from a local file or from the server.
    Prompt for inputs if needed.
    """

    def __init__(self, args=None, logger=None):
        if args is None:
            args = self._get_args()
        self.args = args
        self.settings_manager = get_settings_manager_from_parsed_args(self.args)
        self.master_url = self.settings_manager.get_server_url_for_client()
        if logger is None:
            logger = get_console_logger(name=__file__)
        self.logger = logger

    def _get_args(self):
        parser = self.get_parser()
        args = parser.parse_args()
        self._validate_args(args)
        return args

    @classmethod
    def get_parser(cls, parser=None):
        if parser is None:
            parser = argparse.ArgumentParser(__file__)
        parser.add_argument('workflow', metavar='WORKFLOW', help='Workflow ID or file path')
        parser.add_argument('inputs', metavar='INPUT_NAME=DATA_ID', nargs='*', help='Data object ID or file path for inputs')
        parser = add_settings_options_to_parser(parser)
        return parser

    def run(self):
        self._get_objecthandler()
        self._get_filehandler()
        self._get_workflow()
        self._initialize_workflow_run()
        self._process_predefined_inputs()
        self._get_inputs_required()
        self._get_inputs_provided()
        self._prompt_for_missing_inputs()
        self._process_inputs_provided()
        self._create_workflow_run()

    def _validate_args(self, args):
        self._validate_command_line_inputs(args.inputs)

    def _validate_command_line_inputs(self, inputs):
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
        self.filehandler = FileHandler(self.master_url, logger=self.logger)

    def _get_workflow(self):
        workflow_id = self.args.workflow
        workflows_from_server = self._get_workflows_from_server(workflow_id)
        workflow_from_file = self._get_workflow_from_file(workflow_id)
        if not (workflows_from_server or workflow_from_file):
            raise Exception('Could not find workflow that matches "%s"' % workflow_id)
        elif workflows_from_server and not workflow_from_file:
            # Return only if there is a single match for the workflow on the server.
            if len(workflows_from_server) > 1:
                workflow_list = [workflow['workflow_name']+'@'+workflow['_id'][:7] for workflow in workflows_from_server]
                raise Exception('Multiple workflows on the server matched "%s". Try using the full id. \n%s' % (workflow_id, '\n'.join(workflow_list)))
            else:
                self.workflow = workflows_from_server[0]
                self._validate_workflow()
                return
        elif workflows_from_server and workflow_from_file:
            warnings.warn('The workflow name "%s" matches both a local file and a workflow on the server. '\
                          'Using the local file.')
        else:
            # Workflow is from local source, not server.
            self.workflow = workflow_from_file
            self._validate_workflow()

    def _validate_workflow(self):
        if self.workflow.get('workflow_inputs'):
            if not isinstance(self.workflow['workflow_inputs'], list):
                raise ValidationError('Workflow is invalid. "workflow_inputs" should contain a list but it contains "%s"'\
                                      % self.workflow.get('workflow_inputs'))
            for input in self.workflow['workflow_inputs']:
                if not isinstance(input, dict):
                    raise ValidationError('Workflow is invalid. Workflow input should be a dict but it contains "%s"'\
                                          % input)
                if not input.get('to_channel'):
                    raise ValidationError('Workflow is invalid. "to_channel" is not defined for this input: "%s"' % input)
                if not input.get('type'):
                    raise ValidationError('Workflow is invalid. "type" is not defined for this input: "%s"' % input)
            
    def _get_workflow_name(self, workflow, workflow_path):
        if workflow.get('workflow_name') is not None:
            return workflow.get('workflow_name')
        else:
            return os.path.basename(workflow_path)
                    
    def _get_workflows_from_server(self, workflow_id):
        workflow_list = self.objecthandler.get_workflow_index(query_string=workflow_id)
        return workflow_list

    def _get_workflow_from_file(self, workflow_id):
        if os.path.exists(os.path.expanduser(workflow_id)):
            return WorkflowUploader.default_run(os.path.expanduser(workflow_id))
        else:
            return None

    def _initialize_workflow_run(self):
        self.workflow_run = {
            'workflow': self.workflow,
            'workflow_run_inputs': []
        }

    def _process_predefined_inputs(self):
        """Process inputs with values predefined in the workflow.
        """
        if not self.workflow.get('workflow_inputs'):
            return
        for input in self.workflow['workflow_inputs']:
            if self._has_value(input):
                self._process_input(input['to_channel'], input['value'], input['type'], input, value_is_list_format=False)

    def _has_value(self, input):
        """True if input already has a value assigned. Otherwise the user will be 
        prompted for a value
        """
        return input.get('value') is not None
    
    def _get_inputs_required(self):
        self.inputs_required = OrderedDict()
        if not self.workflow.get('workflow_inputs'):
            return
        for workflow_input in self.workflow['workflow_inputs']:
            if not self._has_value(workflow_input):
                self.inputs_required[workflow_input['to_channel']] = workflow_input

    def _get_inputs_provided(self):
        """Produces a dict of inputs provided with the run command.
        """
        self.inputs_provided = {}
        if self.args.inputs:
            for kv_pair in self.args.inputs:
                (name, values) = kv_pair.split('=')
                value_list = values.split(',')
                self.inputs_provided[name] = value_list
                if name not in self.inputs_required.keys():
                    raise UnmatchedInputError('Unmatched input "%s" is not in workflow' % name)
                self.inputs_provided[name] = {'value': value_list, 'value_is_list_format': True}

    def _process_inputs_provided(self):
        for (input_name, input_info) in self.inputs_provided.iteritems():
            data_object = InputProcessor(
                self.inputs_required[input_name]['type'],
                objecthandler=self.objecthandler,
                filehandler=self.filehandler,
                logger = self.logger
            ).load_data_object(input_info['value'], value_is_list_format=input_info['value_is_list_format'])
            workflow_input = filter(lambda x:x['to_channel']==input_name, self.workflow['workflow_inputs'])[0]
            self._process_input(input_name, input_info['value'], workflow_input['type'], workflow_input, value_is_list_format=True)
            
    def _process_input(self, name, value, type, workflow_input, value_is_list_format=True):
        data_object = InputProcessor(
            type,
            objecthandler=self.objecthandler,
            filehandler=self.filehandler,
            logger = self.logger
        ).load_data_object(value, value_is_list_format=value_is_list_format)
        self._add_workflow_run_input(name, data_object, workflow_input)
        
    def _add_workflow_run_input(self, input_name, data_object, workflow_input):
        self.workflow_run['workflow_run_inputs'].append({
            'workflow_input': workflow_input,
            'data_object': data_object
        })

    def _prompt_for_missing_inputs(self):
        """For any inputs that are required but were not provided at the command line, prompt the
        user
        """
        for (input_name, input) in self.inputs_required.iteritems():
            if not input_name in self.inputs_provided.keys():
                data_object = InputProcessor(
                    self.inputs_required[input_name]['type'],
                    objecthandler=self.objecthandler,
                    filehandler=self.filehandler,
                    logger = self.logger
                ).prompt_for_input(input_name, input['prompt'])
                self._add_workflow_run_input(input_name, data_object, self.inputs_required[input_name])

    def _create_workflow_run(self):
        workflow_run_from_server = self.objecthandler.post_workflow_run(self.workflow_run)
        self.logger.info('Created run %s for workflow "%s"' \
            % (workflow_run_from_server['_id'],
               self.workflow['workflow_name']))

if __name__=='__main__':
    WorkflowRunner().run()
