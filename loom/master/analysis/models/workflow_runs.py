from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

from analysis import get_setting
from analysis.exceptions import *
from analysis.models.base import AnalysisAppInstanceModel, AnalysisAppImmutableModel
from analysis.models.channels import Channel, InputOutputNode, ChannelSet
from analysis.models.data_objects import DataObject
from analysis.models.task_definitions import TaskDefinition
from analysis.models.task_runs import TaskRun, TaskRunInput, TaskRunOutput, TaskRunBuilder
from analysis.models.workflows import AbstractWorkflow, Workflow, Step, WorkflowInput, WorkflowOutput, StepInput, StepOutput
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
    def before_create_or_update(cls, data):
        """Cast as WorkflowRun or StepRun according to the type of template given
        """
        if data.get('template') is not None:
            template = AbstractWorkflow.create(data.get('template'))
            if template.is_step():
                data.update({'_class': 'StepRun'})
            else:
                data.update({'_class': 'WorkflowRun'})
    
    def is_step(self):
        return self.downcast().is_step()

    def get_input(self, channel):
        inputs = [i for i in self.downcast().inputs.filter(channel=channel)]
        inputs.extend([i for i in self.downcast().fixed_inputs.filter(channel=channel)])
        assert len(inputs) == 1
        return inputs[0]


class WorkflowRun(AbstractWorkflowRun):

    NAME_FIELD = 'workflow__name'

    step_runs = fields.OneToManyField('AbstractWorkflowRun', related_name='parent_run')
    inputs = fields.OneToManyField('WorkflowRunInput', related_name='workflow_run')
    fixed_inputs = fields.OneToManyField('FixedWorkflowRunInput', related_name='workflow_run')
    outputs = fields.OneToManyField('WorkflowRunOutput', related_name='workflow_run')
    template = fields.ForeignKey('Workflow')

    def is_step(self):
        return False

    def after_create_or_update(self, data):
        if not self._is_initialized():
            self._initialize_step_runs()
            self._initialize_inputs_outputs()
            self._initialize_channels()

    def _is_initialized(self):
        return self.step_runs.count() == self.template.steps.count() \
            and self.inputs.count() == self.template.inputs.count() \
            and self.fixed_inputs.count() == self.template.fixed_inputs.count() \
            and self.outputs.count() == self.template.outputs.count()

    def _initialize_step_runs(self):
        """Create a run for each step
        """
        # Workaround--not using the "update" method here to avoid infinite recursion
        for step in self.template.steps.all():
            self.step_runs.add(AbstractWorkflowRun.create({'template': step}))

    def _initialize_inputs_outputs(self):
        self.update({
            'inputs': [{'channel': input.channel, 'type': input.type} for input in self.template.inputs.all()],
            'fixed_inputs': [{'channel': input.channel, 'type': input.type} for input in self.template.fixed_inputs.all()],
            'outputs': [{'channel': output.channel, 'type': output.type} for output in self.template.outputs.all()]
        })

    def _initialize_channels(self):
        """Create the Channel objects connecting workflow input/outputs to step input/outputs
        """
        for source in self._get_all_sources():
            destinations = self._get_destinations(source.channel)
            channel = Channel.create_from_sender(source, source.channel)
            channel.add_receivers(destinations)

    def initial_push(self):
        # Runtime inputs will be pushed when data is added,
        # but fixed inputs have to be pushed now on creation
        for input in self.fixed_inputs.all():
            input.initial_push()
        for step_run in self.step_runs.all():
            step_run.downcast().initial_push()

    def _get_all_sources(self):
        sources = [source for source in self.inputs.all()]
        sources.extend([source for source in self.fixed_inputs.all()])
        for step_run in self.step_runs.all():
            sources.extend([source for source in step_run.downcast().outputs.all()])
        return sources

    def _get_destinations(self, channel):
        destinations = [dest for dest in self.outputs.filter(channel=channel)]
        for step_run in self.step_runs.all():
            destinations.extend([dest for dest in step_run.downcast().inputs.filter(channel=channel)])
        return destinations


