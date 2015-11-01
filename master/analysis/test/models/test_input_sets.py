import os
import sys

from django.conf import settings
from django.test import TestCase

from analysis.models import *
from loom.common import fixtures
from loom.common.fixtures.workflows import hello_world


class FakeSource(object):

    def is_available(self):
        return True

    def get_data_object(self):
        return TestInputSet.GET_DATA_OBJECT_OUTPUT

class FakeStepRun(object):

    def get_output_port(self, name):
        return 0

class FakeQuerySet(object):

    def __init__(self, list_):
        self.list = list_

    def all(self):
        return self.list

    def count(self):
        return len(self.list)

    def first(self):
        return self.list[0]

class FakeStep(object):

    def __init__(self, step_runs=None, name='stepname',
                 are_step_runs_pending=False):
        self.step_runs = step_runs
        self.name = name
        self.are_step_runs_pending_value=are_step_runs_pending

    def are_step_runs_pending(self):
        return self.are_step_runs_pending_value

class FakeDataBinding(object):

    def get_data_object(self):
        return "dummy_data_object"

class FakeRequestInputPort(object):

    def __init__(self, 
                 has_parallel_inputs=True, 
                 is_from_same_source_step=True, 
                 source_step=None, 
                 source_port=None,
                 name='fakeport',
                 has_data_binding=False):
        self.has_parallel_inputs_value = has_parallel_inputs
        self.is_from_same_source_step_value = \
            is_from_same_source_step
        self.source_step_value = source_step
        self.source_port_value = source_port
        self.name = name
        self.has_data_binding_value = has_data_binding

    def has_parallel_inputs(self):
        return self.has_parallel_inputs_value

    def is_from_same_source_step(self, port):
        return self.is_from_same_source_step_value
    
    def has_data_binding(self):
        return self.has_data_binding_value

    def get_source_step(self):
        return self.source_step_value

    def get_source(self):
        return self.source_port_value

    def _get_data_binding(self):
        return FakeDataBinding()

class FakeRequestOutputPort(object):

    name = 'fakeport'

    def __init__(self, step_run_ports=None):
        self.step_run_ports_value = step_run_ports

    def get_step_run_ports(self):
        return self.step_run_ports_value

class TestInputSet(TestCase):

    PORT_NAME = 'port1'
    GET_DATA_OBJECT_OUTPUT = 'GET_DATA_OBJECT_OUTPUT'

    def setUp(self):
        self.input_set = InputSet()
        self.input_set.add_input(self.PORT_NAME, FakeSource())

    def test_add_input_duplicate(self):
        """Multiple inputs with the same name are not allowed"""
        with self.assertRaises(Exception):
            self.input_set.add_input(self.PORT_NAME, FakeSource())

    def test_init(self):
        self.assertTrue(isinstance(self.input_set.inputs, dict))

    def test_is_data_ready(self):
        self.assertTrue(self.input_set.is_data_ready())

    def test_get_data_object(self):
        data_object = self.input_set.get_data_object(self.PORT_NAME)
        self.assertEqual(data_object, self.GET_DATA_OBJECT_OUTPUT)

    def test_source_methods(self):
        """Verifies that required methods exist on source."""
        for source_model in [DataObject, StepRunOutputPort]:
            for method in ['is_available', 'get_data_object']:
                self.assertTrue(hasattr(source_model, method))
        

class TestAbstractInputSetManager(TestCase):

    dummy_step = 'DUMMY_STEP'

    def setUp(self):
        self.input_set_manager = AbstractInputSetManager(self.dummy_step)

    def test_init(self):
        self.assertEqual(self.input_set_manager.step, self.dummy_step)

    def test_are_previous_steps_pending(self):
        with self.assertRaises(Exception):
            self.input_set_manager.are_previous_steps_pending()

    def test_get_available_input_sets(self):
        with self.assertRaises(Exception):
            self.input_set_manager.get_available_input_sets()


class TestInputlessInputSetManager(TestCase):

    def setUp(self):
        dummy_step = 'dummy'
        self.input_set_manager = InputlessInputSetManager(dummy_step)
        
    def test_are_previous_steps_pending(self):
        self.assertFalse(self.input_set_manager.are_previous_steps_pending())

    def test_get_available_input_sets(self):
        self.assertEqual(self.input_set_manager.get_available_input_sets(), [])
    
