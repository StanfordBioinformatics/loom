#!/usr/bin/env python

import os
import unittest
from datetime import datetime
import requests
import time

from xppf.client import xppf_server_controls
from xppf.master.utils.testserver import TestServer

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
        self.test_server = TestServer()
        self.test_server.start()

        with open(os.path.join(os.path.dirname(__file__),'../../doc/examples/helloworld/helloworld.json')) as f:
            self.helloworld_json = f.read()

    def tearDown(self):
        self.test_server.stop()

    def test_status(self):
        # Test create
        r = requests.get(self.test_server.server_url+'/api/status/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.text, '{"message": "server is up"}')

if __name__=='__main__':
    unittest.main()
