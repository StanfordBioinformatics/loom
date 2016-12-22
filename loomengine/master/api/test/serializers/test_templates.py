from rest_framework.test import RequestsClient
import datetime
from django.test import TestCase, TransactionTestCase
import loomengine.utils.helper

from . import fixtures
import fixtures.run_fixtures.many_steps.generator
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
        with self.settings(TEST_DISABLE_TASK_DELAY=True,
                           WORKER_TYPE='MOCK'):
            s = StepSerializer(data=fixtures.templates.step_a)
            s.is_valid()
            m = s.save()

        self.assertEqual(m.command, fixtures.templates.step_a['command'])
        self.assertEqual(
            m.fixed_inputs.first().data_root.data_object.substitution_value,
            fixtures.templates.step_a['fixed_inputs'][0]['data']['contents'])

    def testRender(self):
        with self.settings(TEST_DISABLE_TASK_DELAY=True,
                           WORKER_TYPE='MOCK'):
            s = StepSerializer(data=fixtures.templates.step_a)
            s.is_valid()
            m = s.save()

        self.assertEqual(m.command, s.data['command'])


class TestWorkflowSerializer(TransactionTestCase):

    @classmethod
    def isWorkflowReady(cls, workflow_id):
        return Workflow.objects.get(id=workflow_id).saving_status == 'ready'

    def testCreateFlatWorkflow(self):
        with self.settings(TEST_DISABLE_TASK_DELAY=True,
                           WORKER_TYPE='MOCK'):
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
        with self.settings(TEST_DISABLE_TASK_DELAY=True,
                           WORKER_TYPE='MOCK'):

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
        with self.settings(TEST_DISABLE_TASK_DELAY=True,
                           WORKER_TYPE='MOCK'):
            s = WorkflowSerializer(data=fixtures.templates.nested_workflow)
            s.is_valid()
            m = s.save()

        self.assertEqual(s.data['name'], 'nested')

class TestTemplateSerializer(TransactionTestCase):

    def testCreateStep(self):
        with self.settings(TEST_DISABLE_TASK_DELAY=True,
                           WORKER_TYPE='MOCK'):
            s = TemplateSerializer(data=fixtures.templates.step_a)
            s.is_valid()
            m = s.save()

        self.assertEqual(m.step.command, fixtures.templates.step_a['command'])
        self.assertEqual(
            m.fixed_inputs.first().data_root.data_object.substitution_value,
            fixtures.templates.step_a['fixed_inputs'][0]['data']['contents'])

    def testCreateFlatWorkflow(self):
        with self.settings(TEST_DISABLE_TASK_DELAY=True,
                           WORKER_TYPE='MOCK'):
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
        with self.settings(TEST_DISABLE_TASK_DELAY=True,
                           WORKER_TYPE='MOCK'):
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
        with self.settings(TEST_DISABLE_TASK_DELAY=True,
                           WORKER_TYPE='MOCK'):
            s = TemplateSerializer(data=fixtures.templates.nested_workflow)
            s.is_valid()
            m = s.save()

        s2 = TemplateSerializer(m)
        self.assertEqual(s2.data['name'], 'nested')

    def testCreationTime(self):
        # We're measuring request time, not total generation time with
        # postprocessing
        with self.settings(TEST_NO_POSTPROCESS=True):
                
            data1000 = fixtures.run_fixtures.many_steps\
                                          .generator.make_many_steps(1000)

            s = TemplateSerializer(data=data1000)
            tic1000 = datetime.datetime.now()
            s.is_valid(raise_exception=True)
            m = s.save()
            time1000 = datetime.datetime.now() - tic1000

            # Create template with 1000 steps in under 500 ms
            self.assertTrue(time1000.total_seconds() < 0.5)

    def testCreationPostprocessingTime(self):
        # We're measuring total time to create a new template,
        # which includes postprocessing after the response to
        # the initial request.

        data100 = fixtures.run_fixtures.many_steps\
                                           .generator.make_many_steps(100)

        s = TemplateSerializer(data=data100)
        tic100 = datetime.datetime.now()
        s.is_valid(raise_exception=True)
        m = s.save()
        self._wait_for_postprocessing(m)
        time100 = datetime.datetime.now() - tic100

        # Create template with 1000 steps in under 500 ms
        self.assertTrue(time100.total_seconds() < 10)

    def testRenderTime(self):
        data100 = fixtures.run_fixtures.many_steps\
                                       .generator.make_many_steps(100)

        s = TemplateSerializer(data=data100)
        s.is_valid(raise_exception=True)
        m100 = s.save()

        self._wait_for_postprocessing(m100)

        client = RequestsClient()

        tic100 = datetime.datetime.now()
        response = client.get(
            'http://testserver/api/templates/%s/' % m100.uuid)
        time100 = datetime.datetime.now() - tic100

        # Render template with 100 steps in under 500 ms
        self.assertTrue(time100.total_seconds() < 0.5)

        
        
    def _wait_for_postprocessing(self, template):
        loomengine.utils.helper.wait_for_true(
            lambda: Template.objects.get(id=template.id).saving_status=='ready',
            timeout_seconds=120,
            sleep_interval=1)
        loomengine.utils.helper.wait_for_true(
            lambda: all([step.saving_status=='ready' for step in Template.objects.get(id=template.id).workflow.steps.all()]),
            timeout_seconds=120,
            sleep_interval=1)
