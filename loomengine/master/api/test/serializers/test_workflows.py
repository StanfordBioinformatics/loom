from django.test import TestCase

from api.test import fixtures
from api.serializers.workflows import *

class TestFixedStepInputSerializer(TestCase):

    def testCreate(self):
        step = Step(command='test command')
        step.save()
        
        s = FixedStepInputSerializer(
            data=fixtures.workflows.fixed_step_input,
            context={'parent_field': 'step',
                     'parent_instance': step})
        s.is_valid()
        fixed_input = s.save()
        
        self.assertEqual(
            fixed_input.data_object.string_content.string_value,
            fixtures.workflows.fixed_step_input['value'])


class TestStepSerializer(TestCase):

    def testCreate(self):
        s = StepSerializer(data=fixtures.workflows.step_a)
        s.is_valid()
        m = s.save()

        self.assertEqual(m.command, fixtures.workflows.step_a['command'])
        self.assertEqual(
            m.fixed_inputs.first().data_object.string_content.string_value,
            fixtures.workflows.step_a['fixed_inputs'][0]['value'])


class TestWorkflowSerializer(TestCase):

    def testCreate(self):
        s = WorkflowSerializer(data=fixtures.workflows.flat_workflow)
        s.is_valid()
        m = s.save()

        self.assertEqual(
            m.fixed_inputs.first().data_object.string_content.string_value,
            fixtures.workflows.flat_workflow['fixed_inputs'][0]['value'])

    def testCreateNestedWorkflow(self):
        s = WorkflowSerializer(data=fixtures.workflows.nested_workflow)
        s.is_valid()
        m = s.save()

        self.assertEqual(
            m.fixed_inputs.first().data_object.string_content.string_value,
            fixtures.workflows.nested_workflow['fixed_inputs'][0]['value'])
        self.assertEqual(
            m.steps.first().name,
            fixtures.workflows.nested_workflow['steps'][0]['name'])

    def testRenderFixedInputValue(self):
        s = WorkflowSerializer(data=fixtures.workflows.flat_workflow)
        s.is_valid()
        m = s.save()

        data = WorkflowSerializer(m).data
        self.assertEqual(
            data['fixed_inputs'][0]['value'],
            m.fixed_inputs.first().data_object.string_content.string_value)
