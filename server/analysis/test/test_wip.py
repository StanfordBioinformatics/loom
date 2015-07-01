from django.test import TestCase
from analysis.models import *
import os
from django.conf import settings

class TestWorkInProgress(TestCase):

    hello_world_analysis_count = 1
    hello_world_step_count = 2

    def setUp(self):
        with open(os.path.join(settings.BASE_DIR,'../../doc/examples/helloworld/helloworld.json')) as f:
            self.helloworld_json = f.read()
        self.wip = WorkInProgress._get_wip_singleton()

    def test_submit_new_request(self):
        requests_before = self.wip.open_requests.count()        
        analyses_before = self.wip.ready_analyses.count()

        WorkInProgress.submit_new_request(self.helloworld_json)

        requests_after = self.wip.open_requests.count()
        analyses_after = self.wip.ready_analyses.count()

        self.assertEqual(requests_after, requests_before + 1)
        self.assertEqual(analyses_after, analyses_before + self.hello_world_analysis_count)

    def test_run_ready_analyses(self):
        WorkInProgress.submit_new_request(self.helloworld_json)

        ready_analyses_before = self.wip.ready_analyses.count()
        running_analyses_before = self.wip.running_analyses.count()

        self.wip._run_ready_analyses()

        ready_analyses_after = self.wip.ready_analyses.count()
        running_analyses_after = self.wip.running_analyses.count()

        self.assertEqual(ready_analyses_after, ready_analyses_before - self.hello_world_analysis_count)
        self.assertEqual(running_analyses_after, running_analyses_before + self.hello_world_analysis_count)

    def test_update_ready_steps(self):
        WorkInProgress.submit_new_request(self.helloworld_json)
        self.wip._run_ready_analyses()

        steps_before = self.wip.ready_steps.count()

        self.wip._update_ready_steps()

        steps_after = self.wip.ready_steps.count()
    
        # Only 1 step initially has all prereqs in this request
        self.assertEqual(steps_after, steps_before + 1) 

