import datetime
from django.test import TestCase, TransactionTestCase, override_settings

import loomengine.utils.helper
from . import fixtures
from api.serializers.templates import *
from api.serializers.runs import *
from api.models.runs import Run


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
