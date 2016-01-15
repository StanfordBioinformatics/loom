from analysis.models import *
from django.conf import settings
from django.test import TestCase
import os
import sys
from loom.common import fixtures
from loom.common.fixtures.workflows import hello_world
from .common import ImmutableModelsTestCase


class TestModelsWorkflows(ImmutableModelsTestCase):

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

class TestWorkflow(TestCase):
    
    def testGetStep(self):
        self.workflow = Workflow.create(fixtures.workflow_obj)
        step1 = self.workflow.get_step('step1')
        self.assertEqual(step1.name, fixtures.step_1_obj['name'])

    def testWorkflowsReverseSorted(self):
        count = 5
        for i in range(count):
            Workflow.create(fixtures.workflow_obj)
        wf_list = Workflow.get_sorted()
        for i in range(1, count):
            self.assertTrue(wf_list[i-1].datetime_created > wf_list[i].datetime_created)

    def testWorkflowNoCount(self):
        count = 5
        for i in range(count):
            Workflow.create(fixtures.workflow_obj)
        wf_list = Workflow.get_sorted()
        self.assertEqual(len(wf_list), count)

    def testWorkflowWithCount(self):
        count = 5
        for i in range(count):
            Workflow.create(fixtures.workflow_obj)

        wf_list_full = Workflow.get_sorted()
        wf_list_truncated = Workflow.get_sorted(count-1)
        wf_list_untruncated = Workflow.get_sorted(count+1)

        # Truncated list should start with the newest record
        self.assertEqual(wf_list_full[0].datetime_created, wf_list_truncated[0].datetime_created)

        # Length should match count
        self.assertEqual(len(wf_list_truncated), count-1)

        # If count is greater than available elements, all elements should be present
        self.assertEqual(len(wf_list_untruncated), count)

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
