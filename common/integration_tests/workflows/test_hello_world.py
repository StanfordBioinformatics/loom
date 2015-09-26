import os
import sys
sys.path.append(
    os.path.join(os.path.dirname(__file__), 
                 '../../../..'))

from xppf.common.fixtures import *
from xppf.common.integration_tests.workflows.abstract_workflow_tester import AbstractWorkflowTester

helloworld_json_path = os.path.join(
    os.path.dirname(__file__), 
    '../../../../xppf/doc/examples/helloworld/helloworld.json')

hello_file = os.path.join(
    os.path.dirname(__file__), 
    '../../../../xppf/doc/examples/helloworld/hello.txt')

class TestHelloWorldWorkflow(AbstractWorkflowTester):

    def setUp(self):

        self.start_server()
        self.upload(hello_file)
        self.start_job(helloworld_json_path)
        self.wait_for_job()

    def tearDown(self):
        self.stop_server()

    def testWorkflow(self):
        self.assertTrue(True)
