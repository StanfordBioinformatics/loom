#!/usr/bin/env python

import os
import unittest
from datetime import datetime
import time

from xppf.client import xppf_server_controls

class TestXppfServerControls(unittest.TestCase):

    def setUp(self):
        self.parser = xppf_server_controls.XppfServerControls._get_parser()
        args = self.parser.parse_args(['start', '--require_default_settings'])
        xs = xppf_server_controls.XppfServerControls(args=args)
        xs.main()
        self.wait_for_true(lambda: os.path.exists(xs.settings_manager.get_pid_file()))

    def tearDown(self):
        args = self.parser.parse_args(['stop', '--require_default_settings'])
        xs = xppf_server_controls.XppfServerControls(args=args)
        xs.main()
        self.wait_for_true(lambda: not os.path.exists(xs.settings_manager.get_pid_file()))

    def test_status(self):
        args = self.parser.parse_args(['status', '--require_default_settings'])

        # call by args. This just prints output to screen
        xs = xppf_server_controls.XppfServerControls(args=args)
        xs.main()
        
        # call by status method directly to check response
        response = xs.status()
        self.assertEqual(response.status_code, 200)
        

    def wait_for_true(self, test_method, timeout_seconds=5):
        start_time = datetime.now()
        while not test_method():
            time.sleep(timeout_seconds/10.0)
            time_running = datetime.now() - start_time
            if time_running.seconds > timeout_seconds:
                raise Exception("Timeout")

if __name__=='__main__':
    unittest.main()
