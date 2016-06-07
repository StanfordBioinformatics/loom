from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from analysis.exceptions import *
from .base import AnalysisAppInstanceModel, AnalysisAppImmutableModel
from .channels import Channel, InputOutputNode, ChannelSet
from .data_objects import DataObject
from .task_definitions import TaskDefinition
from .task_runs import TaskRun, TaskRunInput, TaskRunOutput, TaskRunBuilder
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
                'fixed_inputs': [{'channel': input.channel, 'type': input.type} for input in workflow.fixed_inputs.all()],
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
    fixed_inputs = fields.OneToManyField('WorkflowRunInput', related_name='workflow_run_as_fixed_input')
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

        # Runtime inputs will be pushed when data is added,
        # but fixed inputs have to be pushed now on creation
        for input in self.fixed_inputs.all():
            input.initial_push()

    def _initialize_step_runs(self):
        """Create a run for each step
        """
        for step in self.workflow.steps.all():
            step_run = self.create_run_from_workflow(step)
            self.step_runs.add(step_run)

    def _initialize_channels(self):
        """Create the Channel objects connecting workflow input/outputs to step input/outputs
        """
        for source in self._get_sources():
            destinations = self._get_matching_destinations(source.channel)
            channel = Channel.create_from_sender(source, source.channel)
            channel.add_receivers(destinations)

    def _get_sources(self):
        sources = [source for source in self.inputs.all()]
        sources.extend([source for source in self.fixed_inputs.all()])
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
    fixed_inputs = fields.OneToManyField('FixedStepRunInput', related_name='step_run')
    outputs = fields.OneToManyField('StepRunOutput', related_name='step_run')
    step = fields.ForeignKey('Step', related_name='step_run')
    task_runs = fields.ManyToManyField('TaskRun', related_name='step_runs')
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

    def after_create_or_update(self):
        self._initialize_channels()

        # Runtime inputs will be pushed when data is added,
        # but fixed inputs have to be pushed now on creation
        for input in self.fixed_inputs.all():
            input.initial_push()

    def _initialize_channels(self):
        """The only Channels created here are to handle data from StepRun fixed inputs.
        These are unusual, because the FixedInput is both source and destination
        for the channel. Normally channels transmit data between objects, but here
        they just act as a gatekeeper to know when the data has been consumed and
        to integrate the data with other inputs for the step.
        """
        for input in self.fixed_inputs.all():
            channel = Channel.create_from_sender(input, input.channel)
            channel.add_receiver(input)

    def is_step(self):
        return True

    def get_all_inputs(self):
        inputs = [i for i in self.inputs.all()]
        inputs.extend([i for i in self.fixed_inputs.all()])
        return inputs

    def push(self):
        for input_set in ChannelSet(self.get_all_inputs()).get_ready_input_sets():
            task_run = TaskRunBuilder.create_from_step_run(self, input_set)
            task_run.mock_run()


class TypedInputOutputNode(InputOutputNode):

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


class AbstractStepRunInput(TypedInputOutputNode):

    def push(self):
        self.step_run.push()

    class Meta:
        abstract=True


class StepRunInput(AbstractStepRunInput):

    task_run_inputs = fields.ManyToManyField('TaskRunInput', related_name='step_run_inputs')


class FixedStepRunInput(AbstractStepRunInput):

    task_run_inputs = fields.ManyToManyField('TaskRunInput', related_name='fixed_step_run_inputs')
        
    def initial_push(self):
        data_object = self._get_data_object()
        self.to_channel.push(data_object)
        self.to_channel.close()

    def _get_data_object(self):
        fixed_step_input = self.step_run.step.get_fixed_input(self.channel)
        return DataObject.get_by_value(fixed_step_input.value, self.type)


class StepRunOutput(TypedInputOutputNode):
    
    task_run_outputs = fields.ManyToManyField('TaskRunOutput', related_name='step_run_outputs')
    
    def push(self, data_object):
        self.to_channel.push(data_object)

    def get_filename(self):
        return self.step_run.step.get_output(self.channel).filename


class WorkflowRunInput(TypedInputOutputNode):

    def push(self):
        self.from_channel.forward(self.to_channel)

    def initial_push(self):
        data_object = self._get_data_object()
        self.to_channel.push(data_object)

    def _get_data_object(self):
        fixed_workflow_input = self.workflow_run_as_fixed_input.workflow.get_fixed_input(self.channel)
        return DataObject.get_by_value(fixed_workflow_input.value, self.type)


class WorkflowRunOutput(TypedInputOutputNode):

    def push(self):
        self.from_channel.forward(self.to_channel)
