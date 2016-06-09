from django.test import TestCase

from . import fixtures
from .common import ModelTestMixin
from analysis.models import *

class TestWorkflowModels(TestCase, ModelTestMixin):

    def testFlatWorkflow(self):
        o = Workflow.create(fixtures.flat_workflow)
        self.assertEqual(o.steps.first().name, fixtures.flat_workflow['steps'][0]['name'])
        self.roundTrip(o)

    def testNestedWorkflow(self):
        o = Workflow.create(fixtures.nested_workflow)
        self.assertEqual(o.steps.first().downcast().steps.first().name, fixtures.nested_workflow['steps'][0]['steps'][0]['name'])
        self.roundTrip(o)
    

