from django.conf import settings
from django.test import TestCase
import os
import sys

from analysis.models import *

sys.path.append(os.path.join(settings.BASE_DIR, '../../..'))
from xppf.common.fixtures import *


class TestWorkInProgress(TestCase):

    hello_world_workflow_count = 1
    hello_world_step_count = 2

    def setUp(self):
        self.queues = WorkInProgress._get_queue_singleton()

    def test_submit_new_request(self):
        request_submissions_before = self.queues.open_request_submissions.count()        
        workflows_before = self.queues.open_workflows.count()

        WorkInProgress.submit_new_request(helloworld_json)

        request_submissions_after = self.queues.open_request_submissions.count()
        workflows_after = self.queues.open_workflows.count()

        self.assertEqual(request_submissions_after, request_submissions_before + 1)
        self.assertEqual(workflows_after, workflows_before + self.hello_world_workflow_count)

    def test_update_ready_steps(self):
        steps_ready_to_run_before = self.queues.steps_ready_to_run.count()
        steps_running_before = self.queues.steps_running.count()

        WorkInProgress.submit_new_request(helloworld_json)
        q = WorkInProgress._get_queue_singleton()
        q._update_steps_ready_to_run()

        steps_ready_to_run_after = self.queues.steps_ready_to_run.count()
        steps_running_after = self.queues.steps_running.count()

        self.assertEqual(steps_ready_to_run_after, steps_ready_to_run_before + 1)
        self.assertEqual(steps_running_after, steps_running_before)
