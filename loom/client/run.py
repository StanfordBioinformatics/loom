#!/usr/bin/env python

import argparse
from jinja2 import DictLoader, Environment
import json
import os
import requests
import yaml

from loom.client import settings_manager
from loom.client import upload

class SubmitWorkflowException(Exception):
    pass

class InvalidConstantsException(Exception):
    pass

class MissingConstantsException(Exception):
    pass

class WorkflowRunner(object):
    """Run a workflow.
    First upload input files and create corresponding DataObjects
    with file hashes in the workflow, then submit workflow to run.
    Workflow may be in either YAML or JSON format.
    """

    def __init__(self, args=None):
        if args == None:
            args = self._get_args()
        self.args = args
        self._validate_constants()
        self.settings_manager = settings_manager.SettingsManager(
            settings_file=self.args.settings, 
            require_default_settings=self.args.require_default_settings,
            save_settings=not self.args.no_save_settings
            )

    def _get_args(self):
        parser = self.get_parser()
        args = parser.parse_args()
        return args

    @classmethod
    def get_parser(cls, parser=None):
        if parser == None:
            parser = argparse.ArgumentParser(__file__)
        parser.add_argument('workflow_file', metavar='WORKFLOW_FILE')
        parser.add_argument('constants', metavar='CONSTANT_KEY=VALUE',  nargs='*')
        parser.add_argument('--settings', '-s', metavar='SETTINGS_FILE',
                            help="Settings indicate what server to talk to and how to launch it. Use 'loom config")
        parser.add_argument('--require_default_settings', action='store_true', help=argparse.SUPPRESS)
        parser.add_argument('--no_save_settings', action='store_true', help=argparse.SUPPRESS)
        return parser

    def _validate_constants(self):
        for constant in self.args.constants:
            vals = constant.split('=')
            if not len(vals) == 2:
                self._raise_validate_constants_error(constant)
            elif vals[0] == '':
                self._raise_validate_constants_error(constant)

    def _raise_validate_constants_error(self, constant):
        raise InvalidConstantsException('Invalid constant key-value pair "%s". Must be of the form key=value' % constant)

    def run(self):
        self._read_workflow_file()
        self._substitute_command_line_constants()
        self._validate_workflow()
        self._process_data_uploads()
        self._submit_workflow()

    def _read_workflow_file(self):
        try:
            with open(self.args.workflow_file) as f:
                self.workflow = json.load(f)
                return
        except IOError:
            raise Exception('Could not find or could not read file %s' % self.args.workflow_file)
        except ValueError:
            pass

        try:
            with open(self.args.workflow_file) as f:
                self.workflow = yaml.load(f)
                return
        except IOError:
            raise Exception('Could not find or could not read file %s' % self.args.workflow_file)
        except yaml.parser.ParserError:
            raise Exception('Input file is not valid YAML or JSON format')

    def _substitute_command_line_constants(self):
        workflow_constants = self.workflow.setdefault('constants', {})
        workflow_constants.update(self._get_command_line_constants())
        for key, value in workflow_constants.iteritems():
            if value is None:
                raise MissingConstantsException('The constant "%s" is not defined. '
                                'You can set it from the commandline with '
                                '"loomrun FILENAME %s=VALUE"' % (key, key))

    def _get_command_line_constants(self):
        command_line_constants = {}
        for constant in self.args.constants:
            (key, value) = constant.split('=')
            command_line_constants[key] = value
        return command_line_constants

    def _validate_workflow(self):
        #TODO
        pass

    def _process_data_uploads(self):
        inputs = self.workflow.setdefault('inputs', [])
        counter = 0
        for input in inputs:
            print "Processing input %s of %s" % (counter, len(inputs))
            self._process_data_upload(input)

    def _process_data_upload(self, input):
        filename = self.render(data_upload['filename'])
        if data_upload['type'] == 'file':
            file_id = self._upload_file(filename)
            self.input_files[filename] = file_id

    def _upload_file(self, raw_filename):
        filename = self.render(raw_filename)
        if not os.path.isfile(filename):
            raise Exception('File not found at %s' % filename)
        uploader = self._get_uploader(filename)
        return uploader.run()

    def _get_uploader(self, filename):
        parser = upload.Upload.get_parser()
        arg_set = ['--settings', self.args.settings]
        if self.args.no_save_settings:
            arg_set.append('--no_save_settings')
        if self.args.require_default_settings:
            arg_set.append('--require_default_settings')
        arg_set.append(filename)
        args = parser.parse_args(arg_set)
        return upload.Upload(args)
        
    def _submit_workflow(self):
        try:
            response = requests.post(self.settings_manager.get_server_url_for_client()+'/api/submitworkflow', data=json.dumps(self.workflow))
        except requests.exceptions.ConnectionError as e:
            raise Exception("No response from server. (%s)" % e)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise SubmitWorkflowException("%s\n%s" % (e.message, response.text))
        return response

    def render(self, template_string):
        if template_string == None:
            return None
        max_iter = 1000
        counter = 0
        while True:
            counter += counter
            updated_template_string = self._render_once(template_string)
            if updated_template_string == template_string:
                return template_string
            if counter > max_iter:
                raise Exception("There appears to be a cyclical reference in your {{ templates }}. "
                                "Maximum iterations exceeded in rendering a template string for this step: %s" % step.to_obj())
            template_string = updated_template_string
            
    def _render_once(self, template_string):
        loader = DictLoader({'template': template_string})
        env = Environment(loader=loader)
        template = env.get_template('template')
        constants = self.workflow.setdefault('constants', {})
        return template.render(**constants)

if __name__=='__main__':
    WorkflowRunner().run()
