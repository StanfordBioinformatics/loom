import datetime
from django.test import TestCase, TransactionTestCase

import loomengine.utils.helper
from . import fixtures
from api.serializers.templates import *
from api.serializers.runs import *
from api.models.runs import Run
from api.test.serializers.test_templates \
    import wait_for_template_postprocessing


def wait_for_run_postprocessing(run):
    TIMEOUT=120 #seconds
    INTERVAL=1 #seconds
    loomengine.utils.helper.wait_for_true(
        lambda: Run.objects.get(id=run.id).saving_status=='ready',
        timeout_seconds=TIMEOUT,
        sleep_interval=INTERVAL)
    loomengine.utils.helper.wait_for_true(
        lambda: all([step.saving_status=='ready' for step in Run.objects.get(id=run.id).workflowrun.steps.all()]),
        timeout_seconds=TIMEOUT,
        sleep_interval=INTERVAL)
    return Run.objects.get(id=run.id)


class TestStepRunSerializer(TransactionTestCase):

    def testRender(self):
        with self.settings(TEST_DISABLE_TASK_DELAY=True,
                           WORKER_TYPE='MOCK'):
            s = TemplateSerializer(data=fixtures.templates.step_a)
            s.is_valid()
            m = s.save()
            run = Run.create_from_template(m)

        self.assertEqual(
            m.uuid,
            StepRunSerializer(run).data['template']['uuid'])

class TestWorkflowRunSerializer(TransactionTestCase):

    def testRenderFlat(self):
        with self.settings(TEST_DISABLE_TASK_DELAY=True,
                           WORKER_TYPE='MOCK'):
            s = TemplateSerializer(data=fixtures.templates.flat_workflow)
            s.is_valid()
            m = s.save()
            run = Run.create_from_template(m)

        self.assertEqual(
            m.uuid,
            WorkflowRunSerializer(run).data['template']['uuid'])


class TestRunSerializer(TransactionTestCase):

    def testRender(self):
        with self.settings(TEST_DISABLE_TASK_DELAY=True,
                           WORKER_TYPE='MOCK'):
            s = TemplateSerializer(data=fixtures.templates.step_a)
            s.is_valid()
            m = s.save()
            # Refresh to update saving_status
            m = Template.objects.get(id=m.id)
            run = Run.create_from_template(m)

        self.assertEqual(
            m.uuid,
            RunSerializer(run).data['template']['uuid'])

    def testRenderFlat(self):
        with self.settings(TEST_DISABLE_TASK_DELAY=True,
                           WORKER_TYPE='MOCK'):
            s = TemplateSerializer(data=fixtures.templates.flat_workflow)
            s.is_valid()
            m = s.save()
            run = Run.create_from_template(m)

        self.assertEqual(
            m.uuid,
            RunSerializer(run).data['template']['uuid'])

    def testRenderNested(self):
        with self.settings(TEST_DISABLE_TASK_DELAY=True,
                           WORKER_TYPE='MOCK'):
            s = TemplateSerializer(data=fixtures.templates.nested_workflow)
            s.is_valid()
            m = s.save()
            run = Run.create_from_template(m)

        self.assertEqual(
            m.uuid,
            RunSerializer(run).data['template']['uuid'])

    def testCreationTime(self):
        # We're measuring request time, not total generation time with
        # postprocessing
        data100 = fixtures.run_fixtures.many_steps\
                                        .generator.make_many_steps(100)
        s = TemplateSerializer(data=data100)
        s.is_valid(raise_exception=True)
        template = s.save()
        template = wait_for_template_postprocessing(template)
        
        with self.settings(TEST_NO_AUTO_START_RUNS=True,
                           TEST_NO_POSTPROCESS=True):
            tic100 = datetime.datetime.now()
            Run.create_from_template(template)
            time100 = datetime.datetime.now() - tic100
            
            # Create run with 1000 steps in under 500 ms
            self.assertTrue(time100.total_seconds() < 0.5)

    def testCreationPostprocessingTime(self):
        NUMSTEPS = 20
        # We're measuring request time, not total generation time with
        # postprocessing
        data = fixtures.run_fixtures.many_steps\
                                        .generator.make_many_steps(NUMSTEPS)
        s = TemplateSerializer(data=data)
        s.is_valid(raise_exception=True)
        template = s.save()
        template = wait_for_template_postprocessing(template)

        with self.settings(TEST_NO_AUTO_START_RUNS=True):
            tic = datetime.datetime.now()
            run = Run.create_from_template(template)
            run = wait_for_run_postprocessing(run)
            toc = datetime.datetime.now() - tic
            
            # Postprocess run with 20 steps in under 10 s
            self.assertTrue(toc.total_seconds() < 10)
