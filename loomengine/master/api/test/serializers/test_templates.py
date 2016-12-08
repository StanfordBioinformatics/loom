from django.test import TestCase, TransactionTestCase

from . import fixtures
from api.serializers.templates import *


class TestFixedStepInputSerializer(TestCase):

    def testCreate(self):
        step = Step(command='test command')
        step.save()

        s = FixedStepInputSerializer(
            data=fixtures.templates.fixed_step_input,
            context={'parent_field': 'step',
                     'parent_instance': step})
        s.is_valid(raise_exception=True)
        fixed_input = s.save()

        self.assertEqual(
            fixed_input.data_root.data_object.substitution_value,
            fixtures.templates.fixed_step_input['data']['contents'])


    def testRender(self):
        step = Step(command='test command')
        step.save()

        s = FixedStepInputSerializer(
            data=fixtures.templates.fixed_step_input,
            context={'parent_field': 'step',
                     'parent_instance': step})
        s.is_valid(raise_exception=True)
        fixed_input = s.save()

        s2 = FixedStepInputSerializer(fixed_input)
        self.assertEqual(s2.data['data'].keys(),
                         ['uuid'])
        

class TestStepSerializer(TransactionTestCase):

    def testCreate(self):
        s = StepSerializer(data=fixtures.templates.step_a)
        s.is_valid()
        m = s.save()

        self.assertEqual(m.command, fixtures.templates.step_a['command'])
        self.assertEqual(
            m.fixed_inputs.first().data_root.data_object.substitution_value,
            fixtures.templates.step_a['fixed_inputs'][0]['data']['contents'])

    def testRender(self):
        s = StepSerializer(data=fixtures.templates.step_a)
        s.is_valid()
        m = s.save()

        self.assertEqual(m.command, s.data['command'])


class TestWorkflowSerializer(TestCase):

    def testCreateFlatWorkflow(self):
        s = WorkflowSerializer(data=fixtures.templates.flat_workflow)
        s.is_valid()
        m = s.save()

        self.assertEqual(
            m.steps.first().step.command,
            fixtures.templates.flat_workflow['steps'][0]['command'])
        self.assertEqual(
            m.fixed_inputs.first().data_root.data_object.substitution_value,
            fixtures.templates.flat_workflow['fixed_inputs'][0]['data']['contents'])

    def testCreateNestedWorkflow(self):
        s = WorkflowSerializer(data=fixtures.templates.nested_workflow)
        s.is_valid()
        m = s.save()

        self.assertEqual(
            m.steps.first().workflow.steps.first().step.command,
            fixtures.templates.nested_workflow[
                'steps'][0]['steps'][0]['command'])
        self.assertEqual(
            m.fixed_inputs.first().data_root.data_object.substitution_value,
            fixtures.templates.nested_workflow['fixed_inputs'][0]['data']['contents'])

    def testRender(self):
        s = WorkflowSerializer(data=fixtures.templates.nested_workflow)
        s.is_valid()
        m = s.save()

        self.assertEqual(s.data['name'], 'nested')

class TestTemplateSerializer(TestCase):

    def testCreateStep(self):
        s = TemplateSerializer(data=fixtures.templates.step_a)
        s.is_valid()
        m = s.save()

        self.assertEqual(m.step.command, fixtures.templates.step_a['command'])
        self.assertEqual(
            m.fixed_inputs.first().data_root.data_object.substitution_value,
            fixtures.templates.step_a['fixed_inputs'][0]['data']['contents'])

    def testCreateFlatWorkflow(self):
        s = TemplateSerializer(data=fixtures.templates.flat_workflow)
        s.is_valid()
        m = s.save()

        self.assertEqual(
            m.steps.first().step.command, 
            fixtures.templates.flat_workflow['steps'][0]['command'])
        self.assertEqual(
            m.fixed_inputs.first().data_root.data_object.substitution_value,
            fixtures.templates.flat_workflow['fixed_inputs'][0]['data']['contents'])

    def testCreateNestedWorkflow(self):
        s = TemplateSerializer(data=fixtures.templates.nested_workflow)
        s.is_valid()
        m = s.save()

        self.assertEqual(
            m.steps.first().workflow.steps.first().step.command,
            fixtures.templates.nested_workflow[
                'steps'][0]['steps'][0]['command'])
        self.assertEqual(
            m.fixed_inputs.first().data_root.data_object.substitution_value,
            fixtures.templates.nested_workflow['fixed_inputs'][0]['data']['contents'])

    def testRender(self):
        s = TemplateSerializer(data=fixtures.templates.nested_workflow)
        s.is_valid()
        m = s.save()

        s2 = TemplateSerializer(m)
        self.assertEqual(s2.data['name'], 'nested')

