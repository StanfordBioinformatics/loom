from django.conf import settings
from django.test import TestCase
import os
import sys
from analysis.models import *
from loom.common.fixtures import hello_world
from .common import ImmutableModelsTestCase

class TestHelloWorld(ImmutableModelsTestCase):
  
    def testHelloWorld(self):
        run_request = RunRequest.create(hello_world.hello_world_run_request_obj)

        self.roundTripJson(run_request)
        self.roundTripObj(run_request)
