from django.conf import settings
from django.test import TestCase
import os
import sys

from analysis.models import *
sys.path.append(os.path.join(settings.BASE_DIR, '../../..'))
from xppf.common.fixtures import *

from .common import ImmutableModelsTestCase


class TestRunsModels(ImmutableModelsTestCase):

    def testMinimalStepRun(self):
        o = StepRun.create(step_run_minimal_obj)
        self.assertEqual(o.steps.all().first().name,
                         step_run_minimal_obj['steps'][0]['name'])
        self.roundTripJson(o)
        self.roundTripObj(o)

    def testStepRunWithEverything(self):
        o = StepRun.create(step_run_with_everything_obj)
        self.assertEqual(o.steps.all().first().name,
                         step_run_with_everything_obj['steps'][0]['name'])
        self.roundTripJson(o)
        self.roundTripObj(o)

#    def testStepRunConnector(self):
#        o = StepRun.create(step_run_with_everything_obj)
        
                         

#class TestStepRun(TestCase):

#    def testGetInputPortBundles(self):
#        o = StepRun.create(hello_world_step_run_obj2)
#        o.get_input_port_bundles()
        # TODO
