from django.test import TestCase

from api.test import fixtures
from api.models import *
from api.serializers.task_runs import *

class TestWorkerProcessSerializer(TestCase):

    def testCreate(self):
        step = Step.objects.create(command='blank')
        step_run = StepRun.objects.create(template=step)
        task_run = TaskRun.objects.create(step_run=step_run)
        task_run_attempt = TaskRunAttempt.objects.create(task_run=task_run)

        s = WorkerProcessSerializer(
            data={'status': 'running'},
            context={'parent_field': 'task_run_attempt',
                     'parent_instance': task_run_attempt})
        s.is_valid(raise_exception=True)
        m = s.save()
        self.assertEqual(m.status, 'running')
