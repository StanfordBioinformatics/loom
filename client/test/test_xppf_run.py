#!/usr/bin/env python

import os
import unittest
from datetime import datetime
import time

from xppf.client import xppf_server_controls
from xppf.client import xppf_run
from xppf.master.utils.testserver import TestServer

class TestXppfRun(unittest.TestCase):

    TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'testdata')

    def setUp(self):
        self.test_server = TestServer()
        self.test_server.start()

    def tearDown(self):
        self.test_server.stop()

    def test_run(self):
        run_parser = xppf_run.XppfRun._get_parser()
        args = run_parser.parse_args([os.path.join(self.TEST_DATA_DIR, 'invalid_pipeline.json')])
        xrun = xppf_run.XppfRun(args=args)
        with self.assertRaises(xppf_run.XppfRunException):
            xrun.run()

if __name__=='__main__':
    unittest.main()
