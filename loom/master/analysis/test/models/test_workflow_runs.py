from analysis.models import *
from analysis.exceptions import *
from django.conf import settings
from django.test import TestCase
import os
import sys
from loom.common import fixtures
from loom.common.fixtures.workflows import hello_world
from .common import UniversalModelTestMixin


class TestWorkflowRunModels(TestCase, UniversalModelTestMixin):

    def testWorkflowRun(self):
        o = WorkflowRun.create(fixtures.workflow_run_struct)
        self.assertEqual(
            o.workflow_run_inputs.first().workflow_input.to_channel,
            fixtures.workflow_run_struct['workflow_run_inputs'][0]\
            ['workflow_input']['to_channel']
        )
        self.roundTripJson(o)
        self.roundTripStruct(o)

class TestWorkflowRunEndToEnd(TestCase, UniversalModelTestMixin):
    
    def testStraightPipeSuccessfulRun(self):
        workflow = fixtures.straight_pipe_workflow_struct
        input_data_object = fixtures.straight_pipe_workflow_input_file_struct
        workflow_run_struct = {
            'workflow': workflow,
            'workflow_run_inputs': [
                {
                    'workflow_input': workflow['workflow_inputs'][0],
                    'data_object': input_data_object
                }
            ]
        }
        
        workflow_run = WorkflowRun.create(workflow_run_struct)

        # The WorkflowRun should be in 'running' status
        self.assertEqual(workflow_run.status, 'running')
        # There should be two StepRuns
        self.assertEqual(workflow_run.step_runs.count(), 2)
        # They should both be in 'waiting' status
        self.assertEqual(workflow_run.step_runs.all()[0].status, 'waiting')
        self.assertEqual(workflow_run.step_runs.all()[1].status, 'waiting')
        # There should be no TaskRuns
        self.assertEqual(workflow_run.step_runs.all()[0].task_runs.count(), 0)
        self.assertEqual(workflow_run.step_runs.all()[1].task_runs.count(), 0)

        # Call update_and_run
        workflow_run.update_and_run(dummy_run=True)
        
        """
        # The WorkflowRun should be in 'running' status
        self.assertEqual(workflow_run.status, 'running')
        # There should be two StepRuns
        self.assertEqual(workflow_run.step_runs.count(), 2)
        # The first should be in 'completed' status, the second in 'waiting'
        self.assertEqual(workflow_run.step_runs.all()[0].status, 'completed')
        self.assertEqual(workflow_run.step_runs.all()[1].status, 'waiting')
        # There should be one TaskRun on the first step, none on the second
        self.assertEqual(workflow_run.step_runs.all()[0].task_runs.count(), 1)
        self.assertEqual(workflow_run.step_runs.all()[1].task_runs.count(), 0)
        # The TaskRun should be in 'completed' status and should have a result
        self.assertEqual(workflow_run.step_runs.all()[0].task_runs.first().status, 'completed')
        self.assertTrue(workflow_run.step_runs.first().task_runs.first().task_run_outputs.first().has_result())

        # Call update_and_run
        workflow_run.update_and_run(dummy_run=True)
        """
        
        # The WorkflowRun should be in 'completed' status
        self.assertEqual(workflow_run.status, 'completed')
        # There should be two StepRuns
        self.assertEqual(workflow_run.step_runs.count(), 2)
        # The both should be in 'completed' status.
        self.assertEqual(workflow_run.step_runs.all()[0].status, 'completed')
        self.assertEqual(workflow_run.step_runs.all()[1].status, 'completed')
        # There should be one TaskRun on each step
        self.assertEqual(workflow_run.step_runs.all()[0].task_runs.count(), 1)
        self.assertEqual(workflow_run.step_runs.all()[1].task_runs.count(), 1)
        # The TaskRuns should be in 'completed' status and should have a result
        self.assertEqual(workflow_run.step_runs.all()[0].task_runs.first().status, 'completed')
        self.assertTrue(workflow_run.step_runs.all()[0].task_runs.first().task_run_outputs.first().has_result())
        self.assertEqual(workflow_run.step_runs.all()[1].task_runs.first().status, 'completed')
        self.assertTrue(workflow_run.step_runs.all()[1].task_runs.first().task_run_outputs.first().has_result())
        

class TestStepRun(TestCase, UniversalModelTestMixin):

    def testAreInputsReady(self):
        workflow_run = WorkflowRun.create(fixtures.workflow_run_struct)
        self.assertTrue(workflow_run.step_runs.all()[0]._are_inputs_ready())
        self.assertFalse(workflow_run.step_runs.all()[1]._are_inputs_ready())

    def testGetTaskInputs(self):
        workflow_run = WorkflowRun.create(fixtures.workflow_run_struct)
        self.assertEqual(len(workflow_run.step_runs.all()[0]._get_task_inputs()), 0)

        with self.assertRaises(MissingInputsError):
            inputs = self.assertIsNone(workflow_run.step_runs.all()[1]._get_task_inputs())
    
"""
class TestWorkflowRunMethods(TestCase):

    def testWorkflowRunsReverseSorted(self):
        count = 5
        for i in range(count):
            WorkflowRun.create(fixtures.workflow_run_struct)
        wf_list = WorkflowRun.order_by_most_recent()
        for i in range(1, count):
            self.assertTrue(wf_list[i-1].datetime_created > wf_list[i].datetime_created)

    def testWorkflowRunNoCount(self):
        count = 5
        for i in range(count):
            WorkflowRun.create(fixtures.workflow_run_struct)
        wf_list = WorkflowRun.order_by_most_recent()
        self.assertEqual(len(wf_list), count)

    def testWorkRunRequestflowWithCount(self):
        count = 5
        for i in range(count):
            WorkflowRun.create(fixtures.workflow_run_struct)

        wf_list_full = WorkflowRun.order_by_most_recent()
        wf_list_truncated = WorkflowRun.order_by_most_recent(count-1)
        wf_list_untruncated = WorkflowRun.order_by_most_recent(count+1)

        # Truncated list should start with the newest record
        self.assertEqual(wf_list_full[0].datetime_created, wf_list_truncated[0].datetime_created)

        # Length should match count
        self.assertEqual(len(wf_list_truncated), count-1)

        # If count is greater than available elements, all elements should be present
        self.assertEqual(len(wf_list_untruncated), count)
    
class TestWorkflowRunInitChannels(TestCase):

    def testInitializeWorkflow(self):
        wfrun = WorkflowRun.create(fixtures.hello_world_workflow_run_struct)
        self.assertTrue(True)
"""
