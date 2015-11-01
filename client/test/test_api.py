#!/usr/bin/env python

import os
import unittest
from datetime import datetime
import requests
import time

from loom.client import xppf_server_controls
from loom.common.testserver import TestServer

class TestXppfRun(unittest.TestCase):

    def setUp(self):
        self.test_server = TestServer()
        self.test_server.start()

    def tearDown(self):
        self.test_server.stop()

    def test_status(self):
        # Test create
        r = requests.get(self.test_server.server_url+'/api/status/')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.text, '{"message": "server is up"}')

if __name__=='__main__':
    unittest.main()
