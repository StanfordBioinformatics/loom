#!/usr/bin/env python

import os
import unittest
from datetime import datetime
import time

from loom.client import server
from loom.client.common import is_server_running
from loom.common.testserver import TestServer

class TestServerControls(unittest.TestCase):

    def setUp(self):
        self.test_server = TestServer()
        self.test_server.setlocal()
        self.test_server.start()

    def tearDown(self):
        self.test_server.stop()

    def test_status(self):
        parser = server.get_parser()
        args = parser.parse_args(['--require_default_settings', 'status'])

        # call by args. This just prints output to screen
        xs = server.ServerControlsFactory(args=args)
        xs.run()
        
        # call by status method directly to check response
        self.assertTrue(is_server_running())

if __name__=='__main__':
    unittest.main()
