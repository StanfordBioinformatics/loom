from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
import uuid

from analysis import get_setting
from analysis.exceptions import *
from analysis.models.channels import InputOutputNode, InputNodeSet
from analysis.models.data_objects import DataObject
from analysis.models.task_definitions import TaskDefinition
from analysis.models.task_runs import TaskRun, TaskRunInput, TaskRunOutput
from analysis.models.workflows import AbstractWorkflow, Workflow, Step, \
    WorkflowInput, WorkflowOutput, StepInput, StepOutput
from .base import BaseModel, BasePolymorphicModel


"""
This module defines WorkflowRun and other classes related to
running an analysis
"""

class AbstractWorkflowRun(BasePolymorphicModel):
    """AbstractWorkflowRun represents the process of executing a Workflow on 
    a particular set of inputs. The workflow may be either a Step or a 
    Workflow composed of one or more Steps.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    parent = models.ForeignKey('WorkflowRun',
                               related_name='step_runs',
                               null=True,
                               on_delete=models.CASCADE)
    @property
    def name(self):
        return self.template.name

    def get_input(self, channel):
        inputs = [i for i in self.inputs.filter(channel=channel)]
        inputs.extend([i for i in self.fixed_inputs.filter(
            channel=channel)])
        assert len(inputs) == 1
        return inputs[0]

    def get_output(self, channel):
        outputs = [o for o in self.outputs.filter(channel=channel)]
        assert len(outputs) == 1
        return outputs[0]

    @classmethod
    def create_from_template(cls, template):
        if template.is_step():
            run = StepRun.objects.create(template=template)
        else:
            run = WorkflowRun.objects.create(template=template)
        run.post_create()
        return run


class WorkflowRun(AbstractWorkflowRun):

    NAME_FIELD = 'workflow__name'

    template = models.ForeignKey('Workflow',
                                 related_name='runs',
                                 on_delete=models.PROTECT)

    def is_step(self):
        return False

    def post_create(self):
        self._initialize()
        self.initial_push()

    def _initialize(self):
        self._initialize_step_runs()
        self._initialize_inputs_outputs()
        self._initialize_channels()

    def _initialize_step_runs(self):
        """Create a run for each step
        """
        for step in self.template.steps.all():
            if step.is_step():
                ChildRunClass = StepRun
            else:
                ChildRunClass = WorkflowRun
            child_run = ChildRunClass.objects.create(template=step,
                                                     parent=self)
            child_run._initialize()

    def _initialize_inputs_outputs(self):
        # TODO - check to see if the input already exists
        for input in self.template.inputs.all():
            WorkflowRunInput.objects.create(
                workflow_run=self,
                channel = input.channel,
                workflow_input=input)
        for fixed_input in self.template.fixed_inputs.all():
            fixed_workflow_run_input = FixedWorkflowRunInput.objects.create(
                workflow_run=self,
                channel=fixed_input.channel,
                workflow_input=fixed_input)
        for output in self.template.outputs.all():
            WorkflowRunOutput.objects.create(
                workflow_run=self,
                channel=output.channel,
                workflow_output=output)

    def _initialize_channels(self):
        for destination in self._get_destinations():
            source = self._get_source(destination.channel)

            # For a matching source and desination, make sure they are
            # sender/receiver on the same channel 
            if not destination.sender:
                destination.sender = source
                destination.save()
            else:
                assert destination.sender == source
                
    def _get_destinations(self):
        destinations = [dest for dest in self.outputs.all()]
        for step_run in self.step_runs.all():
            destinations.extend([dest for dest in step_run.inputs.all()])
        return destinations

    def _get_source(self, channel):
        sources = [source for source in self.inputs.filter(channel=channel)]
        sources.extend([source for source in
                        self.fixed_inputs.filter(channel=channel)])
        for step_run in self.step_runs.all():
            sources.extend([source for source in
                            step_run.outputs.filter(channel=channel)])
        if len(sources) < 1:
            raise Exception('Could not find data source for channel "%s"' % channel)
        elif len(sources) > 1:
            raise Exception('Found multiple data sources for channel "%s"' % channel)
        return sources[0]

    def initial_push(self):
        # Runtime inputs will be pushed when data is added,
        # but fixed inputs have to be pushed now on creation
        for input in self.fixed_inputs.all():
            input.initial_push()
        # StepRun will normally be pushed as individual DataObjects arrive,
        # but we do the initial_push in case all inputs are fixed
        for step_run in self.step_runs.all():
            step_run.initial_push()


class StepRun(AbstractWorkflowRun):

    NAME_FIELD = 'step__name'

    template = models.ForeignKey('Step',
                                 related_name='step_runs',
                                 on_delete=models.PROTECT)

    @property
    def command(self):
        return self.template.command

    @property
    def environment(self):
        return self.template.environment

    @property
    def resources(self):
        return self.template.resources

    def is_step(self):
        return True

    def post_create(self):
        self._initialize()

    def _initialize(self):
        self._initialize_inputs_outputs()

    def _is_initialized(self):
        return self.inputs.count() == self.template.inputs.count() \
            and self.fixed_inputs.count() \
            == self.template.fixed_inputs.count() \
            and self.outputs.count() == self.template.outputs.count()

    def _initialize_inputs_outputs(self):
        for input in self.template.inputs.all():
            StepRunInput.objects.create(
                step_run=self,
                channel = input.channel,
                step_input=input)
        for fixed_input in self.template.fixed_inputs.all():
            FixedStepRunInput.objects.create(
                step_run=self,
                channel=fixed_input.channel,
                step_input=fixed_input)
        for output in self.template.outputs.all():
            StepRunOutput.objects.create(
                step_run=self,
                channel=output.channel,
                step_output=output)

    def _initialize_channels(self):
        for destination in self._get_destinations():
            source = self._get_source(destination.channel)

            # For a matching source and desination, make sure they are
            # sender/receiver on the same channel 
            if not destination.sender:
                destination.sender = source
                destination.save()
            else:
                assert destination.sender == source

    def get_all_inputs(self):
        inputs = [i for i in self.inputs.all()]
        inputs.extend([i for i in self.fixed_inputs.all()])
        return inputs

    def initial_push(self):
        # Runtime inputs will be pushed when data is added,
        # but fixed inputs have to be pushed now on creation
        for input in self.fixed_inputs.all():
            input.initial_push()
        self.push()
        
    def push(self):
        if self.task_runs.count() == 0:
            for input_set in InputNodeSet(
                    self.get_all_inputs()).get_ready_input_sets():
                task_run = TaskRun.create_from_input_set(input_set, self)
                task_run.run()


class AbstractStepRunInput(InputOutputNode):

    # This table is needed because it is referenced by TaskRunInput,
    # and TaskRuns do not distinguish between fixed and runtime inputs

    def push(self, indexed_data_object):
        # Save arriving data as on any InputOutputNode
        super(AbstractStepRunInput, self).push(indexed_data_object)
        # Also make the step_run check to see if it is ready to kick
        # off a new TaskRun
        self.step_run.push()

    def push_to_receivers(self, indexed_data_object):
        # No receivers, but we need to push to the step_run
        self.step_run.push()


class StepRunInput(AbstractStepRunInput):

    step_run = models.ForeignKey('StepRun',
                                 related_name='inputs',
                                 on_delete=models.CASCADE)
    step_input = models.ForeignKey('StepInput',
                                   related_name='step_run_inputs',
                                   on_delete=models.PROTECT)

    @property
    def type(self):
        return self.step_input.type


class FixedStepRunInput(AbstractStepRunInput):

    step_run = models.ForeignKey('StepRun',
                                 related_name='fixed_inputs',
                                 on_delete=models.CASCADE)
    step_input = models.ForeignKey('FixedStepInput',
                                   related_name='step_run_inputs',
                                   on_delete=models.PROTECT)
    
    @property
    def type(self):
        return self.step_input.type

    def initial_push(self):
        self.push_without_index(self.step_input.data_object)


class StepRunOutput(InputOutputNode):

    step_run = models.ForeignKey('StepRun',
                                 related_name='outputs',
                                 on_delete=models.CASCADE)
    step_output = models.ForeignKey('StepOutput',
                                    related_name='step_run_outputs',
                                    on_delete=models.PROTECT)

    @property
    def type(self):
        return self.step_output.type

    @property
    def filename(self):
        if self.step_output is None:
            return ''
        return self.step_output.filename


class WorkflowRunInput(InputOutputNode):

    workflow_run = models.ForeignKey('WorkflowRun',
                                     related_name='inputs',
                                     on_delete=models.CASCADE)
    workflow_input = models.ForeignKey('WorkflowInput',
                                   related_name='workflow_run_inputs',
                                   on_delete=models.PROTECT)

    @property
    def type(self):
        return self.workflow_input.type

class FixedWorkflowRunInput(InputOutputNode):

    workflow_run = models.ForeignKey('WorkflowRun',
                                     related_name='fixed_inputs',
                                     on_delete=models.CASCADE)
    workflow_input = models.ForeignKey('FixedWorkflowInput',
                                   related_name='workflow_run_inputs',
                                   on_delete=models.PROTECT)

    def initial_push(self):
        self.push_without_index(self.workflow_input.data_object)

    @property
    def type(self):
        return self.workflow_input.type


class WorkflowRunOutput(InputOutputNode):

    workflow_run = models.ForeignKey('WorkflowRun',
                                     related_name='outputs',
                                     on_delete=models.CASCADE)
    workflow_output = models.ForeignKey('WorkflowOutput',
                                   related_name='workflow_run_outputs',
                                   on_delete=models.PROTECT)
    @property
    def type(self):
        return self.workflow_output.type
