from analysis.models import *
from .common import ImmutableModelsTestCase
from django.conf import settings
from django.test import TestCase
import os
import sys

from loom.common import fixtures


class TestRunsModels(ImmutableModelsTestCase):

    def testMinimalStepRun(self):
        o = StepRun.create(fixtures.step_run_minimal_struct)
        self.roundTripJson(o)
        self.roundTripStruct(o)

    def testStepRunWithEverything(self):
        o = StepRun.create(fixtures.step_run_with_everything_struct)
        self.roundTripJson(o)
        self.roundTripStruct(o)

    def testStepResult(self):
        step_run = StepRun.create(fixtures.step_run_with_everything_struct)
        file = File.create(fixtures.file_struct)
        result = StepResult.create(
            {
                'output_port': step_run.output_ports.first().to_struct(),
                'data_object': file.to_struct()
             }
            )
        self.roundTripJson(result)
        self.roundTripStruct(result)

class TestStepRun(TestCase):

    def testStepRunDataPipe(self):
        pass

    def testStepRunDataBinding(self):
        pass

    def testGetInputPortBundles(self):
        # TODO
        pass
