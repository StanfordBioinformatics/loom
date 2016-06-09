from django.test import TestCase

from analysis.models import TaskRun, TaskDefinition
from . import fixtures
from .common import ModelTestMixin

class TestTaskRuns(TestCase, ModelTestMixin):

    def testTaskRun(self):
        tr = TaskRun.create(fixtures.task_run)
        self.assertEqual(tr.task_definition.command, fixtures.task_run['task_definition']['command'])
        self.roundTrip(tr)

