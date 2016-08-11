from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

from analysis import get_setting
from analysis.exceptions import *

from analysis.models.channels import TypedInputOutputNode, InputNodeSet
from analysis.models.data_objects import DataObject
from analysis.models.task_definitions import TaskDefinition
from analysis.models.task_runs import TaskRun, TaskRunInput, TaskRunOutput, \
    TaskRunBuilder
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

    parent = models.ForeignKey('WorkflowRun',
                               related_name='step_runs',
                               null=True,
                               on_delete=models.CASCADE)

    def get_input(self, channel):
        inputs = [i for i in self.inputs.filter(channel=channel)]
        inputs.extend([i for i in self.fixed_inputs.filter(
            channel=channel)])
        assert len(inputs) == 1
        return inputs[0]


class WorkflowRun(AbstractWorkflowRun):

    NAME_FIELD = 'workflow__name'

    template = models.ForeignKey('Workflow',
                                 related_name='runs',
                                 on_delete=models.PROTECT)

    def is_step(self):
        return False

    def post_create(self):
        self._initialize()

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
        for input in self.template.inputs.all():
            WorkflowRunInput.objects.create(
                workflow_run=self,
                channel = input.channel,
                type = input.type)
        for fixed_input in self.template.fixed_inputs.all():
            FixedWorkflowRunInput.objects.create(
                workflow_run=self,
                channel=fixed_input.channel,
                type=fixed_input.type)
        for output in self.template.outputs.all():
            WorkflowRunOutput.objects.create(
                workflow_run=self,
                channel=output.channel,
                type=output.type)

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
        assert len(sources) == 1
        return sources[0]

    def initial_push(self):
        # Runtime inputs will be pushed when data is added,
        # but fixed inputs have to be pushed now on creation
        for input in self.fixed_inputs.all():
            input.push_all()
        # StepRun will normally be pushed as individual DataObjects arrive,
        # but we push_all once just in case all inputs are fixed.
        for step_run in self.step_runs.all():
            step_run.initial_push()


class StepRun(AbstractWorkflowRun):

    NAME_FIELD = 'step__name'

    template = models.ForeignKey('Step',
                                 related_name='step_runs',
                                 on_delete=models.PROTECT)

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
                type = input.type)
        for fixed_input in self.template.fixed_inputs.all():
            FixedStepRunInput.objects.create(
                step_run=self,
                channel=fixed_input.channel,
                type=fixed_input.type)
        for output in self.template.outputs.all():
            StepRunOutput.objects.create(
                step_run=self,
                channel=output.channel,
                type=output.type)

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
        # TODO
        # This is for running with all possible inputs.
        # We may also want to check for just one specific index.
        pass

#    def push(self, indexed_data_object):
#        pass
        # TODO - make this specific for a single index
#        for input_set in InputNodeSet(
#                self.get_all_inputs()).get_ready_input_sets():
#            task_run = TaskRunBuilder.create_from_step_run(self, input_set)
#            task_run.run()


class AbstractStepRunInput(TypedInputOutputNode):

    # This table is needed because it is referenced by TaskRunInput,
    # and TaskRuns do not distinguish between fixed and runtime inputs

#    def push(self, indexed_data_object):
#        pass
        #self.step_run.push()
        # TODO
    pass

class StepRunInput(AbstractStepRunInput):

    step_run = models.ForeignKey('StepRun',
                                 related_name='inputs',
                                 on_delete=models.CASCADE)


class FixedStepRunInput(AbstractStepRunInput):

    step_run = models.ForeignKey('StepRun',
                                 related_name='fixed_inputs',
                                 on_delete=models.CASCADE)


class StepRunOutput(TypedInputOutputNode):

    task_run_outputs = models.ManyToManyField('TaskRunOutput',
                                              related_name='step_run_outputs')
    step_run = models.ForeignKey('StepRun',
                                 related_name='outputs',
                                 on_delete=models.CASCADE)

    def get_filename(self):
        return self.step_run.template.get_output(self.channel).filename

    def get_type(self):
        return self.step_run.template.get_output(self.channel).type


class WorkflowRunInput(TypedInputOutputNode):

    workflow_run = models.ForeignKey('WorkflowRun',
                                     related_name='inputs',
                                     on_delete=models.CASCADE)


class FixedWorkflowRunInput(TypedInputOutputNode):

    workflow_run = models.ForeignKey('WorkflowRun',
                                     related_name='fixed_inputs',
                                     on_delete=models.CASCADE)


class WorkflowRunOutput(TypedInputOutputNode):

    workflow_run = models.ForeignKey('WorkflowRun',
                                     related_name='outputs',
                                     on_delete=models.CASCADE)
