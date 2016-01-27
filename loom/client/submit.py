#!/usr/bin/env python

import json
import requests

from loom.client import settings_manager

_OK_RESPONSE_CODE = 200

class SubmitWorkflowException(Exception):
    pass

class Submit:
    """
    This method provides commands for submitting workflows.
    An loom server must already be running to use this client.
    Users should call this through ../bin/loomsubmit to ensure the environment is configured.
    """

    def __init__(self, args=None):
        if args is None:
            args=self._get_args()
        self.settings_manager = settings_manager.SettingsManager(settings_file = args.settings, require_default_settings=args.require_default_settings)
        self.workflow_file = args.workflow_file

    def _get_args(self):
        parser = self.get_parser()
        args = parser.parse_args()
        return args

    @classmethod
    def get_parser(cls):
        import argparse
        parser = argparse.ArgumentParser('loomsubmit')
        parser.add_argument('workflow_file')
        parser.add_argument('--settings', '-s', metavar='SETTINGS_FILE', 
                            help="Settings indicate what server to talk to and how to launch it. Use 'loomserver savesettings -s SETTINGS_FILE' to save.")
        parser.add_argument('--require_default_settings', '-d', action='store_true', help=argparse.SUPPRESS)
        return parser

    def get(self, relative_url):
        response = requests.get(self.settings_manager.get_server_url_for_client()+relative_url)
        return response

    def post(self, relative_url, data):
        response = requests.post(self.settings_manager.get_server_url_for_client()+relative_url, data=json.dumps(data))
        return response

    def run(self):
        workflow = self.read_workflow_file()

        try:
            response = requests.post(self.settings_manager.get_server_url_for_client()+'/api/submitworkflow', data=json.dumps(workflow))
        except requests.exceptions.ConnectionError as e:
            raise Exception("No response from server. (%s)" % e)

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise SubmitWorkflowException("%s\n%s" % (e.message, response.text))

        return response

    def read_workflow_file(self):
        try: 
            with open(self.workflow_file, 'r') as f:
                workflow_data = json.load(f)
                return workflow_data
        except IOError as e:
            raise Exception('Failed to open workflow file %s. (%s)' % (self.workflow_file, e))
        except ValueError:
            raise Exception("Failed to parse workflow file file because it is not in valid JSON format: %s" % self.workflow_file)

if __name__=='__main__':
    response =  Submit().run()
    print response.text
