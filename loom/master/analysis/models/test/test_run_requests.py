from django.test import TestCase
from analysis.models.run_requests import RunRequest, RunRequestInput
from analysis.models.data_objects import DataObject
from .fixtures.data_objects import *
from .fixtures.run_requests import *
from .common import ModelTestMixin

class TestRunRequest(TestCase, ModelTestMixin):

    def testFlatRunRequest(self):
        o = RunRequest.create(flat_run_request)
        self.roundTrip(o)

    def testNestedRunRequest(self):
        o = RunRequest.create(nested_run_request)
        self.roundTrip(o)
