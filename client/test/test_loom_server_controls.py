#!/usr/bin/env python

import os
import unittest
from datetime import datetime
import time

from loom.client import loom_server_controls
from loom.common.testserver import TestServer

class TestLoomServerControls(unittest.TestCase):

    def setUp(self):
        self.test_server = TestServer()
        self.test_server.start()

    def tearDown(self):
        self.test_server.stop()

    def test_status(self):
        parser = loom_server_controls.LoomServerControls._get_parser()
        args = parser.parse_args(['status', '--require_default_settings'])

        # call by args. This just prints output to screen
        xs = loom_server_controls.LoomServerControls(args=args)
        xs.main()
        
        # call by status method directly to check response
        response = xs.status()
        self.assertEqual(response.status_code, 200)

if __name__=='__main__':
    unittest.main()
