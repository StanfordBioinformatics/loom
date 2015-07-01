from django.test import TestCase
from analysis.models import *
from .common import ImmutableModelsTestCase
from .test_models_files import TestFiles
from .test_models_steps import TestSteps


file_obj = TestFiles.file_obj

docker_image_request_obj = {
    'docker_image': 'ubuntu',
    }

request_input_port_obj_1 = {
    'name': 'input_port1',
    'file_path': 'rel/path/to/input_file',
    }

request_output_port_obj_1 = {
    'name': 'output_port1',
    'file_path': 'rel/path/to/output_file',
    }

request_input_port_obj_2 = {
    'name': 'input_port2',
    'file_path': 'rel/path/to/input_file',
    }

request_output_port_obj_2 = {
    'name': 'output_port2',
    'file_path': 'rel/path/to/output_file',
    }

port_identifier_obj = {
    'step': 'stepname',
    'port': 'portname',
    }

request_input_binding_obj = {
    'file': file_obj,
    'destination': {
        'step': 'step1',
        'port': 'input_port1',
        },
    }

request_connector_obj = {
    'source': {
        'step': 'step1',
        'port': 'output_port1',
        },
    'destination': {
        'step': 'step2',
        'port': 'input_port2',
        },
    }

resource_request_obj = {
    'memory': '5G',
    'cores': 4,
    }

step_request_obj_1 = {
    'name': 'step1',
    'input_ports': [request_input_port_obj_1],
    'output_ports': [request_output_port_obj_1],
    'command': 'echo hello',
    'environment': docker_image_request_obj,
    'resources': resource_request_obj,
    }

step_request_obj_2 = {
    'name': 'step2',
    'input_ports': [request_input_port_obj_2],
    'output_ports': [request_output_port_obj_2],
    'command': 'echo world',
    'environment': docker_image_request_obj,
    'resources': resource_request_obj,
    }

analysis_request_obj = {
    'steps': [step_request_obj_1, step_request_obj_2],
    'input_bindings': [request_input_binding_obj],
    'connectors': [request_connector_obj],
    }

request_obj = {
    'analyses': [analysis_request_obj],
    'requester': 'someone@example.com',
    }


class TestModelsRequests(ImmutableModelsTestCase):

    def testDockerImageRequest(self):
        o = DockerImageRequest.create(docker_image_request_obj)
        self.assertEqual(o.docker_image, docker_image_request_obj['docker_image'])
        self.roundTripJson(o)
        self.roundTripObj(o)

    def testEnvironmentRequest(self):
        o = EnvironmentRequest.create(docker_image_request_obj)
        self.assertEqual(o.docker_image, docker_image_request_obj['docker_image'])
        self.roundTripJson(o)
        self.roundTripObj(o)

    def testRequestInputPort(self):
        o = RequestInputPort.create(request_input_port_obj_1)
        self.assertEqual(o.name, request_input_port_obj_1['name'])
        self.roundTripJson(o)
        self.roundTripObj(o)

    def testRequestOutputPort(self):
        o = RequestOutputPort.create(request_output_port_obj_1)
        self.assertEqual(o.name, request_output_port_obj_1['name'])
        self.roundTripJson(o)
        self.roundTripObj(o)

    def testInputBindingPortIdentifier(self):
        o = InputBindingPortIdentifier.create(port_identifier_obj)
        self.assertEqual(o.step, port_identifier_obj['step'])
        self.roundTripJson(o)
        self.roundTripObj(o)

    def testRequestConnectorSourcePortIdentifier(self):
        o = RequestConnectorSourcePortIdentifier.create(port_identifier_obj)
        self.assertEqual(o.step, port_identifier_obj['step'])
        self.roundTripJson(o)
        self.roundTripObj(o)

    def testRequestConnectorDestinationPortIdentifier(self):
        o = RequestConnectorDestinationPortIdentifier.create(port_identifier_obj)
        self.assertEqual(o.step, port_identifier_obj['step'])
        self.roundTripJson(o)
        self.roundTripObj(o)

    def testRequestInputBinding(self):
        o = RequestInputBinding.create(request_input_binding_obj)
        self.assertEqual(o.destination.step, request_input_binding_obj['destination']['step'])
        self.roundTripJson(o)
        self.roundTripObj(o)

    def testRequestConnector(self):
        o = RequestConnector.create(request_connector_obj)
        self.assertEqual(o.source.step, request_connector_obj['source']['step'])
        self.roundTripJson(o)
        self.roundTripObj(o)

    def testResourceRequest(self):
        o = ResourceRequest.create(resource_request_obj)
        self.assertEqual(o.cores, resource_request_obj['cores'])
        self.roundTripJson(o)
        self.roundTripObj(o)

    def testStepRequest(self):
        o = StepRequest.create(step_request_obj_1)
        self.assertEqual(o.name, step_request_obj_1['name'])
        self.roundTripJson(o)
        self.roundTripObj(o)

    def testAnalysisRequest(self):
        o = AnalysisRequest.create(analysis_request_obj)
        self.assertEqual(o.steps.count(), len(analysis_request_obj['steps']))
        self.roundTripJson(o)
        self.roundTripObj(o)

    def testRequest(self):
        o = Request.create(request_obj)
        self.assertEqual(o.analyses.count(), len(request_obj['analyses']))
        self.roundTripJson(o)
        self.roundTripObj(o)

