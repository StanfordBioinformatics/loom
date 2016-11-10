from django.test import TestCase
from api.models.data_objects import *
from api.models.runs import *

def get_step_run():
    step_run = StepRun.objects.create(
        command='echo hey',
        interpreter='/bin/bash',
    )
    StepRunInput.objects.create(
        step_run = step_run,
        channel = 'input1',
        type = 'file',
        mode = 'no_gather',
        group = 0
    )
    FixedStepRunInput.objects.create(
        step_run = step_run,
        channel = 'input2',
        type = 'file',
        mode = 'no_gather',
        group = 0
    )
    StepRunOutput.objects.create(
        step_run = step_run,
        channel = 'output1',
        type = 'file',
        mode = 'no_scatter',
    )
    StepRunDockerEnvironment.objects.create(
        step_run = step_run,
        docker_image = 'ubuntu'
    )
    StepRunResourceSet.objects.create(
        step_run = step_run,
        memory = 1,
        disk_size = 1,
        cores = 1
    )
    return step_run

def get_workflow_run():
    workflow_run = WorkflowRun.objects.create(
        name = 'workflow1',
        type = 'workflow')
    workflow_run.add_step(get_step_run())
    return workflow_run

class TestStepRun(TestCase):

    def testCreate(self):
        step_run = get_step_run()
        self.assertTrue(step_run.command.startswith('echo'))

class TestWorkflowRun(TestCase):

    def testCreate(self):
        workflow_run = get_workflow_run()
        self.assertTrue(workflow_run.name == 'workflow1')
