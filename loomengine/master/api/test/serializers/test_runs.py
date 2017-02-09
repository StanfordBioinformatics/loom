import datetime
from django.test import TestCase, TransactionTestCase, override_settings

import loomengine.utils.helper
from . import fixtures
from api.serializers.templates import *
from api.serializers.runs import *
from api.models.runs import Run
from api.test.serializers.test_templates \
    import wait_for_template_postprocessing


def wait_for_run_postprocessing(run):
    TIMEOUT=20 #seconds
    INTERVAL=1 #seconds
    loomengine.utils.helper.wait_for_true(
        lambda: Run.objects.get(id=run.id).postprocessing_status=='done',
        timeout_seconds=TIMEOUT,
        sleep_interval=INTERVAL)
    loomengine.utils.helper.wait_for_true(
        lambda: all([step.postprocessing_status=='done' for step in Run.objects.get(id=run.id).workflowrun.steps.all()]),
        timeout_seconds=TIMEOUT,
        sleep_interval=INTERVAL)
    return Run.objects.get(id=run.id)


@override_settings(TEST_DISABLE_TASK_DELAY=True)
class TestStepRunSerializer(TransactionTestCase):

    def testRender(self):
        s = TemplateSerializer(data=fixtures.templates.step_a)
        s.is_valid()
        m = s.save()
        run = Run.create_from_template(m)

        self.assertEqual(
            m.uuid,
            StepRunSerializer(run).data['template']['uuid'])


@override_settings(TEST_DISABLE_TASK_DELAY=True)
class TestWorkflowRunSerializer(TransactionTestCase):

    def testRenderFlat(self):
        s = TemplateSerializer(data=fixtures.templates.flat_workflow)
        s.is_valid()
        m = s.save()
        run = Run.create_from_template(m)

        self.assertEqual(
            m.uuid,
            WorkflowRunSerializer(run).data['template']['uuid'])


@override_settings(TEST_DISABLE_TASK_DELAY=True)
class TestRunSerializer(TransactionTestCase):

    def testRender(self):
        s = TemplateSerializer(data=fixtures.templates.step_a)
        s.is_valid()
        m = s.save()
        # Refresh to update postprocessing_status
        m = Template.objects.get(id=m.id)
        run = Run.create_from_template(m)
        
        self.assertEqual(
            m.uuid,
            RunSerializer(run).data['template']['uuid'])

    def testRenderFlat(self):
        s = TemplateSerializer(data=fixtures.templates.flat_workflow)
        s.is_valid()
        m = s.save()
        run = Run.create_from_template(m)

        self.assertEqual(
            m.uuid,
            RunSerializer(run).data['template']['uuid'])

    def testRenderNested(self):
        s = TemplateSerializer(data=fixtures.templates.nested_workflow)
        s.is_valid()
        m = s.save()
        run = Run.create_from_template(m)

        self.assertEqual(
            m.uuid,
            RunSerializer(run).data['template']['uuid'])
