from django.test import TestCase, TransactionTestCase

from . import fixtures
from api.serializers.templates import *
from api.serializers.runs import *


class TestStepRunSerializer(TransactionTestCase):

    def testRender(self):
        s = TemplateSerializer(data=fixtures.templates.step_a)
        s.is_valid()
        m = s.save()
        run = Run.create_from_template(m)

        self.assertEqual(
            m.uuid,
            StepRunSerializer(run).data['template']['uuid'])

class TestWorkflowRunSerializer(TransactionTestCase):

    def testRenderFlat(self):
        s = TemplateSerializer(data=fixtures.templates.flat_workflow)
        s.is_valid()
        m = s.save()
        run = Run.create_from_template(m)

        self.assertEqual(
            m.uuid,
            WorkflowRunSerializer(run).data['template']['id'])


class TestWorkflowRunSerializer(TransactionTestCase):

    def testRenderFlat(self):
        s = TemplateSerializer(data=fixtures.templates.flat_workflow)
        s.is_valid()
        m = s.save()
        run = Run.create_from_template(m)

        self.assertEqual(
            m.uuid,
            WorkflowRunSerializer(run).data['template']['uuid'])


class TestRunSerializer(TransactionTestCase):

    def testRender(self):
        s = TemplateSerializer(data=fixtures.templates.step_a)
        s.is_valid()
        m = s.save()
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

    def testRenderFlat(self):
        s = TemplateSerializer(data=fixtures.templates.flat_workflow)
        s.is_valid()
        m = s.save()
        run = Run.create_from_template(m)

        self.assertEqual(
            m.uuid,
            RunSerializer(run).data['template']['uuid'])
