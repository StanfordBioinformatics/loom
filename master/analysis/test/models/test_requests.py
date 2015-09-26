from django.conf import settings
from django.test import TestCase
import os
import sys

from analysis.models import *

sys.path.append(os.path.join(settings.BASE_DIR, '../../..'))
from xppf.common.fixtures import *

from .common import ImmutableModelsTestCase


class TestModelsRequestSubmissions(ImmutableModelsTestCase):

    def testRequestDockerImage(self):
        o = RequestDockerImage.create(docker_image_obj)
        self.assertEqual(o.docker_image, docker_image_obj['docker_image'])
        self.roundTripJson(o)
        self.roundTripObj(o)

    def testRequestEnvironment(self):
        o = RequestEnvironment.create(docker_image_obj)
        self.assertEqual(o.docker_image, docker_image_obj['docker_image'])
        self.roundTripJson(o)
        self.roundTripObj(o)

    def testRequestInputPort(self):
        o = RequestInputPort.create(input_port_obj_1)
        self.assertEqual(o.name, input_port_obj_1['name'])
        self.roundTripJson(o)
        self.roundTripObj(o)

    def testRequestOutputPort(self):
        o = RequestOutputPort.create(output_port_obj_1)
        self.assertEqual(o.name, output_port_obj_1['name'])
        self.roundTripJson(o)
        self.roundTripObj(o)

    def testRequestDataBindingPortIdentifier(self):
        o = RequestDataBindingPortIdentifier.create(port_identifier_obj)
        self.assertEqual(o.step, port_identifier_obj['step'])
        self.roundTripJson(o)
        self.roundTripObj(o)

    def testRequestDataPipeSourcePortIdentifier(self):
        o = RequestDataPipeSourcePortIdentifier.create(port_identifier_obj)
        self.assertEqual(o.step, port_identifier_obj['step'])
        self.roundTripJson(o)
        self.roundTripObj(o)

    def testRequestDataPipeDestinationPortIdentifier(self):
        o = RequestDataPipeDestinationPortIdentifier.create(port_identifier_obj)
        self.assertEqual(o.step, port_identifier_obj['step'])
        self.roundTripJson(o)
        self.roundTripObj(o)

    def testRequestDataBinding(self):
        o = RequestDataBinding.create(data_binding_obj)
        self.assertEqual(o.destination.step, data_binding_obj['destination']['step'])
        self.roundTripJson(o)
        self.roundTripObj(o)

    def testRequestDataPipe(self):
        o = RequestDataPipe.create(data_pipe_obj)
        self.assertEqual(o.source.step, data_pipe_obj['source']['step'])
        self.roundTripJson(o)
        self.roundTripObj(o)

    def testRequestResourceSet(self):
        o = RequestResourceSet.create(resource_set_obj)
        self.assertEqual(o.cores, resource_set_obj['cores'])
        self.roundTripJson(o)
        self.roundTripObj(o)

    def testStep(self):
        o = Step.create(step_obj_1)
        self.assertEqual(o.name, step_obj_1['name'])
        self.roundTripJson(o)
        self.roundTripObj(o)

    def testWorkflow(self):
        o = Workflow.create(workflow_obj)
        self.assertEqual(o.steps.count(), len(workflow_obj['steps']))
        self.roundTripJson(o)
        self.roundTripObj(o)

    def testRequestSubmission(self):
        o = RequestSubmission.create(request_submission_obj)
        self.assertEqual(o.workflows.count(), len(request_submission_obj['workflows']))
        self.roundTripJson(o)
        self.roundTripObj(o)

class TestWorkflow(TestCase):
    def setUp(self):
        self.workflow = Workflow.create(workflow_obj)
    
    def testGetStep(self):
        step1 = self.workflow.get_step('step1')
        self.assertEqual(step1.name, step_obj_1['name'])

class TestRequestInputPort(TestCase):
    def setUp(self):
        self.workflow = Workflow.create(workflow_obj)
        self.step1 = self.workflow.get_step('step1')
        self.step2 = self.workflow.get_step('step2')

    def testIsReadyBoundData(self):
        port1 = self.step1._get_input_port('input_port1')
        self.assertTrue(port1.has_file())

    def testIsReadyConnectedFile(self):
        port2 = self.step2._get_input_port('input_port2')
        self.assertFalse(port2.has_file())
        
class TestStep(TestCase):
    def setUp(self):
        self.workflow = Workflow.create(workflow_obj)
        self.step1 = self.workflow.get_step('step1')
        self.step2 = self.workflow.get_step('step2')
        
    def testIsReadyBoundData(self):
        # This step is not ready because although it already has 
        # a bound file, that file has no location
        self.assertFalse(self.step1._are_inputs_ready())

    def testIsReadyDataPipeNoFile(self):
        # This step is not ready because its input port has a data_pipe to the
        # previous step but no file exists.
        self.assertFalse(self.step2._are_inputs_ready())

    def testIsReadyDataPipeWithFile(self):
        # TODO

        # self.step1.create_step_run()
        # self.step1.post_result()
        # self.assertTrue(step2.is_ready())
        pass

    def testGetInputPort(self):
        port1 = self.step1._get_input_port('input_port1')
        self.assertEqual(port1.name, 'input_port1')

    def testGetOutputPort(self):
        port1 = self.step1._get_output_port('output_port1')
        self.assertEqual(port1.name, 'output_port1')

    def testRenderStepDefinition(self):
        step_definition = self.step1._render_step_definition()
        self.assertEqual(step_definition['template']['input_ports'][0]['file_path'], step_definition['data_bindings'][0]['input_port']['file_path'])

    def testCreateStepDefinition(self):
        step_definition = self.step1._create_step_definition()
        self.assertEqual(step_definition.template.input_ports.first().file_path, step_definition.data_bindings.first().input_port.file_path)

class TestRequestSubmissions(TestCase):

    def testRequestSubmissionsReverseSorted(self):
        count = 5
        for i in range(count):
            RequestSubmission.create(request_submission_obj)
        r_list = RequestSubmission.get_sorted()
        for i in range(1, count):
            self.assertTrue(r_list[i-1].datetime_created > r_list[i].datetime_created)

    def testRequestSubmissionNoCount(self):
        count = 5
        for i in range(count):
            RequestSubmission.create(request_submission_obj)
        r_list = RequestSubmission.get_sorted()
        self.assertEqual(len(r_list), count)

    def testRequestSubmissionWithCount(self):
        count = 5
        for i in range(count):
            RequestSubmission.create(request_submission_obj)

        r_list_full = RequestSubmission.get_sorted()
        r_list_truncated = RequestSubmission.get_sorted(count-1)
        r_list_untruncated = RequestSubmission.get_sorted(count+1)

        # Truncated list should start with the newest record
        self.assertEqual(r_list_full[0].datetime_created, r_list_truncated[0].datetime_created)

        # Length should match count
        self.assertEqual(len(r_list_truncated), count-1)

        # If count is greater than available elements, all elements should be present
        self.assertEqual(len(r_list_untruncated), count)

    
