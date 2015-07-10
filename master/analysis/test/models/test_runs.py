from django.test import TestCase

from analysis.models import *
from analysis.test.fixtures import *

from .common import ImmutableModelsTestCase


class TestRunsModels(ImmutableModelsTestCase):

    def testStepRun(self):
        o = StepRun.create(hello_world_step_run_obj1)
        self.assertEqual(o.step_definition.template.get('environment').docker_image,
                         hello_world_step_run_obj1['step_definition']['template']['environment']['docker_image'])
        self.roundTripJson(o)
        self.roundTripObj(o)

class TestStepRun(TestCase):

    def testGetInputPortBundles(self):
        o = StepRun.create(hello_world_step_run_obj2)
        o.get_input_port_bundles()
        # TODO
