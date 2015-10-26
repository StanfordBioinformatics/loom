from analysis.models import *
from django.conf import settings
from django.test import TestCase
import os
import sys
sys.path.append(os.path.join(settings.BASE_DIR, '../../..'))
from xppf.common import fixtures
from xppf.common.fixtures.workflows import hello_world

from .common import ImmutableModelsTestCase

class SetupHelper:

    def _create_world_step_run(self, link_to_step=True):
        world_step = self.workflow.get_step('world_step')
        self.world_step_run = world_step.create_or_get_step_run(self.world_step_input_set)

    def _create_world_step_result(self):
        world_result = StepResult.create(
            {
                'data_object': hello_world.world_file,
                'output_port': self.world_step_run.output_ports.first().to_serializable_obj(),
                }
            )
        self._create_world_file_storage_location()

    def _create_world_file_storage_location(self):
        FileStorageLocation.create({
                'file_contents': hello_world.world_file['file_contents'],
                'host_url': 'localhost',
                'file_path': '~/world.txt'
                })

    def _create_hello_world_file_storage_location(self):
        FileStorageLocation.create({
                'file_contents': hello_world.hello_file['file_contents'],
                'host_url': 'localhost',
                'file_path': '~/hello_world.txt'
                })

    def _create_hello_world_step_input_set(self):
        self.hello_world_step_input_set = InputSet(self.workflow.get_step('hello_world_step'))
        self.hello_world_step_input_set.add_input('hello_in', File.create(hello_world.hello_file))
        self.hello_world_step_input_set.add_input('world_in', self.world_step_run.output_ports.first())

    def _create_world_step_input_set(self):
        self.world_step_input_set = InputSet(self.workflow.get_step('world_step'))


class TestInputSet(TestCase, SetupHelper):
    
    def setUp(self):
        self.workflow = Workflow.create(hello_world.hello_world_workflow)

    def test_is_data_ready_no_input_ports(self):
        self._create_world_step_input_set()
        self.assertTrue(self.world_step_input_set.is_data_ready())

    def test_is_data_ready_no_file_location(self):
        self._create_world_step_input_set()
        self._create_world_step_run()
        self._create_world_step_result()
        self._create_hello_world_step_input_set()

        # File without a FileStorageLocation is not ready
        self.assertFalse(self.hello_world_step_input_set.is_data_ready())

        # But with a location, it is ready
        self._create_hello_world_file_storage_location()
        self.assertTrue(self.hello_world_step_input_set.is_data_ready())

    def test_is_data_ready_no_run_result(self):
        self._create_world_step_input_set()
        self._create_world_step_run()
        self._create_hello_world_file_storage_location()
        self._create_hello_world_step_input_set()

        # StepRunPort without result is not ready
        self.assertFalse(self.hello_world_step_input_set.is_data_ready())

        # But with a result, it is ready
        self._create_world_step_result()
        self._create_hello_world_step_input_set()
        self.assertTrue(self.hello_world_step_input_set.is_data_ready())

    def test_create_step_run_no_inputs(self):
        self._create_world_step_input_set()
        world_step = self.workflow.get_step('world_step')

        self.assertEqual(world_step.step_runs.count(), 0)
        world_step.create_or_get_step_run(self.world_step_input_set)
        self.assertEqual(world_step.step_runs.count(), 1)

        # Recreating should have no effect
        world_step.create_or_get_step_run(self.world_step_input_set)
        self.assertEqual(world_step.step_runs.count(), 1)
        
    def test_create_step_run_with_inputs(self):
        self._create_world_step_input_set()
        self._create_world_step_run()
        self._create_world_step_result()
        self._create_hello_world_step_input_set()
        self._create_hello_world_file_storage_location()
        hello_world_step = self.workflow.get_step('hello_world_step')

        self.assertEqual(hello_world_step.step_runs.count(), 0)
        hello_world_step.create_or_get_step_run(self.hello_world_step_input_set)
        self.assertEqual(hello_world_step.step_runs.count(), 1)

        # Recreating should have no effect
        hello_world_step.create_or_get_step_run(self.hello_world_step_input_set)
        self.assertEqual(hello_world_step.step_runs.count(), 1)

    def test_create_step_run_not_linked_to_step(self):
        self._create_world_step_input_set()
        self._create_world_step_run()
        self.world_step_run.steps = []

        self.assertEqual(self.workflow.get_step('world_step').step_runs.count(), 0)
        self.workflow.get_step('world_step').create_or_get_step_run(self.world_step_input_set)
        self.assertEqual(self.workflow.get_step('world_step').step_runs.count(), 1)


class TestOversimplifiedInputManager(TestCase, SetupHelper):

    def setUp(self):
        self.workflow = Workflow.create(hello_world.hello_world_workflow)
    
    def test_init_on_step(self):
        step = Step.create(fixtures.step_1_obj)
        self.assertTrue(hasattr(step, 'input_set_manager'))

    def test_are_step_runs_pending(self):
        step = self.workflow.get_step('world_step')
        self.assertTrue(step.input_set_manager.are_step_runs_pending())

    def test_get_available_input_sets_no_inputs(self):
        step = self.workflow.get_step('world_step')
        input_sets = step.input_set_manager.get_available_input_sets()
        self.assertEqual(len(input_sets), 1)
        self.assertEqual(len(input_sets[0].inputs), 0)

    def test_get_available_input_sets_with_inputs(self):
        self._create_world_step_input_set()
        self._create_world_step_run()
        self._create_world_step_result()
        step = self.workflow.get_step('hello_world_step')
        input_sets = step.input_set_manager.get_available_input_sets()
        self.assertEqual(len(input_sets), 1)
        self.assertEqual(len(input_sets[0].inputs), 2)


