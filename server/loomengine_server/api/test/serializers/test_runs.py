import datetime
from django.test import TestCase, TransactionTestCase, override_settings
from rest_framework.serializers import ValidationError

from . import fixtures, get_mock_request, create_run_from_template
from . import get_mock_context
from api.serializers.templates import *
from api.serializers.runs import *
from api.models.runs import Run

@override_settings(TEST_DISABLE_ASYNC_DELAY=True,
                   TEST_NO_PUSH_INPUTS=True)
class TestRunSerializer(TransactionTestCase):

    def testCreateWithMissingInput(self):

        count_before = Run.objects.count()

        s = TemplateSerializer(data=fixtures.templates.step_b)
        s.is_valid(raise_exception=True)
        m = s.save()
        run_dict = {
            'template': '@%s' % m.uuid,
            'user_inputs': [
                {
                    'channel': 'b1',
                    'data': { 'contents': 'missingfile' }
                },
                {
                    'channel': 'b2',
                    'data': { 'contents': 'missingfile' }
                },
                {
                    'channel': 'b3',
                    'data': { 'contents': 'validstring' }
                }
            ]
        }
        s = RunSerializer(data=run_dict)
        try:
            s.is_valid(raise_exception=True)
            m = s.save()
        except ValidationError:
            pass

        count_after = Run.objects.count()
        self.assertEqual(count_before, count_after)

    def testRender(self):
        s = TemplateSerializer(data=fixtures.templates.step_a)
        s.is_valid(raise_exception=True)
        m = s.save()
        # Refresh to update postprocessing_status
        m = Template.objects.get(id=m.id)
        run = create_run_from_template(m)

        self.assertEqual(
            m.uuid,
            RunSerializer(run, context=get_mock_context()).data[
                'template']['uuid'])
            
            

    def testRenderFlat(self):
        s = TemplateSerializer(data=fixtures.templates.flat_workflow)
        s.is_valid(raise_exception=True)
        m = s.save()
        run = create_run_from_template(m)

        self.assertEqual(
            m.uuid,
            RunSerializer(run, context=get_mock_context()).data[
                'template']['uuid'])

    def testRenderNested(self):
        s = TemplateSerializer(data=fixtures.templates.nested_workflow)
        s.is_valid(raise_exception=True)
        m = s.save()
        run = create_run_from_template(m)

        self.assertEqual(
            m.uuid,
            RunSerializer(run, context=get_mock_context()).data[
                'template']['uuid'])
