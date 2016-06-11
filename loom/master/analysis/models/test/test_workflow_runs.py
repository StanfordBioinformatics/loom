from django.conf import settings
from django.test import TestCase

from analysis.models import *
from analysis.exceptions import *
from . import fixtures
from .common import ModelTestMixin


class TestStepRun(TestCase, ModelTestMixin):

    def testStepRun(self):
        with self.settings(WORKER_TYPE='MOCK'):
            o = StepRun.create(fixtures.step_run_a)
            self.assertEqual(
                o.template.name, fixtures.step_run_a['template']['name']
            )
            self.roundTrip(o)


class TestWorkflowRun(TestCase, ModelTestMixin):

    def testFlatWorkflowRun(self):
        with self.settings(WORKER_TYPE='MOCK'):
            o = WorkflowRun.create(fixtures.flat_workflow_run)
            self.assertEqual(
                o.template.steps.first().name, fixtures.flat_workflow_run['template']['steps'][0]['name']
            )
            self.roundTrip(o)
        
    def testNestedWorkflowRun(self):
        with self.settings(WORKER_TYPE='MOCK'):
            o = WorkflowRun.create(fixtures.nested_workflow_run)
            self.assertEqual(
                o.template.steps.first().downcast().steps.first().name, fixtures.nested_workflow_run['template']['steps'][0]['steps'][0]['name']
            )
            self.roundTrip(o)
