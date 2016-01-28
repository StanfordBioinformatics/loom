from analysis.models import *
import copy
from django.conf import settings
from django.test import TestCase
import os
import sys

from loom.common.fixtures import *
from .common import ImmutableModelsTestCase


class TestDefinitionModels(ImmutableModelsTestCase):

    def testDockerImage(self):
        o = StepDefinitionDockerImage.create(docker_image_struct)
        self.assertEqual(o.docker_image, docker_image_struct['docker_image'])
        self.roundTripJson(o)
        self.roundTripStruct(o)

    def testEnvironment(self):
        o = StepDefinitionEnvironment.create(docker_image_struct)
        self.assertEqual(o.docker_image, docker_image_struct['docker_image'])
        self.assertTrue(isinstance(o, StepDefinitionDockerImage))
        self.roundTripJson(o)
        self.roundTripStruct(o)

    def testInputPort(self):
        o = StepDefinitionInputPort.create(step_definition_input_port_struct)
        self.assertEqual(o.file_names.first().name, step_definition_input_port_struct['file_names'][0]['name'])
        self.roundTripJson(o)
        self.roundTripStruct(o)

    def testOutputPort(self):
        o = StepDefinitionOutputPort.create(step_definition_output_port_struct)
        self.assertEqual(o.file_name, step_definition_output_port_struct['file_name'])
        self.roundTripJson(o)
        self.roundTripStruct(o)

    def testStepDefinition(self):
        o = StepDefinition.create(step_definition_struct)
        self.assertEqual(o.command, step_definition_struct['command'])
        self.roundTripJson(o)
        self.roundTripStruct(o)

class TestStepDefinition(TestCase):

    def setUp(self):
        self.step_definition = StepDefinition.create(step_definition_struct)

    def testGetStepRun(self):
        run = self.step_definition.get_step_run()
        self.assertIsNone(run)

class TestStepDefinitionInputPort(TestCase):

    def setUp(self):
        self.step_definition_struct = step_definition_struct
        self.step_definition = StepDefinition.create(self.step_definition_struct)
        self.port_struct = self.step_definition_struct['input_ports'][0]
        self.port = StepDefinitionInputPort.create(self.port_struct) 
            # Same instance as the one attached to self.step_definition, since it's immutable

    def test_port_with_empty_array(self):
        port_struct = {u'file_names': [{'name': u''}], u'is_array': True, u'data_object': {'files': []}}
        port_struct['data_object'] = {'files': []}
        port = StepDefinitionInputPort.create(port_struct)
        o = port.to_struct()
        
    def test_get_files_and_locations_list(self):
        fl_list = self.port.get_files_and_locations_list()
        self.assertEqual(fl_list[0]['file']['file_contents']['hash_value'], self.port.data_object.file_contents.hash_value)

    def test_get_input_bundles(self):
        input_bundles = self.step_definition.get_input_bundles()
        self.assertEqual(input_bundles[0]['input_port']['data_object']['file_contents']['hash_value'], self.step_definition.input_ports.first().get('data_object').file_contents.hash_value)
            
