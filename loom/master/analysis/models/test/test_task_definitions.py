from django.test import TestCase

from analysis.models import TaskDefinition
from . import fixtures
from .common import ModelTestMixin


class TestTaskDefinitions(TestCase, ModelTestMixin):

    def testTaskDefinition(self):
        td = TaskDefinition.create(fixtures.task_definition)
        self.assertTrue(td.command, fixtures.task_definition['command'])
        self.roundTrip(td)
    
