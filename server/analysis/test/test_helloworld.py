from django.conf import settings
from django.test import TestCase
import os
from analysis.models import *
from .common import ImmutableModelsTestCase

class TestHelloWorld(ImmutableModelsTestCase):
  
    def setUp(self):
        with open(os.path.join(settings.BASE_DIR,'../../doc/examples/helloworld/helloworld.json')) as f:
            self.helloworld_json = f.read()
        
    def testHelloWorld(self):
        request = Request.create(self.helloworld_json)

        self.roundTripJson(request)
        self.roundTripObj(request)
