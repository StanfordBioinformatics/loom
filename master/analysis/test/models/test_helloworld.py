from django.conf import settings
from django.test import TestCase
import os

from analysis.models import *
from analysis.test.fixtures import *

from .common import ImmutableModelsTestCase

class TestHelloWorld(ImmutableModelsTestCase):
  
    def testHelloWorld(self):
        request_submission = RequestSubmission.create(helloworld_json)

        self.roundTripJson(request_submission)
        self.roundTripObj(request_submission)
