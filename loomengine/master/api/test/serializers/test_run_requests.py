import copy
from django.test import TestCase, TransactionTestCase

from . import fixtures
from api.serializers.run_requests import *
from api.serializers.templates import TemplateSerializer
from api.models.data_trees import DataNode


class TestRunRequestSerializer(TransactionTestCase):

    def testCreate(self):
        with self.settings(DEBUG_DISABLE_TASK_DELAY=True,
                           WORKER_TYPE='MOCK'):
            s = TemplateSerializer(data=fixtures.templates.flat_workflow)
            s.is_valid(raise_exception=True)
            workflow = s.save()
            workflow_id = '%s@%s' % (workflow.name, workflow.uuid)

            run_request_data = {
                'template': workflow_id,
                'inputs': [
                    fixtures.run_requests.run_request_input,
                ]
            }

            s = RunRequestSerializer(
                data=run_request_data)
            s.is_valid(raise_exception=True)
            rr = s.save()

        self.assertEqual(
            rr.inputs.first().get_data_as_scalar().substitution_value,
            fixtures.run_requests.run_request_input['data']['contents'])

        data_tree = DataNode.objects.get(uuid=RunRequestSerializer(rr).data['inputs'][0]['data']['uuid'])
        self.assertEqual(
            data_tree.data_object.substitution_value,
            fixtures.run_requests.run_request_input['data']['contents'])

        self.assertEqual(
            RunRequestSerializer(rr).data['template']['uuid'],
            rr.template.uuid)

        self.assertEqual(rr.run.template.uuid, rr.template.uuid)

    def testCreateNested(self):
        with self.settings(DEBUG_DISABLE_TASK_DELAY=True,
                           WORKER_TYPE='MOCK'):
            s = TemplateSerializer(data=fixtures.templates.nested_workflow)
            s.is_valid(raise_exception=True)
            workflow = s.save()

            workflow_id = '%s@%s' % (workflow.name, workflow.uuid)

            run_request_data = {'template': workflow_id}

            s = RunRequestSerializer(
                data=run_request_data)
            s.is_valid(raise_exception=True)

            rr = s.save()

        self.assertEqual(rr.run.template.name, workflow.name)
        self.assertEqual(rr.run.steps.first().template.name,
                         workflow.steps.first().name)

