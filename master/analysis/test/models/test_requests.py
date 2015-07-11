from django.test import TestCase

from analysis.models import *
from analysis.test.fixtures import *

from .common import ImmutableModelsTestCase


class TestModelsRequests(ImmutableModelsTestCase):

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

    def testStepRequest(self):
        o = StepRequest.create(step_obj_1)
        self.assertEqual(o.name, step_obj_1['name'])
        self.roundTripJson(o)
        self.roundTripObj(o)

    def testRequestsAnalysis(self):
        o = AnalysisRequest.create(analysis_obj)
        self.assertEqual(o.steps.count(), len(analysis_obj['steps']))
        self.roundTripJson(o)
        self.roundTripObj(o)

    def testRequest(self):
        o = Request.create(request_obj)
        self.assertEqual(o.analyses.count(), len(request_obj['analyses']))
        self.roundTripJson(o)
        self.roundTripObj(o)

class TestAnalysisRequest(TestCase):
    def setUp(self):
        self.analysis = AnalysisRequest.create(analysis_obj)
    
    def testGetStepRequest(self):
        step1 = self.analysis.get_step('step1')
        self.assertEqual(step1.name, step_obj_1['name'])

class TestRequestInputPort(TestCase):
    def setUp(self):
        self.analysis = AnalysisRequest.create(analysis_obj)
        self.step1 = self.analysis.get_step('step1')
        self.step2 = self.analysis.get_step('step2')

    def testIsReadyBoundData(self):
        port1 = self.step1._get_input_port('input_port1')
        self.assertTrue(port1.has_file())

    def testIsReadyConnectedFile(self):
        port2 = self.step2._get_input_port('input_port2')
        self.assertFalse(port2.has_file())
        
class TestStepRequest(TestCase):
    def setUp(self):
        self.analysis = AnalysisRequest.create(analysis_obj)
        self.step1 = self.analysis.get_step('step1')
        self.step2 = self.analysis.get_step('step2')
        
    def testIsReadyBoundData(self):
        # This step is ready because it already has a bound file.
        self.assertTrue(self.step1._are_inputs_ready())

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
