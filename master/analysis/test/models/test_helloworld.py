from django.conf import settings
from django.test import TestCase
import os

from analysis.models import *
from analysis.test.fixtures import *

from .common import ImmutableModelsTestCase

class TestHelloWorld(ImmutableModelsTestCase):
  
    def testHelloWorld(self):
        request = Request.create(helloworld_json)

        self.roundTripJson(request)
        self.roundTripObj(request)
