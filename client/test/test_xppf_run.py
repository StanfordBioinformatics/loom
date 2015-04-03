#!/usr/bin/env python

import os
import unittest
from datetime import datetime
import time

from xppf.client import xppf_server_controls
from xppf.client import xppf_run

class TestXppfRun(unittest.TestCase):

    TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'testdata')

    def setUp(self):
        xsc_parser = xppf_server_controls.XppfServerControls._get_parser()
        args = xsc_parser.parse_args(['start', '--require_default_settings'])
        xs = xppf_server_controls.XppfServerControls(args=args)
        xs.main()
        self.wait_for_true(lambda: os.path.exists(xs.settings_manager.get_pid_file()))

    def tearDown(self):
        xsc_parser = xppf_server_controls.XppfServerControls._get_parser()
        args = xsc_parser.parse_args(['stop', '--require_default_settings'])
        xs = xppf_server_controls.XppfServerControls(args=args)
        xs.main()
        self.wait_for_true(lambda: not os.path.exists(xs.settings_manager.get_pid_file()))

    def test_run(self):
        run_parser = xppf_run.XppfRun._get_parser()
        args = run_parser.parse_args([os.path.join(self.TEST_DATA_DIR, 'invalid_pipeline.json')])
        xrun = xppf_run.XppfRun(args=args)
        with self.assertRaises(xppf_run.XppfRunException):
            xrun.run()

    def wait_for_true(self, test_method, timeout_seconds=5):
        start_time = datetime.now()
        while not test_method():
            time.sleep(timeout_seconds/10.0)
            time_running = datetime.now() - start_time
            if time_running.seconds > timeout_seconds:
                raise Exception("Timeout")

if __name__=='__main__':
    unittest.main()
