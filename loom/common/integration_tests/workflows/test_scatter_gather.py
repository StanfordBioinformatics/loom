import os
from loom.common.fixtures import *
from loom.common.integration_tests.workflows.abstract_workflow_tester import AbstractWorkflowTester

array_in_json_path = os.path.join(
    os.path.dirname(__file__), 
    '../../../common/fixtures/workflows/scatter_gather/scatter_gather.json')

class TestScatterGatherWorkflow(AbstractWorkflowTester):
    pass
    """
    def setUp(self):

        self.start_server()
        self.start_job(array_in_json_path)
        self.wait_for_job()

    def tearDown(self):
        self.stop_server()

    def testWorkflow(self):
        self.assertTrue(True)
    """
