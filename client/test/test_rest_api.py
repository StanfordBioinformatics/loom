#!/usr/bin/env python

import os
import unittest
from datetime import datetime
import requests
import time

from xppf.client import xppf_server_controls

class TestXppfRun(unittest.TestCase):

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

        with open(os.path.join(os.path.dirname(__file__),'../../doc/examples/helloworld/helloworld.json')) as f:
            self.helloworld_json = f.read()

    def tearDown(self):
        xsc_parser = xppf_server_controls.XppfServerControls._get_parser()
        args = xsc_parser.parse_args(['stop', '--require_default_settings'])
        xs = xppf_server_controls.XppfServerControls(args=args)
        xs.main()
        self.wait_for_true(lambda: not os.path.exists(xs.settings_manager.get_pid_file()))

    def test_create_show_index_immutable(self):
        import pdb; pdb.set_trace()
        # Test create
        r = requests.post(self.server_url+'/api/analysis_requests', data=self.helloworld_json)
        self.assertEqual(r.text,
                         '{"message": "created analysis_request", "_id": "6fa582dee34ba7e2874ebff16e8cb1fe05e81c686612e2e92e4d9f8087c5dd63"}')

        # Test show
        r = requests.get(self.server_url+'/api/analysis_requests/6fa582dee34ba7e2874ebff16e8cb1fe05e81c686612e2e92e4d9f8087c5dd63')
        self.assertEqual(r.json()['analysis_request']['_id'], '6fa582dee34ba7e2874ebff16e8cb1fe05e81c686612e2e92e4d9f8087c5dd63')

        # Test index
        r = requests.get(self.server_url+'/api/analysis_requests/')
        ids = map(lambda x:x['_id'], r.json()['analysis_requests'])
        self.assertTrue('6fa582dee34ba7e2874ebff16e8cb1fe05e81c686612e2e92e4d9f8087c5dd63' in ids)

    def test_create_show_index_update_mutable(self):
        # Test create
        r = requests.post(self.server_url+'/api/file_path_locations', data=self.file_path_location_json)
        self.assertEqual(r.json()['message'], "created file_path_location")

        # Test show
        id = r.json()['_id']
        r = requests.get(self.server_url+'/api/file_path_locations/%s' % id)
        self.assertEqual(r.json()['file_path_location']['_id'], id)

        # Test index
        r = requests.get(self.server_url+'/api/file_path_locations')
        ids = map(lambda x:x['_id'], r.json()['file_path_locations'])
        self.assertTrue(id in ids)

        # Test update
        r = requests.post(self.server_url+'/api/file_path_locations/%s' % id, 
                          data='{"file_path": "/new/file/path"}')
        r = requests.get(self.server_url+'/api/file_path_locations/%s' % id)
        self.assertEqual(r.json()['file_path_location']['file_path'], '/new/file/path')

    def wait_for_true(self, test_method, timeout_seconds=5):
        start_time = datetime.now()
        while not test_method():
            time.sleep(timeout_seconds/10.0)
            time_running = datetime.now() - start_time
            if time_running.seconds > timeout_seconds:
                raise Exception("Timeout")

if __name__=='__main__':
    unittest.main()
