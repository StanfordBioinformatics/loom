from analysis.models import *
from django.conf import settings
from django.test import TestCase
import os
import sys
from xppf.common import fixtures
from xppf.common.fixtures.workflows import hello_world
from .common import ImmutableModelsTestCase


class TestModelsRunRequests(ImmutableModelsTestCase):

    def testRequestDockerImage(self):
        o = RequestDockerImage.create(fixtures.docker_image_obj)
        self.assertEqual(o.docker_image, fixtures.docker_image_obj['docker_image'])
        self.roundTripJson(o)
        self.roundTripObj(o)

    def testRequestEnvironment(self):
        o = RequestEnvironment.create(fixtures.docker_image_obj)
        self.assertEqual(o.docker_image, fixtures.docker_image_obj['docker_image'])
        self.roundTripJson(o)
        self.roundTripObj(o)

    def testRequestInputPort(self):
        o = RequestInputPort.create(fixtures.input_port_1a_obj)
        self.assertEqual(o.name, fixtures.input_port_1a_obj['name'])
        self.roundTripJson(o)
        self.roundTripObj(o)

    def testRequestOutputPort(self):
        o = RequestOutputPort.create(fixtures.output_port_1_obj)
        self.assertEqual(o.name, fixtures.output_port_1_obj['name'])
        self.roundTripJson(o)
        self.roundTripObj(o)

    def testRequestDataBindingInputPortIdentifier(self):
        o = RequestDataBindingDestinationPortIdentifier.create(fixtures.port_identifier_obj)
        self.assertEqual(o.step, fixtures.port_identifier_obj['step'])
        self.roundTripJson(o)
        self.roundTripObj(o)

    def testRequestDataPipeSourcePortIdentifier(self):
        o = RequestDataPipeSourcePortIdentifier.create(fixtures.port_identifier_obj)
        self.assertEqual(o.step, fixtures.port_identifier_obj['step'])
        self.roundTripJson(o)
        self.roundTripObj(o)

    def testRequestDataPipeDestinationPortIdentifier(self):
        o = RequestDataPipeDestinationPortIdentifier.create(fixtures.port_identifier_obj)
        self.assertEqual(o.step, fixtures.port_identifier_obj['step'])
        self.roundTripJson(o)
        self.roundTripObj(o)

    def testRequestDataBinding(self):
        o = RequestDataBinding.create(fixtures.data_binding_obj)
        self.assertEqual(o.destination.step, fixtures.data_binding_obj['destination']['step'])
        self.roundTripJson(o)
        self.roundTripObj(o)

    def testRequestDataPipe(self):
        o = RequestDataPipe.create(fixtures.data_pipe_obj)
        self.assertEqual(o.source.step, fixtures.data_pipe_obj['source']['step'])
        self.roundTripJson(o)
        self.roundTripObj(o)

    def testRequestResourceSet(self):
        o = RequestResourceSet.create(fixtures.resource_set_obj)
        self.assertEqual(o.cores, fixtures.resource_set_obj['cores'])
        self.roundTripJson(o)
        self.roundTripObj(o)

    def testStep(self):
        o = Step.create(fixtures.step_1_obj)
        self.assertEqual(o.name, fixtures.step_1_obj['name'])
        self.roundTripJson(o)
        self.roundTripObj(o)

    def testWorkflow(self):
        o = Workflow.create(fixtures.workflow_obj)
        self.assertEqual(o.steps.count(), len(fixtures.workflow_obj['steps']))
        self.roundTripJson(o)
        self.roundTripObj(o)

    def testRunRequest(self):
        o = RunRequest.create(fixtures.run_request_obj)
        self.assertEqual(o.workflows.count(), len(fixtures.run_request_obj['workflows']))
        self.roundTripJson(o)
        self.roundTripObj(o)

class TestWorkflow(TestCase):
    def setUp(self):
        self.workflow = Workflow.create(fixtures.workflow_obj)
    
    def testGetStep(self):
        step1 = self.workflow.get_step('step1')
        self.assertEqual(step1.name, fixtures.step_1_obj['name'])

class TestRequestInputPort(TestCase):
    pass

        
class TestStep(TestCase):
    def setUp(self):
        self.workflow = Workflow.create(fixtures.workflow_obj)
        self.step1 = self.workflow.get_step('step1')
        self.step2 = self.workflow.get_step('step2')
        
    def testGetInputPort(self):
        port1 = self.step1.get_input_port('input_port1a')
        self.assertEqual(port1.name, 'input_port1a')

    def testGetOutputPort(self):
        port1 = self.step1.get_output_port('output_port1')
        self.assertEqual(port1.name, 'output_port1')


class TestRunRequests(TestCase):

    def testRunRequestsReverseSorted(self):
        count = 5
        for i in range(count):
            RunRequest.create(fixtures.run_request_obj)
        r_list = RunRequest.get_sorted()
        for i in range(1, count):
            self.assertTrue(r_list[i-1].datetime_created > r_list[i].datetime_created)

    def testRunRequestNoCount(self):
        count = 5
        for i in range(count):
            RunRequest.create(fixtures.run_request_obj)
        r_list = RunRequest.get_sorted()
        self.assertEqual(len(r_list), count)

    def testRunRequestWithCount(self):
        count = 5
        for i in range(count):
            RunRequest.create(fixtures.run_request_obj)

        r_list_full = RunRequest.get_sorted()
        r_list_truncated = RunRequest.get_sorted(count-1)
        r_list_untruncated = RunRequest.get_sorted(count+1)

        # Truncated list should start with the newest record
        self.assertEqual(r_list_full[0].datetime_created, r_list_truncated[0].datetime_created)

        # Length should match count
        self.assertEqual(len(r_list_truncated), count-1)

        # If count is greater than available elements, all elements should be present
        self.assertEqual(len(r_list_untruncated), count)

"""
class TestOversimplifiedInputManager(TestCase):
    
    def test_init_on_step(self):
        step = Step.create(fixtures.step_1_obj)
        self.assertTrue(hasattr(step, 'input_set_manager'))

#    def test_are_step_runs_pending_for_data_object(self):
#        run_request = RunRequest(fixtures.hello_world_obj)
#        run_request.workflows.first()
            
#    def test_are_step_runs_pending_for_data_pipe(self):
#        pass

#    def test_get_available_input_sets_for_data_object(self):
#        pass

#    def test_get_aviailable_input_sets_for_data_pipe(self):
#        pass


class TestInputSet(TestCase):
    
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
        self.world_step_run.update({'step_results': [world_result.to_serializable_obj()]})

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
        self.hello_world_step_input_set.add_input('world_in', self.world_step_run.get_output_ports()[0])

    def _create_world_step_input_set(self):
        self.world_step_input_set = InputSet(self.workflow.get_step('world_step'))
"""
