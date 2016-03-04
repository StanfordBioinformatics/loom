from django.test import TestCase

from analysis.models import TaskDefinition
from .common import UniversalModelTestMixin
from loom.common import fixtures

class TestTaskDefinitions(TestCase, UniversalModelTestMixin):

    def testTaskDefinition(self):
        td = TaskDefinition.create(fixtures.task_definition_struct)
        self.assertTrue(td.command, fixtures.task_definition_struct['command'])
        self.roundTripJson(td)
        self.roundTripStruct(td)
