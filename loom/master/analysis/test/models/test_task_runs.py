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

    def testCreateFromTaskDefinition(self):
        td = TaskDefinition.create(fixtures.task_definition_struct)
        tr = TaskRun.create_from_task_definition(td)
        self.assertEqual(tr.task_definition.command, td.command)
        self.assertEqual(tr.task_run_inputs.first().task_definition_input._id, td.inputs.first()._id)
        self.assertEqual(tr.task_run_outputs.first().task_definition_output._id, td.outputs.first()._id)
        self.roundTripJson(tr)
        self.roundTripStruct(tr)

    def testExecute(self):
        tr = TaskRun.create(fixtures.task_run_struct)
        tr.execute()
        self.assertIsNotNone(tr.task_run_outputs.first().data_object)

