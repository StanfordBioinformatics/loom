from django.test import TestCase, override_settings
import yaml

from .test_templates import get_workflow
from api.models.data_objects import *
from api.models.runs import Run
from api.models.input_manager import InputManager
from api.serializers import RunRequestSerializer
from api.test.helper import make_run_request_from_template_file

def get_workflow_run():
    wf = get_workflow()
    return Run.create_from_template(wf)

class TestWorkflowRun(TestCase):

    def testCreate(self):
        with self.settings(TEST_DISABLE_ASYNC_DELAY=True,
                           TEST_NO_PUSH_INPUTS_ON_RUN_CREATION=True):
            workflow_run = get_workflow_run()
        self.assertTrue(workflow_run.name == 'one_two')
        self.assertTrue(
            workflow_run.steps.get(name='step_one')\
            .inputs.get(channel='one')\
            .is_connected(
                workflow_run.inputs.get(channel='one')))


class TestInputManager(TestCase):

    def testSimple(self):
        with self.settings(TEST_DISABLE_ASYNC_DELAY=True, TEST_NO_CREATE_TASK=True):
            run_request = make_run_request_from_template_file(
                os.path.join(os.path.dirname(__file__), '..', '..', 'test',
                             'fixtures', 'simple', 'simple.yaml'),
                word_in='puppy')

        sets = InputManager(run_request.run.inputs.all(), 'word_in', [])\
               .get_input_sets()

        self.assertEqual(len(sets), 1)
        self.assertEqual(sets[0].data_path, [])
        input_items = [item for item in sets[0]]
        self.assertEqual(len(input_items), 1)
        self.assertEqual(input_items[0].channel, 'word_in')
