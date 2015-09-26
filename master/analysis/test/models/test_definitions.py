from django.conf import settings
from django.test import TestCase
from analysis.models import *
from .common import ImmutableModelsTestCase
import os
import sys

sys.path.append(os.path.join(settings.BASE_DIR, '../../..'))
from xppf.common.fixtures import *


class TestDefinitionModels(ImmutableModelsTestCase):

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
        o = StepDefinitionInputPort.create(step_definition_input_port_obj)
        self.assertEqual(o.file_path, step_definition_input_port_obj['file_path'])
        self.roundTripJson(o)
        self.roundTripObj(o)

    def testOutputPort(self):
        o = StepDefinitionOutputPort.create(step_definition_output_port_obj)
        self.assertEqual(o.file_path, step_definition_output_port_obj['file_path'])
        self.roundTripJson(o)
        self.roundTripObj(o)

    def testDataBinding(self):
        o = StepDefinitionDataBinding.create(step_definition_data_binding_obj)
        self.assertEqual(o.input_port.file_path, step_definition_data_binding_obj['input_port']['file_path'])
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

class TestStepDefinition(TestCase):

    def setUp(self):
        self.step_definition = StepDefinition.create(step_obj)

    def testGetStepRun(self):
        run = self.step_definition.get_step_run()
        self.assertIsNone(run)

    def testGetDataBinding(self):
        port = self.step_definition.template.input_ports.first()
        data_binding = self.step_definition.get_data_binding(port)
        self.assertEqual(data_binding.input_port._id, port._id)

    def testGetInputFile(self):
        port = self.step_definition.template.input_ports.first()
        data_binding = self.step_definition.get_data_binding(port)
        file = self.step_definition.get_input_file(port)
        self.assertEqual(data_binding.input_port._id, port._id)
        self.assertEqual(data_binding.file._id, file._id)


