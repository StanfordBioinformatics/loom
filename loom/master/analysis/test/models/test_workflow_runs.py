from analysis.models import *
from analysis.exceptions import *
from django.conf import settings
from django.test import TestCase
import os
import sys
from . import fixtures
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

        workflow_run.update_status()
        
        # The WorkflowRun should be in 'running' status
        self.assertEqual(workflow_run.status, 'running')
        # There should be two StepRuns
        self.assertEqual(workflow_run.step_runs.count(), 2)
        # The first should be in 'running' status, the second in 'waiting'
        self.assertEqual(workflow_run.step_runs.all()[0].status, 'running')
        self.assertEqual(workflow_run.step_runs.all()[1].status, 'waiting')
        # There should be one TaskRun on the first step, none on the second
        self.assertEqual(workflow_run.step_runs.all()[0].task_runs.count(), 1)
        self.assertEqual(workflow_run.step_runs.all()[1].task_runs.count(), 0)
        # The TaskRun should be in 'ready_to_run' status and should not have a result.
        self.assertEqual(workflow_run.step_runs.all()[0].task_runs.first().status, 'ready_to_run')
        self.assertFalse(workflow_run.step_runs.first().task_runs.first().task_run_outputs.first().has_result())

        # Run all TaskRuns that are ready
        TaskRun.dummy_run_all()

        # The WorkflowRun should be in 'running' status
        self.assertEqual(workflow_run.status, 'running')
        # There should be two StepRuns
        self.assertEqual(workflow_run.step_runs.count(), 2)
        # The first should be in 'running' status, the second in 'waiting'
        self.assertEqual(workflow_run.step_runs.all()[0].status, 'running')
        self.assertEqual(workflow_run.step_runs.all()[1].status, 'waiting')
        # There should be one TaskRun on the first step, none on the second
        self.assertEqual(workflow_run.step_runs.all()[0].task_runs.count(), 1)
        self.assertEqual(workflow_run.step_runs.all()[1].task_runs.count(), 0)
        # The TaskRun should be in 'running' status and should have a result.
        self.assertEqual(workflow_run.step_runs.all()[0].task_runs.first().status, 'running')
        self.assertTrue(workflow_run.step_runs.first().task_runs.first().task_run_outputs.first().has_result())

        workflow_run.update_status()
        
        # The WorkflowRun should be in 'running' status
        self.assertEqual(workflow_run.status, 'running')
        # There should be two StepRun
        self.assertEqual(workflow_run.step_runs.count(), 2)
        # The first should have 'completed' status, and the second should be 'running'
        self.assertEqual(workflow_run.step_runs.all()[0].status, 'completed')
        self.assertEqual(workflow_run.step_runs.all()[1].status, 'running')
        # There should be one TaskRun on each step
        self.assertEqual(workflow_run.step_runs.all()[0].task_runs.count(), 1)
        self.assertEqual(workflow_run.step_runs.all()[1].task_runs.count(), 1)
        # The first TaskRun should be in 'completed' status and should have a result
        self.assertEqual(workflow_run.step_runs.all()[0].task_runs.first().status, 'completed')
        self.assertTrue(workflow_run.step_runs.all()[0].task_runs.first().task_run_outputs.first().has_result())
        # The second TaskRun should be in 'ready_to_run' status and have no result
        self.assertEqual(workflow_run.step_runs.all()[1].task_runs.first().status, 'ready_to_run')
        self.assertFalse(workflow_run.step_runs.all()[1].task_runs.first().task_run_outputs.first().has_result())

        # Run all TaskRuns that are ready
        TaskRun.dummy_run_all()

        # The WorkflowRun should be in 'running' status
        self.assertEqual(workflow_run.status, 'running')
        # There should be two StepRun
        self.assertEqual(workflow_run.step_runs.count(), 2)
        # The first should have 'completed' status, and the second should be 'running'
        self.assertEqual(workflow_run.step_runs.all()[0].status, 'completed')
        self.assertEqual(workflow_run.step_runs.all()[1].status, 'running')
        # There should be one TaskRun on each step
        self.assertEqual(workflow_run.step_runs.all()[0].task_runs.count(), 1)
        self.assertEqual(workflow_run.step_runs.all()[1].task_runs.count(), 1)
        # The first TaskRun should be in 'completed' status and should have a result
        self.assertEqual(workflow_run.step_runs.all()[0].task_runs.first().status, 'completed')
        self.assertTrue(workflow_run.step_runs.all()[0].task_runs.first().task_run_outputs.first().has_result())
        # The second TaskRun should be in 'running' status and have a result
        self.assertEqual(workflow_run.step_runs.all()[1].task_runs.first().status, 'running')
        self.assertTrue(workflow_run.step_runs.all()[1].task_runs.first().task_run_outputs.first().has_result())

        workflow_run.update_status()

        # The WorkflowRun should be in 'completed' status
        self.assertEqual(workflow_run.status, 'completed')
        # There should be two StepRuns
        self.assertEqual(workflow_run.step_runs.count(), 2)
        # Both StepRuns should have 'completed' status
        self.assertEqual(workflow_run.step_runs.all()[0].status, 'completed')
        self.assertEqual(workflow_run.step_runs.all()[1].status, 'completed')
        # There should be one TaskRun on each step
        self.assertEqual(workflow_run.step_runs.all()[0].task_runs.count(), 1)
        self.assertEqual(workflow_run.step_runs.all()[1].task_runs.count(), 1)
        # Both TaskRuns should be in 'completed' status and should have a result
        self.assertEqual(workflow_run.step_runs.all()[0].task_runs.first().status, 'completed')
        self.assertTrue(workflow_run.step_runs.all()[0].task_runs.first().task_run_outputs.first().has_result())
        self.assertEqual(workflow_run.step_runs.all()[1].task_runs.first().status, 'completed')
        self.assertTrue(workflow_run.step_runs.all()[1].task_runs.first().task_run_outputs.first().has_result())

        
    def testStraightPipeCanceledRun(self):
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

        workflow_run.update_status()
        
        # The WorkflowRun should be in 'running' status
        self.assertEqual(workflow_run.status, 'running')
        # There should be two StepRuns
        self.assertEqual(workflow_run.step_runs.count(), 2)
        # The first should be in 'running' status, the second in 'waiting'
        self.assertEqual(workflow_run.step_runs.all()[0].status, 'running')
        self.assertEqual(workflow_run.step_runs.all()[1].status, 'waiting')
        # There should be one TaskRun on the first step, none on the second
        self.assertEqual(workflow_run.step_runs.all()[0].task_runs.count(), 1)
        self.assertEqual(workflow_run.step_runs.all()[1].task_runs.count(), 0)
        # The TaskRun should be in 'ready_to_run' status and should not have a result.
        self.assertEqual(workflow_run.step_runs.all()[0].task_runs.first().status, 'ready_to_run')
        self.assertFalse(workflow_run.step_runs.first().task_runs.first().task_run_outputs.first().has_result())

        # Run all TaskRuns that are ready
        TaskRun.dummy_run_all()

        # The WorkflowRun should be in 'running' status
        self.assertEqual(workflow_run.status, 'running')
        # There should be two StepRuns
        self.assertEqual(workflow_run.step_runs.count(), 2)
        # The first should be in 'running' status, the second in 'waiting'
        self.assertEqual(workflow_run.step_runs.all()[0].status, 'running')
        self.assertEqual(workflow_run.step_runs.all()[1].status, 'waiting')
        # There should be one TaskRun on the first step, none on the second
        self.assertEqual(workflow_run.step_runs.all()[0].task_runs.count(), 1)
        self.assertEqual(workflow_run.step_runs.all()[1].task_runs.count(), 0)
        # The TaskRun should be in 'running' status and should have a result.
        self.assertEqual(workflow_run.step_runs.all()[0].task_runs.first().status, 'running')
        self.assertTrue(workflow_run.step_runs.first().task_runs.first().task_run_outputs.first().has_result())

        workflow_run.update_status()
        
        # The WorkflowRun should be in 'running' status
        self.assertEqual(workflow_run.status, 'running')
        # There should be two StepRuns
        self.assertEqual(workflow_run.step_runs.count(), 2)
        # The first should have 'completed' status, and the second should be 'running'
        self.assertEqual(workflow_run.step_runs.all()[0].status, 'completed')
        self.assertEqual(workflow_run.step_runs.all()[1].status, 'running')
        # There should be one TaskRun on each step
        self.assertEqual(workflow_run.step_runs.all()[0].task_runs.count(), 1)
        self.assertEqual(workflow_run.step_runs.all()[1].task_runs.count(), 1)
        # The first TaskRun should be in 'completed' status and should have a result
        self.assertEqual(workflow_run.step_runs.all()[0].task_runs.first().status, 'completed')
        self.assertTrue(workflow_run.step_runs.all()[0].task_runs.first().task_run_outputs.first().has_result())
        # The second TaskRun should be in 'ready_to_run' status and have no result
        self.assertEqual(workflow_run.step_runs.all()[1].task_runs.first().status, 'ready_to_run')
        self.assertFalse(workflow_run.step_runs.all()[1].task_runs.first().task_run_outputs.first().has_result())

        # Run all TaskRuns that are ready
        TaskRun.dummy_run_all(finish=False)

        # The WorkflowRun should be in 'running' status
        self.assertEqual(workflow_run.status, 'running')
        # There should be two StepRun
        self.assertEqual(workflow_run.step_runs.count(), 2)
        # The first should have 'completed' status, and the second should be 'running'
        self.assertEqual(workflow_run.step_runs.all()[0].status, 'completed')
        self.assertEqual(workflow_run.step_runs.all()[1].status, 'running')
        # There should be one TaskRun on each step
        self.assertEqual(workflow_run.step_runs.all()[0].task_runs.count(), 1)
        self.assertEqual(workflow_run.step_runs.all()[1].task_runs.count(), 1)
        # The first TaskRun should be in 'completed' status and should have a result
        self.assertEqual(workflow_run.step_runs.all()[0].task_runs.first().status, 'completed')
        self.assertTrue(workflow_run.step_runs.all()[0].task_runs.first().task_run_outputs.first().has_result())
        # The second TaskRun should be in 'running' status but have no result
        self.assertEqual(workflow_run.step_runs.all()[1].task_runs.first().status, 'running')
        self.assertFalse(workflow_run.step_runs.all()[1].task_runs.first().task_run_outputs.first().has_result())

        workflow_run.cancel()

        # The WorkflowRun should be in 'canceled' status
        self.assertEqual(workflow_run.status, 'canceled')
        # There should be two StepRuns
        self.assertEqual(workflow_run.step_runs.count(), 2)
        # One is completed, one is canceled.
        self.assertEqual(workflow_run.step_runs.all()[0].status, 'completed')
        self.assertEqual(workflow_run.step_runs.all()[1].status, 'canceled')
        # There should be one TaskRun on each step
        self.assertEqual(workflow_run.step_runs.all()[0].task_runs.count(), 1)
        self.assertEqual(workflow_run.step_runs.all()[1].task_runs.count(), 1)
        # One TaskRun should be completed and have a result
        self.assertEqual(workflow_run.step_runs.all()[0].task_runs.first().status, 'completed')
        self.assertTrue(workflow_run.step_runs.all()[0].task_runs.first().task_run_outputs.first().has_result())
        # The other TaskRun should be canceled and have no result
        self.assertEqual(workflow_run.step_runs.all()[1].task_runs.first().status, 'canceled')
        self.assertFalse(workflow_run.step_runs.all()[1].task_runs.first().task_run_outputs.first().has_result())

    def testStraightPipeErrorRun(self):
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

        workflow_run.update_status()
        
        # The WorkflowRun should be in 'running' status
        self.assertEqual(workflow_run.status, 'running')
        # There should be two StepRuns
        self.assertEqual(workflow_run.step_runs.count(), 2)
        # The first should be in 'running' status, the second in 'waiting'
        self.assertEqual(workflow_run.step_runs.all()[0].status, 'running')
        self.assertEqual(workflow_run.step_runs.all()[1].status, 'waiting')
        # There should be one TaskRun on the first step, none on the second
        self.assertEqual(workflow_run.step_runs.all()[0].task_runs.count(), 1)
        self.assertEqual(workflow_run.step_runs.all()[1].task_runs.count(), 0)
        # The TaskRun should be in 'ready_to_run' status and should not have a result.
        self.assertEqual(workflow_run.step_runs.all()[0].task_runs.first().status, 'ready_to_run')
        self.assertFalse(workflow_run.step_runs.first().task_runs.first().task_run_outputs.first().has_result())

        # Run all TaskRuns that are ready
        TaskRun.dummy_run_all()

        # The WorkflowRun should be in 'running' status
        self.assertEqual(workflow_run.status, 'running')
        # There should be two StepRuns
        self.assertEqual(workflow_run.step_runs.count(), 2)
        # The first should be in 'running' status, the second in 'waiting'
        self.assertEqual(workflow_run.step_runs.all()[0].status, 'running')
        self.assertEqual(workflow_run.step_runs.all()[1].status, 'waiting')
        # There should be one TaskRun on the first step, none on the second
        self.assertEqual(workflow_run.step_runs.all()[0].task_runs.count(), 1)
        self.assertEqual(workflow_run.step_runs.all()[1].task_runs.count(), 0)
        # The TaskRun should be in 'running' status and should have a result.
        self.assertEqual(workflow_run.step_runs.all()[0].task_runs.first().status, 'running')
        self.assertTrue(workflow_run.step_runs.first().task_runs.first().task_run_outputs.first().has_result())

        workflow_run.update_status()
        
        # The WorkflowRun should be in 'running' status
        self.assertEqual(workflow_run.status, 'running')
        # There should be two StepRuns
        self.assertEqual(workflow_run.step_runs.count(), 2)
        # The first should have 'completed' status, and the second should be 'running'
        self.assertEqual(workflow_run.step_runs.all()[0].status, 'completed')
        self.assertEqual(workflow_run.step_runs.all()[1].status, 'running')
        # There should be one TaskRun on each step
        self.assertEqual(workflow_run.step_runs.all()[0].task_runs.count(), 1)
        self.assertEqual(workflow_run.step_runs.all()[1].task_runs.count(), 1)
        # The first TaskRun should be in 'completed' status and should have a result
        self.assertEqual(workflow_run.step_runs.all()[0].task_runs.first().status, 'completed')
        self.assertTrue(workflow_run.step_runs.all()[0].task_runs.first().task_run_outputs.first().has_result())
        # The second TaskRun should be in 'ready_to_run' status and have no result
        self.assertEqual(workflow_run.step_runs.all()[1].task_runs.first().status, 'ready_to_run')
        self.assertFalse(workflow_run.step_runs.all()[1].task_runs.first().task_run_outputs.first().has_result())

        # TaksRuns run and report an error
        TaskRun.dummy_run_all(with_error=True)

        # The WorkflowRun should be in 'running' status
        self.assertEqual(workflow_run.status, 'running')
        # There should be two StepRun
        self.assertEqual(workflow_run.step_runs.count(), 2)
        # The first should have 'completed' status, and the second should be 'running'
        self.assertEqual(workflow_run.step_runs.all()[0].status, 'completed')
        self.assertEqual(workflow_run.step_runs.all()[1].status, 'running')
        # There should be one TaskRun on each step
        self.assertEqual(workflow_run.step_runs.all()[0].task_runs.count(), 1)
        self.assertEqual(workflow_run.step_runs.all()[1].task_runs.count(), 1)
        # The first TaskRun should be in 'completed' status and should have a result
        self.assertEqual(workflow_run.step_runs.all()[0].task_runs.first().status, 'completed')
        self.assertTrue(workflow_run.step_runs.all()[0].task_runs.first().task_run_outputs.first().has_result())
        # The second TaskRun should be in 'error' status and have no result
        self.assertEqual(workflow_run.step_runs.all()[1].task_runs.first().status, 'error')
        self.assertFalse(workflow_run.step_runs.all()[1].task_runs.first().task_run_outputs.first().has_result())

        workflow_run.update_status()

        # The WorkflowRun should be in 'error' status
        self.assertEqual(workflow_run.status, 'error')
        # There should be two StepRuns
        self.assertEqual(workflow_run.step_runs.count(), 2)
        # One is completed, one is error
        self.assertEqual(workflow_run.step_runs.all()[0].status, 'completed')
        self.assertEqual(workflow_run.step_runs.all()[1].status, 'error')
        # There should be one TaskRun on each step
        self.assertEqual(workflow_run.step_runs.all()[0].task_runs.count(), 1)
        self.assertEqual(workflow_run.step_runs.all()[1].task_runs.count(), 1)
        # One TaskRun should be completed and have a result
        self.assertEqual(workflow_run.step_runs.all()[0].task_runs.first().status, 'completed')
        self.assertTrue(workflow_run.step_runs.all()[0].task_runs.first().task_run_outputs.first().has_result())
        # The other TaskRun should have 'error' status and have no result
        self.assertEqual(workflow_run.step_runs.all()[1].task_runs.first().status, 'error')
        self.assertFalse(workflow_run.step_runs.all()[1].task_runs.first().task_run_outputs.first().has_result())


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
