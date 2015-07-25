#!/usr/bin/env python

from datetime import datetime
import json
import os
import requests
import subprocess
import time
import unittest

from xppf.client import xppf_server_controls
from xppf.master.analysis.test import fixtures
from xppf.utils.testserver import TestServer
from xppf.worker.step_runner import StepRunner

class TestStepRunner(unittest.TestCase):

    def setUp(self):
        self.test_server = TestServer()
        self.test_server.start()
        self._run_helloworld()

    def tearDown(self):
        self.test_server.stop()

    def _run_helloworld(self):
        r = requests.post(self.test_server.server_url+'/api/submitrequest/', data=fixtures.helloworld_json)
        self.assertEqual(r.status_code, 201)
        self.test_server.dry_run_job_queues()

    # Given steprun ID, retrieve the steprun
    def test_get_step_run(self):
        r = requests.get(self.test_server.server_url+'/api/step_runs/')
        run_id = r.json()['step_runs'][0].get('_id')

        parser = StepRunner._get_parser()
        args = parser.parse_args(['--run_id', run_id, '--master_url', self.test_server.server_url, '--file_server', 'localhost', '--file_root', '.'])
        step_runner = StepRunner(args=args)
        step_runner.run()

    # Run the command

if __name__=='__main__':
    unittest.main()
