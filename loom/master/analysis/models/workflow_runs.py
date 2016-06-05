from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from analysis.exceptions import *
from .base import AnalysisAppInstanceModel, AnalysisAppImmutableModel
from .task_definitions import TaskDefinition
from .task_runs import TaskRun, TaskRunInput, TaskRunOutput
from .workflows import Workflow, Step, WorkflowInput, WorkflowOutput, StepInput, StepOutput
from universalmodels import fields


"""
This module defines WorkflowRun and other classes related to
running an analysis
"""

class AbstractWorkflowRun(AnalysisAppInstanceModel):
    """AbstractWorkflowRun represents the process of executing a Workflow on a particular
    set of inputs. The workflow may be either a Step or a Workflow composed of one or more Steps.
    """

    @classmethod
    def create_run_from_workflow(cls, workflow):

        workflow = workflow.downcast()

        def _add_inputs_outputs_from_workflow(run, workflow):
            run.update({
                'inputs': [{'channel': input.channel, 'type': input.type} for input in workflow.inputs.all()],
                'outputs': [{'channel': output.channel, 'type': output.type} for output in workflow.outputs.all()]
            })
            return run

        if workflow.is_step():
            run = {'step': workflow.to_struct()}
            run = _add_inputs_outputs_from_workflow(run, workflow)
            return StepRun.create(run)
        else:
            run = {'workflow': workflow.to_struct()}
            run = _add_inputs_outputs_from_workflow(run, workflow)
            return WorkflowRun.create(run)

    def is_step(self):
        return self.downcast().is_step()

    def get_input(self, channel):
        inputs=self.downcast().inputs.filter(channel=channel)
        assert inputs.count() == 1
        return inputs.first()


class WorkflowRun(AbstractWorkflowRun):

    NAME_FIELD = 'workflow__name'

    step_runs = fields.OneToManyField('AbstractWorkflowRun', related_name='parent_run')
    inputs = fields.OneToManyField('WorkflowRunInput', related_name='workflow_run')
    outputs = fields.OneToManyField('WorkflowRunOutput', related_name='workflow_run')
    workflow = fields.ForeignKey('Workflow')
    #status = fields.CharField(
    #    max_length=255,
    #    default='running',
    #    choices=(('running', 'Running'),
    #             ('stopped', 'Stopped'),
    #    )
    #)

    def is_step(self):
        return False

    def after_create_or_update(self):
        self._initialize_step_runs()
        self._initialize_channels()

    def _initialize_step_runs(self):
        """Create a run for each step
        """
        for step in self.workflow.steps.all():
            step_run = self.create_run_from_workflow(step)
            self.step_runs.add(step_run)

    def _initialize_channels(self):
        """Create the Channel objects connecting workflow input/outputs to step input/outputs
        """
        from .channels import Channel
        for source in self._get_sources():
            destinations = self._get_matching_destinations(source.channel)
            channel = Channel.create_from_sender(source, source.channel)
            channel.add_receivers(destinations)

    def _get_sources(self):
        sources = [source for source in self.inputs.all()]
        for step_run in self.step_runs.all():
            sources.extend([source for source in step_run.downcast().outputs.all()])
        return sources

    def _get_matching_destinations(self, channel):
        destinations = [dest for dest in self.outputs.filter(channel=channel)]
        for step_run in self.step_runs.all():
            destinations.extend([dest for dest in step_run.downcast().inputs.filter(channel=channel)])
        return destinations


class StepRun(AbstractWorkflowRun):

    NAME_FIELD = 'step__name'

    inputs = fields.OneToManyField('StepRunInput', related_name='step_run')
    outputs = fields.OneToManyField('StepRunOutput', related_name='step_run')
    step = fields.ForeignKey('Step', related_name='step_run')
    task_runs = fields.OneToManyField('TaskRun', related_name='step_run')
    #status = fields.CharField(
    #    max_length=255,
    #    default='waiting',
    #    choices=(('waiting', 'Waiting'),
    #             ('running', 'Running'),
    #             ('completed', 'Completed'),
    #             ('canceled', 'Canceled'),
    #             ('error', 'Error'),
    #    )
    #)

    def is_step(self):
        return True
    
    def push(self):
        if self._is_ready_for_task_run():
            task_run = TaskRun.create_from_step_run(self)
            task_run.mock_run()

    def _is_ready_for_task_run(self):
        for input in self.inputs.all():
            if not input.is_ready():
                return False
        return True


class InputOutput(AnalysisAppInstanceModel):

    def push(self, *args, **kwargs):
        return self.downcast().push(*args, **kwargs)


class TypedInputOutput(InputOutput):

    channel = fields.CharField(max_length=255)
    type = fields.CharField(
        max_length=255,
        choices=(
            ('file', 'File'),
            ('boolean', 'Boolean'),
            ('string', 'String'),
            ('integer', 'Integer'),
            ('json', 'JSON'),
        )
    )

    class Meta:
        abstract = True


class StepRunInput(TypedInputOutput):

    task_run_inputs = fields.OneToManyField('TaskRunInput', related_name='step_run_input')

    def push(self):
        self.step_run.push()

    def is_ready(self):
        return not self.from_channel.is_empty()

    def pop(self):
        return self.from_channel.pop()


class WorkflowRunInput(TypedInputOutput):

    def push(self):
        data_object = self.from_channel.pop()
        self.to_channel.push(data_object)


class StepRunOutput(TypedInputOutput):
    
    task_run_outputs = fields.OneToManyField('TaskRunOutput', related_name='step_run_output')
    
    def push(self, data_object):
        self.to_channel.push(data_object)

    def get_filename(self):
        return self.step_run.step.get_output(self.channel).filename

class WorkflowRunOutput(TypedInputOutput):

    def push(self):
        data_object = self.from_channel.pop()
        self.to_channel.push(data_object)
