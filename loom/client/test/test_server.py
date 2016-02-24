#!/usr/bin/env python

import os
import unittest
from datetime import datetime
import time

from loom.client import server
from loom.common.testserver import TestServer

class TestServerControls(unittest.TestCase):

    def setUp(self):
        self.test_server = TestServer()
        self.test_server.start()

    def tearDown(self):
        self.test_server.stop()

    def test_status(self):
        parser = server.ServerControls.get_parser()
        args = parser.parse_args(['status', '--require_default_settings'])

        # call by args. This just prints output to screen
        xs = server.ServerControls(args=args)
        xs.run()
        
        # call by status method directly to check response
        self.assertTrue(server.is_server_running(xs.settings_manager.get_server_url_for_client()))

if __name__=='__main__':
    unittest.main()
