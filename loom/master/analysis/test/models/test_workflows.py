from analysis.models import *
from django.conf import settings
from django.test import TestCase
import os
import sys
from loom.common import fixtures
from loom.common.fixtures.workflows import hello_world
from .common import UniversalModelTestMixin


class TestWorkflowModels(TestCase, UniversalModelTestMixin):

    def testRequestedDockerImage(self):
        o = RequestedDockerImage.create(fixtures.docker_image_struct)
        self.assertEqual(o.docker_image, fixtures.docker_image_struct['docker_image'])
        self.roundTripJson(o)
        self.roundTripStruct(o)

    def testRequestedEnvironment(self):
        o = RequestedEnvironment.create(fixtures.docker_image_struct)
        self.assertEqual(o.docker_image, fixtures.docker_image_struct['docker_image'])
        self.roundTripJson(o)
        self.roundTripStruct(o)

    def testRequestedResourceSet(self):
        o = RequestedResourceSet.create(fixtures.resource_set_struct)
        self.assertEqual(o.cores, fixtures.resource_set_struct['cores'])
        self.roundTripJson(o)
        self.roundTripStruct(o)

    def testStep(self):
        o = Step.create(fixtures.step_1_struct)
        self.assertEqual(o.step_name, fixtures.step_1_struct['step_name'])
        self.roundTripJson(o)
        self.roundTripStruct(o)

    def testWorkflow(self):
        o = Workflow.create(fixtures.workflow_struct)
        self.assertEqual(o.steps.count(), len(fixtures.workflow_struct['steps']))
        self.roundTripJson(o)
        self.roundTripStruct(o)
