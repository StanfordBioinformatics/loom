import json
import unittest
from loom.common import helper
from loom.common.testserver import TestServer

class AbstractWorkflowTester(unittest.TestCase):

    def is_workflow_complete(self):
        response = self.runner.get('/api/dashboard/')
        if not response.status_code == 200:
            return False
        workflows = response.json().get('workflows')
        r = filter(lambda r, id=self.workflow_id: r['id']==id, workflows)
        if not len(r) == 1:
            return False
        r = r[0]
        return r.get('are_results_complete')

    def start_server(self):
        self.test_server = TestServer()
        self.test_server.start()

    def start_job(self, workflow_json_path):
        run_parser = submit.Submit.get_parser()
        args = run_parser.parse_args(['--require_default_settings', workflow_json_path])
        self.runner = submit.Submit(args=args)
        response = self.runner.run()
        self.assertEqual(response.status_code, 201)
        self.workflow_id = response.json().get('_id')
        
    def wait_for_job(self):
        helper.wait_for_true(self.is_workflow_complete, timeout_seconds=30, sleep_interval=3)

    def stop_server(self):
        self.test_server.stop()