class TestAnalysisRequest(TestCase):
    def setUp(self):
        self.analysis = AnalysisRequest.create(analysis_request_obj)
    
    def testGetStepRequest(self):
        step1 = self.analysis.get_step_request('step1')
        self.assertEqual(step1.name, step_request_obj_1['name'])

class TestRequestInputPort(TestCase):
    def setUp(self):
        self.analysis = AnalysisRequest.create(analysis_request_obj)
        self.step1 = self.analysis.get_step_request('step1')
        self.step2 = self.analysis.get_step_request('step2')

    def testIsReadyBoundFile(self):
        port1 = self.step1.get_input_port('input_port1')
        self.assertTrue(port1.is_ready())

    def testIsReadyConnectedFile(self):
        port2 = self.step2.get_input_port('input_port2')
        self.assertFalse(port2.is_ready())
        
class TestStepRequest(TestCase):
    def setUp(self):
        self.analysis = AnalysisRequest.create(analysis_request_obj)
        self.step1 = self.analysis.get_step_request('step1')
        self.step2 = self.analysis.get_step_request('step2')
        
    def testIsReadyBoundFile(self):
        # This step is ready because it already has a bound file.
        self.assertTrue(self.step1.is_ready())

    def testIsReadyConnectorNoFile(self):
        # This step is not ready because its input port has a connector to the
        # previous step but no file exists.
        self.assertFalse(self.step2.is_ready())

    def testIsReadyConnectorWithFile(self):
        # TODO

        # self.step1.create_step_run()
        # self.step1.post_result()
        # self.assertTrue(step2.is_ready())
        pass

    def testGetInputPort(self):
        port1 = self.step1.get_input_port('input_port1')
        self.assertEqual(port1.name, 'input_port1')

    def testGetOutputPort(self):
        port1 = self.step1.get_output_port('output_port1')
        self.assertEqual(port1.name, 'output_port1')

"""
    step_result_obj = {
        'file': file_obj,
        'output_port': output_port_obj,
        'step_definition': step_definition_obj,
        }

    step_run_record_obj = {
        'step_definition': step_definition_obj,
        'step_results': [step_result_obj],
        }

    analysis_run_obj = {
        'analysis_definition': analysis_definition_obj,
        # Exclude analysis_run_record, to be added on update
        }

    file_import_record_obj = {
        'import_comments': 'Notes about the source of this file...',
        'file': file_obj,
        'requester': 'someone@example.net',
        }

    file_import_request_obj = {
        'import_comments': 'Notes about the source of this file...',
        'file_location': file_path_location_obj,
        'requester': 'someone@example.net',
        # Exclude file_import_record, to be added on update
        }
"""
