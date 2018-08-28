import copy
from django.test import TestCase

from . import fixtures
from . import get_mock_request, get_mock_context
from api.serializers.templates import *
from rest_framework import serializers

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
            template_input.data_node.substitution_value,
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


class TestTemplateSerializer(TestCase):

    def testCreateStep(self):
        s = TemplateSerializer(data=fixtures.templates.step_a)
        s.is_valid(raise_exception=True)
        m = s.save()

        self.assertEqual(m.command, fixtures.templates.step_a['command'])
        self.assertEqual(
            m.get_input('a2').data_node.substitution_value,
            fixtures.templates.step_a['inputs'][1]['data']['contents'])

    def testCreateFlatWorkflow(self):
        s = TemplateSerializer(data=fixtures.templates.flat_workflow)
        s.is_valid(raise_exception=True)
        m = s.save()
    
        self.assertEqual(
            m.steps.first().command, 
            fixtures.templates.flat_workflow['steps'][0]['command'])
        self.assertEqual(
            m.get_input('b2').data_node.substitution_value,
            fixtures.templates.flat_workflow['inputs'][1]['data']['contents'])

    def testCreateNestedWorkflow(self):
        s = TemplateSerializer(data=fixtures.templates.nested_workflow)
        s.is_valid(raise_exception=True)
        m = s.save()

        self.assertEqual(
            m.steps.first().steps.first().command,
            fixtures.templates.nested_workflow[
                'steps'][0]['steps'][0]['command'])
        self.assertEqual(
            m.inputs.first().data_node.substitution_value,
            fixtures.templates.nested_workflow['inputs'][0]['data']['contents'])

    def testCreateNestedWorkflowByReference(self):
        """Create a step first, then define a workflow that references
        that step by its ID
        """
        workflow = copy.deepcopy(fixtures.templates.nested_workflow)
        step = workflow['steps'].pop()
        s = TemplateSerializer(data=step)
        s.is_valid(raise_exception=True)
        step_obj = s.save()
        step_id = '%s@%s' % (step_obj.name, step_obj.uuid)
        workflow['steps'].append(step_id)
        s = TemplateSerializer(data=workflow, context=get_mock_context())
        s.is_valid(raise_exception=True)
        workflow_obj = s.save()

        self.assertEqual(workflow_obj.steps.count(), len(workflow['steps']))

    def testRender(self):
        s = TemplateSerializer(data=fixtures.templates.nested_workflow)
        s.is_valid(raise_exception=True)
        m = s.save()

        s2 = TemplateSerializer(m, context=get_mock_context())
        self.assertEqual(s2.data['name'], 'nested')

class TestTemplateSerializerValidate(TestCase):

    def testDuplicateChannelsNeg(self):
        s = TemplateSerializer(data=fixtures.templates.duplicate_channels)
        with self.assertRaises(serializers.ValidationError):
            s.is_valid(raise_exception=True)
            m = s.save()

    def testDuplicateSourcesNeg(self):
        s = TemplateSerializer(data=fixtures.templates.duplicate_sources)
        with self.assertRaises(serializers.ValidationError):
            s.is_valid(raise_exception=True)
            m = s.save()

    def testNoSourceNeg(self):
        s = TemplateSerializer(data=fixtures.templates.no_source)
        with self.assertRaises(serializers.ValidationError):
            s.is_valid(raise_exception=True)
            m = s.save()

    def testSourceTypeMismatchNeg(self):
        s = TemplateSerializer(data=fixtures.templates.source_type_mismatch)
        with self.assertRaises(serializers.ValidationError):
            s.is_valid(raise_exception=True)
            m = s.save()

    def testInvalidFileReferenceNeg(self):
        s = TemplateSerializer(data=fixtures.templates.missing_file_reference)
        with self.assertRaises(serializers.ValidationError):
            s.is_valid(raise_exception=True)
            m = s.save()

    def testInvalidTemplateReferenceNeg(self):
        s = TemplateSerializer(data=fixtures.templates.missing_template_reference)
        with self.assertRaises(serializers.ValidationError):
            s.is_valid(raise_exception=True)
            m = s.save()

    def testCycleNeg(self):
        s = TemplateSerializer(data=fixtures.templates.has_cycle)
        with self.assertRaises(serializers.ValidationError):
            s.is_valid(raise_exception=True)
            m = s.save()

    def testFixedInputDimensionMismatchNeg(self):
        s = TemplateSerializer(data=fixtures.templates.input_dimension_mismatch)
        with self.assertRaises(serializers.ValidationError):
            s.is_valid(raise_exception=True)
            m = s.save()
