import os
import unittest

from loom.common.integration_tests.workflows.abstract_workflow_tester import AbstractWorkflowTester
from .fixtures import *

hello_world_json_path = os.path.join(
    os.path.dirname(__file__), 
    '../../../../doc/examples/hello_world/hello_world.json')

hello_file = os.path.join(
    os.path.dirname(__file__), 
    '../../../../doc/examples/hello_world/hello.txt')

class TestHelloWorldWorkflow(AbstractWorkflowTester):
    pass

    """
    def setUp(self):

        self.start_server()
        self.upload(hello_file)
        self.start_job(hello_world_json_path)
        self.wait_for_job()

    def tearDown(self):
        self.stop_server()

    def testWorkflow(self):
        self.assertTrue(True)
    """
    
if __name__ == '__main__':
    unittest.main()
