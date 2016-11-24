from django.test import TestCase

from . import fixtures
from api.serializers.templates import *
from api.serializers.runs import *


class TestStepRunSerializer(TestCase):

    def testRender(self):
        s = TemplateSerializer(data=fixtures.templates.step_a)
        s.is_valid()
        m = s.save()
        run = Run.create_from_template(m)

        self.assertEqual(
            m.id,
            StepRunSerializer(run).data['template']['id'])

class TestWorkflowRunSerializer(TestCase):

    def testRenderFlat(self):
        s = TemplateSerializer(data=fixtures.templates.flat_workflow)
        s.is_valid()
        m = s.save()
        run = Run.create_from_template(m)

        self.assertEqual(
            m.id,
            WorkflowRunSerializer(run).data['template']['id'])


class TestWorkflowRunSerializer(TestCase):

    def testRenderFlat(self):
        s = TemplateSerializer(data=fixtures.templates.flat_workflow)
        s.is_valid()
        m = s.save()
        run = Run.create_from_template(m)

        self.assertEqual(
            m.id,
            WorkflowRunSerializer(run).data['template']['id'])


class TestRunSerializer(TestCase):

    def testRender(self):
        s = TemplateSerializer(data=fixtures.templates.step_a)
        s.is_valid()
        m = s.save()
        run = Run.create_from_template(m)

        self.assertEqual(
            m.id,
            RunSerializer(run).data['template']['id'])

    def testRenderFlat(self):
        s = TemplateSerializer(data=fixtures.templates.flat_workflow)
        s.is_valid()
        m = s.save()
        run = Run.create_from_template(m)

        self.assertEqual(
            m.id,
            RunSerializer(run).data['template']['id'])

    def testRenderFlat(self):
        s = TemplateSerializer(data=fixtures.templates.flat_workflow)
        s.is_valid()
        m = s.save()
        run = Run.create_from_template(m)

        self.assertEqual(
            m.id,
            RunSerializer(run).data['template']['id'])
