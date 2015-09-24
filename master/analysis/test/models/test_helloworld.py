from django.conf import settings
from django.test import TestCase
import os
import sys

from analysis.models import *

sys.path.append(os.path.join(settings.BASE_DIR, '../../..'))
from xppf.utils.fixtures import *

from .common import ImmutableModelsTestCase

class TestHelloWorld(ImmutableModelsTestCase):
  
    def testHelloWorld(self):
        request_submission = RequestSubmission.create(helloworld_json)

        self.roundTripJson(request_submission)
        self.roundTripObj(request_submission)
