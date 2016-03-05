from django.test import TestCase

from analysis.models import TaskRun, TaskDefinition
from .common import UniversalModelTestMixin
from loom.common import fixtures

class TestTaskRuns(TestCase, UniversalModelTestMixin):

    def testTaskRun(self):
        tr = TaskRun.create(fixtures.task_run_struct)
        self.assertEqual(tr.task_definition.command, fixtures.task_run_struct['task_definition']['command'])
        self.roundTripJson(tr)
        self.roundTripStruct(tr)