class StepRun(AbstractWorkflowRun):

    NAME_FIELD = 'step__name'

    inputs = fields.OneToManyField('StepRunInput', related_name='step_run')
    fixed_inputs = fields.OneToManyField('FixedStepRunInput', related_name='step_run')
    outputs = fields.OneToManyField('StepRunOutput', related_name='step_run')
    template = fields.ForeignKey('Step', related_name='step_run')
    task_runs = fields.ManyToManyField('TaskRun', related_name='step_runs')

    def after_create_or_update(self, data):
        if not self._is_initialized():
            self._initialize_inputs_outputs()
            self._initialize_channels()

    def _is_initialized(self):
        return self.inputs.count() == self.template.inputs.count() \
            and self.fixed_inputs.count() == self.template.fixed_inputs.count() \
            and self.outputs.count() == self.template.outputs.count()

    def _initialize_inputs_outputs(self):
        self.update({
            'inputs': [{'channel': input.channel, 'type': input.type} for input in self.template.inputs.all()],
            'fixed_inputs': [{'channel': input.channel, 'type': input.type} for input in self.template.fixed_inputs.all()],
            'outputs': [{'channel': output.channel, 'type': output.type} for output in self.template.outputs.all()]
        })

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

    def initial_push(self):
        # Runtime inputs will be pushed when data is added,
        # but fixed inputs have to be pushed on creation
        for input in self.fixed_inputs.all():
            input.initial_push()

    def is_step(self):
        return True

    def get_all_inputs(self):
        inputs = [i for i in self.inputs.all()]
        inputs.extend([i for i in self.fixed_inputs.all()])
        return inputs

    def push(self):
        for input_set in ChannelSet(self.get_all_inputs()).get_ready_input_sets():
            task_run = TaskRunBuilder.create_from_step_run(self, input_set)
            task_run.run()


class TypedInputOutputNode(InputOutputNode):

    channel = fields.CharField(max_length=255)
    type = fields.CharField(
        max_length=255,
        choices=DataObject.TYPE_CHOICES
    )
    data_object = fields.ForeignKey('DataObject', null=True)

    class Meta:
        abstract = True


class AbstractStepRunInput(TypedInputOutputNode):

    task_run_inputs = fields.ManyToManyField('TaskRunInput', related_name='step_run_inputs')

    def push(self, data_object):
        if self.data_object is None:
            self.update({'data_object': data_object})
            if self.step_run:
                self.step_run.push()


class StepRunInput(AbstractStepRunInput):

    pass


class FixedStepRunInput(AbstractStepRunInput):

    def initial_push(self):
        data_object = self._get_data_object()
        self.to_channel.push(data_object)
        self.to_channel.close()

    def _get_data_object(self):
        fixed_step_input = self.step_run.template.get_fixed_input(self.channel)
        return DataObject.get_by_value(fixed_step_input.value, self.type)


class StepRunOutput(TypedInputOutputNode):

    task_run_outputs = fields.ManyToManyField('TaskRunOutput', related_name='step_run_outputs')

    def push(self, data_object):
        if self.data_object is None:
            self.update({'data_object': data_object})
            self.to_channel.push(data_object)
            self.to_channel.close()

    def get_filename(self):
        return self.step_run.template.get_output(self.channel).filename

    def get_type(self):
        return self.step_run.template.get_output(self.channel).type

class WorkflowRunInput(TypedInputOutputNode):

    def push(self, data_object):
        if self.data_object is None:
            self.update({'data_object': data_object})
            self.from_channel.forward(self.to_channel)

class FixedWorkflowRunInput(TypedInputOutputNode):

    def initial_push(self):
        self.update({'data_object': self._get_data_object()})
        self.to_channel.push(self.data_object)
        self.to_channel.close()

    def _get_data_object(self):
        fixed_workflow_input = self.workflow_run.template.get_fixed_input(self.channel)
        return DataObject.get_by_value(fixed_workflow_input.value, self.type)


class WorkflowRunOutput(TypedInputOutputNode):

    def push(self, data_object):
        if self.data_object is None:
            self.update({'data_object': data_object})
            self.from_channel.forward(self.to_channel)
