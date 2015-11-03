#!/usr/bin/env python

import os
import unittest
from datetime import datetime
import time

from loom.client import loom_server_controls
from loom.client import loom_submit
from loom.common.testserver import TestServer

class TestLoomSubmit(unittest.TestCase):

    TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'testdata')

    def setUp(self):
        self.test_server = TestServer()
        self.test_server.start()

    def tearDown(self):
        self.test_server.stop()

    def test_run(self):
        run_parser = loom_submit.LoomSubmit.get_parser()
        args = run_parser.parse_args([os.path.join(self.TEST_DATA_DIR, 'invalid_pipeline.json')])
        lsubmit = loom_submit.LoomSubmit(args=args)
        with self.assertRaises(loom_submit.LoomSubmitException):
            lsubmit.run()

if __name__=='__main__':
    unittest.main()
