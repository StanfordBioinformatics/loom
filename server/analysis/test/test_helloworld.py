from django.conf import settings
from django.test import TestCase
import os
from analysis.models import *

class TestHelloWorld(TestCase):
  
    def setUp(self):
        with open(os.path.join(settings.BASE_DIR,'../../doc/examples/helloworld/helloworld.json')) as f:
            self.helloworld_json = f.read()
        
    def testHelloWorld(self):
        analysis_request = RequestRun.create(self.helloworld_json)

        self.roundTripJson(analysis_request)
        self.roundTripObj(analysis_request)
        
    def roundTripJson(self, model):
        cls = model.__class__
        id1 = model._id
        model = cls.create(model.to_json())
        self.assertEqual(model._id, id1)

    def roundTripObj(self, model):
        cls = model.__class__
        id1 = model._id
        model = cls.create(model.to_obj())
        self.assertEqual(model._id, id1)
