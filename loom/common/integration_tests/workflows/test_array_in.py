import os

from loom.common.fixtures import *
from loom.common.integration_tests.workflows.abstract_workflow_tester import AbstractWorkflowTester

array_in_json_path = os.path.join(
    os.path.dirname(__file__), 
    '../../../common/fixtures/workflows/array_in/array_in.json')

hello_file = os.path.join(
    os.path.dirname(__file__), 
    '../../../common/fixtures/workflows/array_in/hello.txt')

world_file = os.path.join(
    os.path.dirname(__file__), 
    '../../../common/fixtures/workflows/array_in/world.txt')

class TestArrayInWorkflow(AbstractWorkflowTester):
    pass
    """
    def setUp(self):

        self.start_server()
        self.upload(hello_file)
        self.upload(world_file)
        self.start_job(array_in_json_path)
        self.wait_for_job()

    def tearDown(self):
        self.stop_server()

    def testWorkflow(self):
        self.assertTrue(True)
    """
