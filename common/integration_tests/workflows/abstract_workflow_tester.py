import unittest
from xppf.client import xppf_run, xppf_upload
from xppf.common.helper import Helper
from xppf.common.testserver import TestServer

class AbstractWorkflowTester(unittest.TestCase):

    def is_workflow_complete(self):
        response = self.runner.get('/api/dashboard/')
        if not response.status_code == 200:
            return False
        run_requests = response.json().get('run_requests')
        r = filter(lambda r, id=self.request_id: r['id']==id, run_requests)
        if not len(r) == 1:
            return False
        r = r[0]
        return r.get('is_complete')

    def start_server(self):
        self.test_server = TestServer()
        self.test_server.start(no_daemon=False)

    def start_job(self, run_request_json_path):
        run_parser = xppf_run.XppfRun.get_parser()
        args = run_parser.parse_args(['--require_default_settings', run_request_json_path])
        self.runner = xppf_run.XppfRun(args=args)
        response = self.runner.run()
        self.assertEqual(response.status_code, 201)
        self.request_id = response.json().get('_id')
        
    def upload(self, file_path):
        upload_parser = self.uploader = xppf_upload.XppfUpload.get_parser()
        args = upload_parser.parse_args(['--require_default_settings', file_path])
        uploader = xppf_upload.XppfUpload(args=args)
        uploader.run()

    def wait_for_job(self):
        Helper.wait_for_true(self.is_workflow_complete, timeout_seconds=20)

    def stop_server(self):
        self.test_server.stop()
