from django.test import TestCase
from analysis.models import *
import os
from django.conf import settings


class TestQueues(TestCase):

    hello_world_analysis_count = 1
    hello_world_step_count = 2

    def setUp(self):
        with open(os.path.join(settings.BASE_DIR,'../../doc/examples/helloworld/helloworld.json')) as f:
            self.helloworld_json = f.read()
        self.queues = Queues._get_queue_singleton()

    def test_submit_new_request(self):
        requests_before = self.queues.open_requests.count()        
        analyses_before = self.queues.open_analyses.count()

        Queues.submit_new_request(self.helloworld_json)

        requests_after = self.queues.open_requests.count()
        analyses_after = self.queues.open_analyses.count()

        self.assertEqual(requests_after, requests_before + 1)
        self.assertEqual(analyses_after, analyses_before + self.hello_world_analysis_count)

    def test_update_ready_steps(self):
        steps_ready_to_run_before = self.queues.steps_ready_to_run.count()
        steps_running_before = self.queues.steps_running.count()

        Queues.submit_new_request(self.helloworld_json)
        q = Queues._get_queue_singleton()
        q._update_steps_ready_to_run()

        steps_ready_to_run_after = self.queues.steps_ready_to_run.count()
        steps_running_after = self.queues.steps_running.count()

        self.assertEqual(steps_ready_to_run_after, steps_ready_to_run_before + 1)
        self.assertEqual(steps_running_after, steps_running_before)

    def test_run_ready_steps(self):
        steps_ready_to_run_before = self.queues.steps_ready_to_run.count()
        steps_running_before = self.queues.steps_running.count()
        results_before = StepResult.objects.count()

        Queues.submit_new_request(self.helloworld_json)
        q = Queues._get_queue_singleton()
        q._update_steps_ready_to_run()
        q._run_ready_steps()

        steps_ready_to_run_after = self.queues.steps_ready_to_run.count()
        steps_running_after = self.queues.steps_running.count()
        results_after = StepResult.objects.count()

        self.assertEqual(steps_ready_to_run_after, steps_ready_to_run_before)
        self.assertEqual(steps_running_after, steps_running_before + 1)
        self.assertEqual(results_after, results_before + 1)

    def test_run_second_step(self):
        steps_ready_to_run_before = self.queues.steps_ready_to_run.count()
        steps_running_before = self.queues.steps_running.count()
        results_before = StepResult.objects.count()

        Queues.submit_new_request(self.helloworld_json)
        q = Queues._get_queue_singleton()
        q._update_steps_ready_to_run()
        q._run_ready_steps()

        # Step1 should be done now.
        q._update_steps_ready_to_run()
        q._run_ready_steps()

        steps_ready_to_run_after = self.queues.steps_ready_to_run.count()
        steps_running_after = self.queues.steps_running.count()
        results_after = StepResult.objects.count()

        self.assertEqual(steps_ready_to_run_after, steps_ready_to_run_before)
        self.assertEqual(steps_running_after, steps_running_before + 2)
        self.assertEqual(results_after, results_before + 2)
