from django.test import TestCase
from analysis.models.run_requests import RunRequest, RunRequestInput
from analysis.models.data_objects import DataObject
from .fixtures.data_objects import *
from .fixtures.run_requests import *
from .common import UniversalModelTestMixin

class TestRunRequest(TestCase, UniversalModelTestMixin):

    def testRunRequest(self):
        o = RunRequest.create(run_request)
        self.roundTripJson(o)
        self.roundTripStruct(o)
