from django.test import TestCase

from api.models import *
from api.test import fixtures


class TestTaskRunAttempt(TestCase):

    def test_post_save(self):
        step = Step.objects.create(command='blank')
        step_run = StepRun.objects.create(template=step)
        task_run = TaskRun.objects.create(step_run=step_run)

        task_run_attempt = TaskRunAttempt.objects.create(task_run=task_run)

        # Worker Process and monitor should be automatically created
        self.assertIsNotNone(task_run_attempt.worker_process)
        self.assertIsNotNone(task_run_attempt.worker_process_monitor)

        # Their statuses should be 'not_started'
        self.assertEqual(task_run_attempt.worker_process.status, 'not_started')
        self.assertEqual(task_run_attempt.worker_process_monitor.status, 'not_started')
        
    def test_status_updates_local_finished_successfully(self):
        step = Step.objects.create(command='blank')
        step_run = StepRun.objects.create(template=step)
        task_run = TaskRun.objects.create(step_run=step_run)

        task_run_attempt = TaskRunAttempt.objects.create(task_run=task_run)

        process = task_run_attempt.worker_process
        monitor = task_run_attempt.worker_process_monitor

        # Initial status
        self.assertEqual(process.status, 'not_started')
        self.assertEqual(monitor.status, 'not_started')
        self.assertEqual(task_run.status, 'initializing_monitor_process')

        monitor.status = 'gathering_input_files'
        monitor.status = 'preparing_runtime_environment'
        
