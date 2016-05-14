from analysis.models import *
from django.conf import settings
from django.test import TestCase
import os
import sys
from . import fixtures
from .common import UniversalModelTestMixin


class TestWorkflowModels(TestCase, UniversalModelTestMixin):

    def testFlatWorkflow(self):
        o = Workflow.create(fixtures.flat_workflow_struct)
        self.assertEqual(o.steps.first().name, fixtures.flat_workflow_struct['steps'][0]['name'])
        self.roundTripJson(o)
        self.roundTripStruct(o)

    def testNestedWorkflow(self):
        o = Workflow.create(fixtures.nested_workflow_struct)
        self.assertEqual(o.steps.first().downcast().steps.first().name, fixtures.nested_workflow_struct['steps'][0]['steps'][0]['name'])
        self.roundTripJson(o)
        self.roundTripStruct(o)
    

