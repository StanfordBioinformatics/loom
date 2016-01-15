#!/usr/bin/env python

import os
import unittest
from datetime import datetime
import time

from loom.client import submit
from loom.common.testserver import TestServer

class TestSubmit(unittest.TestCase):

    TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'testdata')

    def setUp(self):
        self.test_server = TestServer()
        self.test_server.start()

    def tearDown(self):
        self.test_server.stop()

    def test_run(self):
        run_parser = submit.Submit.get_parser()
        args = run_parser.parse_args([os.path.join(self.TEST_DATA_DIR, 'invalid_pipeline.json')])
        lsubmit = submit.Submit(args=args)
        with self.assertRaises(submit.SubmitWorkflowException):
            lsubmit.run()

if __name__=='__main__':
    unittest.main()
