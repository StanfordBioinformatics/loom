from django.test import TestCase, override_settings
import yaml

from api.test.models.test_templates import get_workflow
from api.models.data_objects import *
from api.models.runs import Run
from api.models.input_calculator import InputCalculator
from api.test.helper import request_run_from_template_file

def get_run():
    wf = get_workflow()
    run = Run.create_from_template(wf)
    run.initialize_inputs()
    run.initialize_outputs()
    run.initialize()
    for step in run.steps.all():
        step.initialize()
    return run

class TestWorkflowRun(TestCase):

    def testCreate(self):
        with self.settings(TEST_DISABLE_ASYNC_DELAY=True,
                           TEST_NO_PUSH_INPUTS_ON_RUN_CREATION=True):
            run = get_run()
        self.assertTrue(run.name == 'one_two')
        self.assertTrue(
            run.steps.get(name='step_one')\
            .inputs.get(channel='one')\
            .is_connected(
                run.inputs.get(channel='one')))


class TestInputCalculator(TestCase):

    def testSimple(self):
        with self.settings(TEST_DISABLE_ASYNC_DELAY=True, TEST_NO_CREATE_TASK=True):
            run = request_run_from_template_file(
                os.path.join(os.path.dirname(__file__), '..', '..', 'test',
                             'fixtures', 'simple', 'simple.yaml'),
                word_in='puppy')

        sets = InputCalculator(run.inputs.all(), 'word_in', [])\
               .get_input_sets()

        self.assertEqual(len(sets), 1)
        self.assertEqual(sets[0].data_path, [])
        input_items = [item for item in sets[0]]
        self.assertEqual(len(input_items), 1)
        self.assertEqual(input_items[0].channel, 'word_in')
