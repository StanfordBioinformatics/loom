from django.test import TestCase
from analysis.models.run_requests import RunRequest, RunRequestInput
from analysis.models.data_objects import DataObject
from .fixtures.data_objects import *
from .fixtures.run_requests import *
from .common import ModelTestMixin

class TestRunRequest(TestCase, ModelTestMixin):

    def testFlatRunRequest(self):
        with self.settings(
                WORKER_TYPE='MOCK'
        ):
            o = RunRequest.create(flat_run_request)

            o.refresh_from_db()
            self.assertTrue(o.is_completed)

            self.roundTrip(o)

    def testNestedRunRequest(self):
        with self.settings(
                WORKER_TYPE='MOCK'
        ):
            o = RunRequest.create(nested_run_request)

            o.refresh_from_db()
            self.assertTrue(o.is_completed)

            self.roundTrip(o)
