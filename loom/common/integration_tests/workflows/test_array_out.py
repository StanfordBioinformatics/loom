import os

from loom.common.integration_tests.workflows.abstract_workflow_tester import AbstractWorkflowTester
from .fixtures import *

array_out_json_path = os.path.join(
    os.path.dirname(__file__), 
    '../../../common/fixtures/workflows/array_out/array_out.json')

class TestArrayInWorkflow(AbstractWorkflowTester):
    pass
    """
    def setUp(self):

        self.start_server()
        self.start_job(array_out_json_path)
        self.wait_for_job()

    def tearDown(self):
        self.stop_server()

    def testWorkflow(self):
        self.assertTrue(True)
    """
