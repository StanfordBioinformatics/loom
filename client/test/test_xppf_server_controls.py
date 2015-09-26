#!/usr/bin/env python

import os
import unittest
from datetime import datetime
import time

from xppf.client import xppf_server_controls
from xppf.common.testserver import TestServer

class TestXppfServerControls(unittest.TestCase):

    def setUp(self):
        self.test_server = TestServer()
        self.test_server.start()

    def tearDown(self):
        self.test_server.stop()

    def test_status(self):
        parser = xppf_server_controls.XppfServerControls._get_parser()
        args = parser.parse_args(['status', '--require_default_settings'])

        # call by args. This just prints output to screen
        xs = xppf_server_controls.XppfServerControls(args=args)
        xs.main()
        
        # call by status method directly to check response
        response = xs.status()
        self.assertEqual(response.status_code, 200)

if __name__=='__main__':
    unittest.main()
