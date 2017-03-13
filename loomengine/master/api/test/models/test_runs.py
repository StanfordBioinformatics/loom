from django.test import TestCase
from api.models.data_objects import *
from api.models.runs import *
from api.test.models.test_templates import get_workflow

def get_workflow_run():
    wf = get_workflow()
    return Run.create_from_template(wf)

class TestWorkflowRun(TestCase):

    def testCreate(self):
        with self.settings(TEST_DISABLE_TASK_DELAY=True):
            workflow_run = get_workflow_run()
        self.assertTrue(workflow_run.name == 'one_two')
        self.assertTrue(
            workflow_run.steps.get(name='step_one')\
            .inputs.get(channel='one')\
            .is_connected(
                workflow_run.inputs.get(channel='one')))
        
