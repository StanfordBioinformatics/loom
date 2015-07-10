#!/usr/bin/env python

import os
from django.test import TestCase
from datetime import datetime
import requests
import time
from django.conf import settings

from xppf.client import xppf_server_controls

class TestXppfRun(TestCase):

    file_path_location_json = """
{
  "file_path": "/path/to/my/file",
  "file": {
    "hash_value": "b1946ac92492d2347c6235b4d2611184",
    "hash_function": "md5"
  }
}                                                                                                                                                                        
"""

    def setUp(self):
        xsc_parser = xppf_server_controls.XppfServerControls._get_parser()
        args = xsc_parser.parse_args(['start', '--require_default_settings'])
        xs = xppf_server_controls.XppfServerControls(args=args)
        xs.main()
        self.server_url = xs.settings_manager.get_server_url()
        self.wait_for_true(lambda: os.path.exists(xs.settings_manager.get_pid_file()))

        with open(os.path.join(settings.BASE_DIR,'../../doc/examples/helloworld/helloworld.json')) as f:
            self.helloworld_json = f.read()

    def tearDown(self):
        xsc_parser = xppf_server_controls.XppfServerControls._get_parser()
        args = xsc_parser.parse_args(['stop', '--require_default_settings'])
        xs = xppf_server_controls.XppfServerControls(args=args)
        xs.main()
        self.wait_for_true(lambda: not os.path.exists(xs.settings_manager.get_pid_file()))

# Requests
# StepRuns
# StepRun/$id/port_bundles
# Files
# FileLocations
# Results

    def test_create_show_index_immutable(self):
        # Test create
        r = requests.post(self.server_url+'/api/requests', data=self.helloworld_json)
        self.assertTrue('{"message": "created request", "_id":' in r.text)

        # Test show
        id = r.json().get('_id')
        r = requests.get(self.server_url+'/api/requests/'+ str(id))
        self.assertEqual(r.json()['_id'], str(id))

        # Test index
        r = requests.get(self.server_url+'/api/requests/')
        ids = map(lambda x:x['_id'], r.json()['requests'])
        self.assertTrue(id in ids)

    def test_create_show_index_update_mutable(self):
        # Test create
        r = requests.post(self.server_url+'/api/file_locations', data=self.file_path_location_json)
        self.assertEqual(r.json()['message'], "created file_location")

        # Test show
        id = r.json()['_id']
        r = requests.get(self.server_url+'/api/file_locations/%s' % id)
        self.assertEqual(r.json()['_id'], id)

        # Test index
        r = requests.get(self.server_url+'/api/file_locations')
        ids = map(lambda x:x['_id'], r.json()['file_locations'])
        self.assertTrue(id in ids)

        # Test update
        r = requests.post(self.server_url+'/api/file_locations/%s' % id, 
                          data='{"file_path": "/new/file/path"}')
        r = requests.get(self.server_url+'/api/file_locations/%s' % id)
        self.assertEqual(r.json()['file_path'], '/new/file/path')

    def wait_for_true(self, test_method, timeout_seconds=5):
        start_time = datetime.now()
        while not test_method():
            time.sleep(timeout_seconds/10.0)
            time_running = datetime.now() - start_time
            if time_running.seconds > timeout_seconds:
                raise Exception("Timeout")

