from django.conf import settings
from django.test import TestCase
import os
import sys
from analysis.models import *
from loom.common.fixtures import hello_world
from .common import ImmutableModelsTestCase

class TestHelloWorld(ImmutableModelsTestCase):
  
    def testHelloWorld(self):
        workflow = Workflow.create(hello_world.hello_world_workflow_obj)

        self.roundTripJson(workflow)
        self.roundTripObj(workflow)
