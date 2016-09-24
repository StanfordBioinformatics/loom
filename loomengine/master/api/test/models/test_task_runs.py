from django.test import TestCase

from api.models import *
from api.test import fixtures


class TestTaskRunAttempt(TestCase):

    def test_create(self):
        step = Step.objects.create(command='blank')
        step_run = StepRun.objects.create(template=step)
        task_run = TaskRun.objects.create(step_run=step_run)

        task_run_attempt = TaskRunAttempt.objects.create(task_run=task_run)

        # Their statuses should be 'not_started'
        self.assertEqual(task_run_attempt.process_status, 'not_started')
        self.assertEqual(task_run_attempt.monitor_status, 'not_started')
        self.assertEqual(task_run_attempt.save_outputs_status, 'not_started')

