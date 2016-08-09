import copy
from django.test import TestCase

from analysis.test import fixtures
from analysis.serializers.run_requests import *
from analysis.serializers.workflows import AbstractWorkflowSerializer


class TestRunRequestSerializer(TestCase):

    def testCreate(self):
        s = AbstractWorkflowSerializer(data=fixtures.workflows.flat_workflow)
        s.is_valid()
        workflow = s.save()
        workflow_id = '%s@%s' % (workflow.name, workflow.id.hex)

        run_request_data = {
            'template': workflow_id,
            'inputs': [
                fixtures.run_requests.run_request_input,
            ]
        }
        
        s = RunRequestSerializer(
            data=run_request_data)
        s.is_valid()
        rr = s.save()

        self.assertEqual(
            rr.inputs.first().data_object.string_content.string_value,
            fixtures.run_requests.run_request_input['value'])

        self.assertEqual(
            RunRequestSerializer(rr).data['inputs'][0]['value'],
            fixtures.run_requests.run_request_input['value'])

        self.assertEqual(
            RunRequestSerializer(rr).data['template'],
            rr.template.get_name_and_id())

        self.assertEqual(rr.run.template.id, rr.template.id)

    def testCreateNested(self):
        s = AbstractWorkflowSerializer(data=fixtures.workflows.nested_workflow)
        s.is_valid()
        workflow = s.save()
        workflow_id = '%s@%s' % (workflow.name, workflow.id.hex)

        run_request_data = {'template': workflow_id}

        s = RunRequestSerializer(
            data=run_request_data)
        s.is_valid()
        rr = s.save()

        self.assertEqual(rr.run.template.name, workflow.name)
        self.assertEqual(rr.run.step_runs.first().template.name,
                         workflow.steps.first().name)