class TestSimpleInputSetManager(TestCase):

    def setUp(self):
        self.request = RunRequest.create(fixtures.hello_world_run_request_obj)
        self.step = self.request.workflows.first().get_step('hello_world_step')
        self.input_set_manager = InputlessInputSetManager(self.step)

    def test_init(self):
        input_set_manager = SimpleInputSetManager(self.step)
        self.assertEqual(input_set_manager.step._id, self.step._id)
        self.assertEqual(len(input_set_manager.input_ports), 
                         self.step.input_ports.count())
        self.assertTrue(isinstance(
                input_set_manager.parallel_input_ports, list))
        self.assertTrue(isinstance(
                    input_set_manager.nonparallel_input_ports, list))
                    
    def test_classify_parallel_ports(self):

        parallel_port1 = FakeRequestInputPort(has_parallel_inputs=True)
        parallel_port2 = FakeRequestInputPort(has_parallel_inputs=True)
        nonparallel_port = FakeRequestInputPort(has_parallel_inputs=False)
        input_set_manager = SimpleInputSetManager(
            'dummy_step', skip_init_for_testing=True)
        input_set_manager.input_ports = [parallel_port1,
                                         parallel_port2, 
                                         nonparallel_port]
        input_set_manager._classify_parallel_ports()
        self.assertTrue(parallel_port1 in 
                        input_set_manager.parallel_input_ports)
        self.assertTrue(parallel_port2 in 
                        input_set_manager.parallel_input_ports)
        self.assertTrue(nonparallel_port in 
                        input_set_manager.nonparallel_input_ports)

    def test_valiate_parallel_input_port(self):
        parallel_port1 = FakeRequestInputPort(has_parallel_inputs=True)
        parallel_port2 = FakeRequestInputPort(has_parallel_inputs=True, 
                                  is_from_same_source_step=False)
        input_set_manager = SimpleInputSetManager(
            'dummy_step', skip_init_for_testing=True)
        input_set_manager.input_ports = [parallel_port1,
                                         parallel_port2]
        with self.assertRaises(Exception):
            input_set_manager._classify_parallel_ports()

    def test_add_parallel_input_port(self):
        # Covered by test_classify_parallel_ports
        pass

    def test_add_nonparallel_input_port(self):
        # Covered by test_classify_parallel_ports
        pass

    def test_get_available_input_sets_nonparallel(self):
        step_runs = [FakeStepRun()]
        step1 = FakeStep(step_runs=FakeQuerySet(step_runs))
        step2 = FakeStep(step_runs=FakeQuerySet(step_runs))
        step_run_output_ports = ['dummy']
        source_port = FakeRequestOutputPort(
            step_run_output_ports)
        port1 = FakeRequestInputPort(
            source_step=step1, 
            source_port=source_port,
            has_parallel_inputs=False,
            name='port1')
        port2 = FakeRequestInputPort(
            source_step=step2,
            source_port=source_port,
            has_parallel_inputs=False,
            has_data_binding=True,
            name='port2')
        input_set_manager = SimpleInputSetManager(
            'dummy_step', skip_init_for_testing=True)
        input_set_manager.nonparallel_input_ports = [port1,
                                                  port2]
        input_set_manager.parallel_input_ports = []
        sets = input_set_manager.get_available_input_sets()
        self.assertTrue('port1' in sets[0].inputs.keys())
        self.assertTrue('port2' in sets[0].inputs.keys())

    def test_get_available_input_sets_parallel(self):
        step_runs = [FakeStepRun()]
        step1 = FakeStep(step_runs=FakeQuerySet(step_runs))
        step2 = FakeStep(step_runs=FakeQuerySet(step_runs))
        step_run_output_ports = ['dummy']
        source_port = FakeRequestOutputPort(
            step_run_output_ports)
        port1 = FakeRequestInputPort(
            source_step=step1, 
            source_port=source_port,
            has_parallel_inputs=True,
            name='port1')
        port2 = FakeRequestInputPort(
            source_step=step2,
            source_port=source_port,
            has_parallel_inputs=True,
            name='port2')
        input_set_manager = SimpleInputSetManager(
            'dummy_step', skip_init_for_testing=True)
        input_set_manager.parallel_input_ports = [port1,
                                                  port2]
        input_set_manager.nonparallel_input_ports = []
        sets = input_set_manager.get_available_input_sets()
        self.assertTrue('port1' in sets[0].inputs.keys())
        self.assertTrue('port2' in sets[0].inputs.keys())

    def test_get_all_source_steps(self):
        step1 = FakeStep(name='step1')
        port1 = FakeRequestInputPort(
            source_step=step1, 
            has_parallel_inputs=False,
            name='port1')
        input_set_manager = SimpleInputSetManager(
            'dummy_step', skip_init_for_testing=True)
        input_set_manager.input_ports = [port1]
        source_steps = input_set_manager._get_all_source_steps()
        self.assertEqual(source_steps[0].name, 'step1')

    def test_are_previous_steps_pending(self):
        step1 = FakeStep(name='step1',
                         are_step_runs_pending=True)
        port1 = FakeRequestInputPort(
            source_step=step1, 
            has_parallel_inputs=False,
            name='port1')
        input_set_manager = SimpleInputSetManager(
            'dummy_step', skip_init_for_testing=True)
        input_set_manager.input_ports = [port1]
        self.assertTrue(input_set_manager.are_previous_steps_pending())

    def test_classify_parallel_ports_external_methods(self):
        """For methods implemented in Fake classes, make sure they exist
        on the real classes
        """
        self.assertTrue(hasattr(StepRunOutputPort, 'is_available'))
        self.assertTrue(hasattr(StepRunOutputPort, 'get_data_object'))

        self.assertTrue(hasattr(DataObject, 'is_available'))
        self.assertTrue(hasattr(DataObject, 'get_data_object'))

        self.assertTrue(hasattr(StepRun, 'get_output_port'))

        self.assertTrue(hasattr(Step, 'are_step_runs_pending'))
        self.assertTrue(hasattr(Step, 'step_runs'))
        self.assertTrue(Step._meta.get_field_by_name('name'))

        self.assertTrue(hasattr(RequestDataBinding, 'get_data_object'))

        self.assertTrue(RequestInputPort._meta.get_field_by_name('name'))
        self.assertTrue(hasattr(RequestInputPort, 'has_parallel_inputs'))
        self.assertTrue(hasattr(RequestInputPort, 'is_from_same_source_step'))
        self.assertTrue(hasattr(RequestInputPort, 'has_data_binding'))
        self.assertTrue(hasattr(RequestInputPort, 'get_source_step'))
        self.assertTrue(hasattr(RequestInputPort, 'get_source'))
        self.assertTrue(hasattr(RequestInputPort, '_get_data_binding'))

        self.assertTrue(RequestOutputPort._meta.get_field_by_name('name'))
        self.assertTrue(hasattr(RequestOutputPort, 'get_step_run_ports'))
        
class TestInputSetManagerFactory(TestCase):
    pass
