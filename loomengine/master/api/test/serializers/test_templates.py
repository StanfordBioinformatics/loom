import copy
from django.test import TestCase, TransactionTestCase, override_settings
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from . import fixtures
from . import get_mock_request, get_mock_context
from api.test.fixtures.many_steps import generator
from api.serializers.templates import *

@override_settings(TEST_DISABLE_ASYNC_DELAY=True)
class TestTemplateInputSerializer(TestCase):

    def testCreate(self):
        template = Template(command='test command',
                        name='test',
                        is_leaf=True)
        template.save()

        s = TemplateInputSerializer(
            data=fixtures.templates.template_input,
            context={'parent_field': 'template',
                     'parent_instance': template})
        s.is_valid(raise_exception=True)
        template_input = s.save()

        self.assertEqual(
            template_input.data_object.substitution_value,
            fixtures.templates.template_input['data']['contents'])


    def testRender(self):
        step = Template(command='test command',
                        name='test',
                        is_leaf=True)
        step.save()

        s = TemplateInputSerializer(
            data=fixtures.templates.template_input,
            context={'parent_field': 'template',
                     'parent_instance': step})
        s.is_valid(raise_exception=True)
        template_input = s.save()

        s2 = TemplateInputSerializer(template_input, context=get_mock_context())
        self.assertTrue('uuid' in s2.data['data'].keys())


@override_settings(TEST_DISABLE_ASYNC_DELAY=True)
class TestTemplateSerializer(TransactionTestCase):

    def testCreateStep(self):
        with self.settings(TEST_DISABLE_ASYNC_DELAY=True):
            s = TemplateSerializer(data=fixtures.templates.step_a)
            s.is_valid(raise_exception=True)
            m = s.save()

        self.assertEqual(m.command, fixtures.templates.step_a['command'])
        self.assertEqual(
            m.get_input('a2').data_object.substitution_value,
            fixtures.templates.step_a['inputs'][1]['data']['contents'])

    def testCreateFlatWorkflow(self):
        with self.settings(TEST_DISABLE_ASYNC_DELAY=True):
            s = TemplateSerializer(data=fixtures.templates.flat_workflow)
            s.is_valid(raise_exception=True)
            m = s.save()
    
        self.assertEqual(
            m.steps.first().command, 
            fixtures.templates.flat_workflow['steps'][0]['command'])
        self.assertEqual(
            m.get_input('b2').data_object.substitution_value,
            fixtures.templates.flat_workflow['inputs'][1]['data']['contents'])

    def testCreateNestedWorkflow(self):
        with self.settings(TEST_DISABLE_ASYNC_DELAY=True):
            s = TemplateSerializer(data=fixtures.templates.nested_workflow)
            s.is_valid(raise_exception=True)
            m = s.save()

        self.assertEqual(
            m.steps.first().steps.first().command,
            fixtures.templates.nested_workflow[
                'steps'][0]['steps'][0]['command'])
        self.assertEqual(
            m.inputs.first().data_object.substitution_value,
            fixtures.templates.nested_workflow['inputs'][0]['data']['contents'])

    def testCreateNestedWorkflowByReference(self):
        """Create a step first, then define a workflow that references
        that step by its ID
        """
        with self.settings(TEST_DISABLE_ASYNC_DELAY=True):
            workflow = copy.deepcopy(fixtures.templates.nested_workflow)
            step = workflow['steps'].pop()
            s = TemplateSerializer(data=step)
            s.is_valid(raise_exception=True)
            step_obj = s.save()
            step_id = '%s@%s' % (step_obj.name, step_obj.uuid)
            workflow['steps'].append(step_id)
            s = TemplateSerializer(data=workflow)
            s.is_valid()
            workflow_obj = s.save()

            self.assertEqual(workflow_obj.steps.count(), len(workflow['steps']))

    def testRender(self):
        s = TemplateSerializer(data=fixtures.templates.nested_workflow)
        s.is_valid(raise_exception=True)
        m = s.save()

        s2 = TemplateSerializer(m, context=get_mock_context())
        self.assertEqual(s2.data['name'], 'nested')

    def testCreationPostprocessing(self):

        STEP_COUNT=2
        
        data = generator.make_many_steps(STEP_COUNT)

        s = TemplateSerializer(data=data)
        s.is_valid(raise_exception=True)
        m = s.save()

        self.assertTrue(m.steps.count() == STEP_COUNT+1)
