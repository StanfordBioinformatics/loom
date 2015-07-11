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

    def test_status(self):
        # Test create
        r = requests.get(self.server_url+'/api/status/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.text, '{"message": "server is up"}')

    def wait_for_true(self, test_method, timeout_seconds=5):
        start_time = datetime.now()
        while not test_method():
            time.sleep(timeout_seconds/10.0)
            time_running = datetime.now() - start_time
            if time_running.seconds > timeout_seconds:
                raise Exception("Timeout")

if __name__=='__main__':
    unittest.main()
