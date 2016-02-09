from analysis.models import *
from django.conf import settings
from django.test import TestCase
import os
import sys
from loom.common import fixtures
from loom.common.fixtures.workflow_run_requests import hello_world
from .common import UniversalModelTestMixin


class TestWorkflowRunRequestModels(TestCase, UniversalModelTestMixin):

    def testRequestedDockerImage(self):
        o = RequestedDockerImage.create(fixtures.docker_image_struct)
        self.assertEqual(o.docker_image, fixtures.docker_image_struct['docker_image'])
        self.roundTripJson(o)
        self.roundTripStruct(o)

    def testRequestedEnvironment(self):
        o = RequestedEnvironment.create(fixtures.docker_image_struct)
        self.assertEqual(o.docker_image, fixtures.docker_image_struct['docker_image'])
        self.roundTripJson(o)
        self.roundTripStruct(o)

    def testRequestedResourceSet(self):
        o = RequestedResourceSet.create(fixtures.resource_set_struct)
        self.assertEqual(o.cores, fixtures.resource_set_struct['cores'])
        self.roundTripJson(o)
        self.roundTripStruct(o)

    def testStepRunRequest(self):
        o = StepRunRequest.create(fixtures.step_run_request_1_struct)
        self.assertEqual(o.name, fixtures.step_run_request_1_struct['name'])
        self.roundTripJson(o)
        self.roundTripStruct(o)

    def testWorkflowRunRequest(self):
        o = WorkflowRunRequest.create(fixtures.workflow_run_request_struct)
        self.assertEqual(o.step_run_requests.count(), len(fixtures.workflow_run_request_struct['step_run_requests']))
        self.roundTripJson(o)
        self.roundTripStruct(o)

class TestWorkflowRunRequestMethods(TestCase):
    
    def testWorkflowRunRequestsReverseSorted(self):
        count = 5
        for i in range(count):
            WorkflowRunRequest.create(fixtures.workflow_run_request_struct)
        wf_list = WorkflowRunRequest.order_by_most_recent()
        for i in range(1, count):
            self.assertTrue(wf_list[i-1].datetime_created > wf_list[i].datetime_created)

    def testWorkflowRunRequestNoCount(self):
        count = 5
        for i in range(count):
            WorkflowRunRequest.create(fixtures.workflow_run_request_struct)
        wf_list = WorkflowRunRequest.order_by_most_recent()
        self.assertEqual(len(wf_list), count)

    def testWorkflowRunRequestWithCount(self):
        count = 5
        for i in range(count):
            WorkflowRunRequest.create(fixtures.workflow_run_request_struct)

        wf_list_full = WorkflowRunRequest.order_by_most_recent()
        wf_list_truncated = WorkflowRunRequest.order_by_most_recent(count-1)
        wf_list_untruncated = WorkflowRunRequest.order_by_most_recent(count+1)

        # Truncated list should start with the newest record
        self.assertEqual(wf_list_full[0].datetime_created, wf_list_truncated[0].datetime_created)

        # Length should match count
        self.assertEqual(len(wf_list_truncated), count-1)

        # If count is greater than available elements, all elements should be present
        self.assertEqual(len(wf_list_untruncated), count)
        
