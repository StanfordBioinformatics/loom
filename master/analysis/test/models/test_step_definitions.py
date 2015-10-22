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
        self.assertEqual(o.file_name, step_definition_input_port_obj['file_name'])
        self.roundTripJson(o)
        self.roundTripObj(o)

    def testOutputPort(self):
        o = StepDefinitionOutputPort.create(step_definition_output_port_obj)
        self.assertEqual(o.file_name, step_definition_output_port_obj['file_name'])
        self.roundTripJson(o)
        self.roundTripObj(o)

    def testStepDefinition(self):
        o = StepDefinition.create(step_definition_obj)
        self.assertEqual(o.command, step_definition_obj['command'])
        self.roundTripJson(o)
        self.roundTripObj(o)

class TestStepDefinition(TestCase):

    def setUp(self):
        self.step_definition = StepDefinition.create(step_definition_obj)

    def testGetStepRun(self):
        run = self.step_definition.get_step_run()
        self.assertIsNone(run)

class TestStepDefinitionInputPort(TestCase):

    def setUp(self):
        self.step_definition_obj = step_definition_obj
        self.step_definition = StepDefinition.create(self.step_definition_obj)
        self.port_obj = self.step_definition_obj['input_ports'][0]
        self.port = StepDefinitionInputPort.create(self.port_obj) 
            # Same instance as the one attached to self.step_definition, since it's immutable

    def test_get_files_and_locations_list(self):
        fl_list = self.port.get_files_and_locations_list()
        self.assertEqual(fl_list[0]['file']['file_contents']['hash_value'], self.port.data_object.file_contents.hash_value)

    def test_get_input_bundles(self):
        input_bundles = self.step_definition.get_input_bundles()
        self.assertEqual(input_bundles[0]['input_port']['data_object']['file_contents']['hash_value'], self.step_definition.input_ports.first().get('data_object').file_contents.hash_value)
