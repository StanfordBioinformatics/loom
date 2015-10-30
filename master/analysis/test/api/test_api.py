from django.conf import settings
from django.test import TestCase
from datetime import datetime
import json
import os
import requests
import sys
import time

from analysis.models import RequestSubmission
from loom.client import xppf_server_controls

sys.path.append(os.path.join(settings.BASE_DIR, '../../..'))
from loom.common.fixtures import *
from loom.common.helper import Helper

class TestXppfRun(TestCase):

    def setUp(self):
        # Start server
        xsc_parser = xppf_server_controls.XppfServerControls._get_parser()
        args = xsc_parser.parse_args(['start', '--require_default_settings'])
        self.xs = xppf_server_controls.XppfServerControls(args=args)
        self.xs.main()
        self.server_url = self.xs.settings_manager.get_server_url_for_client()

        # Confirm server started
        Helper.wait_for_true(self._webserver_started, timeout_seconds=5)

    def tearDown(self):
        # Stop server
        xsc_parser = xppf_server_controls.XppfServerControls._get_parser()
        args = xsc_parser.parse_args(['stop', '--require_default_settings'])
        xs = xppf_server_controls.XppfServerControls(args=args)
        xs.main()

        # Confirm server stopped
        Helper.wait_for_true(self._webserver_stopped, timeout_seconds=5)

    def _webserver_started(self):
        return os.path.exists(self.xs.settings_manager.get_webserver_pidfile())

    def _webserver_stopped(self):
        return not os.path.exists(self.xs.settings_manager.get_webserver_pidfile())

# RequestSubmissions
# StepRuns
# StepRun/$id/port_bundles
# Files
# FileStorageLocations
# Results

    def test_create_show_index_immutable(self):
        # Test create
        r = requests.post(self.server_url+'/api/request_submissions', data=helloworld_json)
        r.raise_for_status()
        self.assertTrue('{"message": "created request_submission", "_id":' in r.text)

        # Test show
        id = r.json().get('_id')
        r = requests.get(self.server_url+'/api/request_submissions/'+ str(id))
        r.raise_for_status()
        self.assertEqual(r.json()['_id'], str(id))

        # Test index
        r = requests.get(self.server_url+'/api/request_submissions/')
        r.raise_for_status()
        ids = map(lambda x:x['_id'], r.json()['request_submissions'])
        self.assertTrue(id in ids)

    def test_create_show_index_update_mutable(self):
        # Test create
        r = requests.post(self.server_url+'/api/file_storage_locations', data=json.dumps(server_file_storage_location_obj))
        r.raise_for_status()
        self.assertEqual(r.json()['message'], "created file_storage_location")

        # Test show
        id = r.json()['_id']
        r = requests.get(self.server_url+'/api/file_storage_locations/%s' % id)
        r.raise_for_status()
        self.assertEqual(r.json()['_id'], id)

        # Test index
        r = requests.get(self.server_url+'/api/file_storage_locations')
        r.raise_for_status()
        ids = map(lambda x:x['_id'], r.json()['file_storage_locations'])
        self.assertTrue(id in ids)

        # Test update
        r = requests.post(self.server_url+'/api/file_storage_locations/%s' % id, 
                          data='{"file_path": "/new/file/path"}')
        r.raise_for_status()
        r = requests.get(self.server_url+'/api/file_storage_locations/%s' % id)
        r.raise_for_status()
        self.assertEqual(r.json()['file_path'], '/new/file/path')
    """
    def test_show_input_port_bundles(self):
        r = requests.post(self.server_url+'/api/request_submissions/', data=json.dumps(hello_world_request_with_runs))
        r.raise_for_status()
        id = hello_world_request_with_runs.get('workflows')[0].get('steps')[0].get('_id')
        r = requests.get(self.server_url+'/api/step_runs/%s/input_port_bundles/' % id)
        r.raise_for_status()
        """

