from analysis.models import *
from .common import ImmutableModelsTestCase
from .test_models_files import TestFiles

file_obj = TestFiles.file_obj

docker_image_obj = {
    'docker_image': '1234567asdf',
    }

input_port_obj = {
    'file_path':'copy/my/file/here.txt',
    }

output_port_obj = {
    'file_path':'look/for/my/file/here.txt',
    }

data_binding_obj = {
    'file': file_obj,
    'input_port': input_port_obj,
    }

template_obj = {
    'input_ports': [input_port_obj],
    'output_ports': [output_port_obj],
    'command': 'echo test',
    'environment': docker_image_obj,
    }

step_obj = {
    'template': template_obj,
    'data_bindings': [data_binding_obj],
    }

class TestDefinitions(ImmutableModelsTestCase):

    def testDockerImage(self):
        o = StepDefinitionDockerImage.create(docker_image_obj)
        self.assertEqual(o.docker_image, docker_image_obj['docker_image'])
        self.roundTripJson(o)
        self.roundTripObj(o)

    def testEnvironment(self):
        o = StepDefinitionEnvironment.create(docker_image_obj)
        self.assertEqual(o.docker_image, docker_image_obj['docker_image'])
        self.assertTrue(isinstance(o, StepDefinitionDockerImage))
        self.roundTripJson(o)
        self.roundTripObj(o)

    def testInputPort(self):
        o = StepDefinitionInputPort.create(input_port_obj)
        self.assertEqual(o.file_path, input_port_obj['file_path'])
        self.roundTripJson(o)
        self.roundTripObj(o)

    def testOutputPort(self):
        o = StepDefinitionOutputPort.create(output_port_obj)
        self.assertEqual(o.file_path, output_port_obj['file_path'])
        self.roundTripJson(o)
        self.roundTripObj(o)

    def testDataBinding(self):
        o = StepDefinitionDataBinding.create(data_binding_obj)
        self.assertEqual(o.input_port.file_path, data_binding_obj['input_port']['file_path'])
        self.roundTripJson(o)
        self.roundTripObj(o)

    def testTemplate(self):
        o = StepDefinitionTemplate.create(template_obj)
        self.assertEqual(o.command, template_obj['command'])
        self.roundTripJson(o)
        self.roundTripObj(o)
        
    def testStepDefinition(self):
        o = StepDefinition.create(step_obj)
        self.assertEqual(o.template.command, step_obj['template']['command'])
        self.roundTripJson(o)
        self.roundTripObj(o)
