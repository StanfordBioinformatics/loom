from django.db import models
from django.dispatch import receiver
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
import uuid

from .base import BaseModel, BasePolymorphicModel
from api import get_setting
from api.models.input_output_nodes import InputOutputNode, InputNodeSet
from api.models.data_objects import DataObject
from api.models.tasks import Task, TaskInput, TaskOutput, TaskAttemptError
from api.models.templates import Workflow, Step, \
    WorkflowInput, WorkflowOutput, StepInput, StepOutput


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
    status = models.CharField(
        max_length=255,
        default='',
    )
    
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
        return run

    def update_parent_status(self):
        if self.parent:
            self.parent.update_status()

    def get_run_request(self):
        try:
            return self.run_request
        except ObjectDoesNotExist:
            pass
        return self.parent.get_run_request()
        

class WorkflowRun(AbstractWorkflowRun):

    NAME_FIELD = 'workflow__name'

    template = models.ForeignKey('Template',
                                 related_name='runs',
                                 on_delete=models.PROTECT)

    def is_step(self):
        return False

    def initialize(self):
        self._initialize_step_runs()
        self._initialize_inputs_outputs()

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
            child_run.initialize()

    def _initialize_inputs_outputs(self):
        self._initialize_inputs()
        self._initialize_fixed_inputs()
        self._initialize_outputs()

    def _initialize_inputs(self):
        for input in self.template.inputs.all():
            WorkflowRunInput.objects.create(
                workflow_run=self,
                channel = input.channel,
                workflow_input=input)

    def _initialize_fixed_inputs(self):
        for fixed_input in self.template.fixed_inputs.all():
            fixed_workflow_run_input = FixedWorkflowRunInput.objects.create(
                workflow_run=self,
                channel=fixed_input.channel,
                workflow_input=fixed_input)
            fixed_workflow_run_input._add_scalar_data_from_template()

    def _initialize_outputs(self):
        for output in self.template.outputs.all():
            WorkflowRunOutput.objects.create(
                workflow_run=self,
                channel=output.channel,
                workflow_output=output)

    def connect_channels(self):
        for destination in self._get_destinations():
            source = self._get_source(destination.channel)
            # Make sure matching source and destination nodes are connected
            source.connect(destination)

        for step in self.step_runs.all():
            step.connect_channels()

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

    def get_step_status_count(self):
        count = {
            'waiting': 0,
            'running': 0,
            'error': 0,
            'success': 0,
        }
        for step in self.step_runs.all():
            step_counts = step.get_step_status_count()
            count['waiting'] += step_counts['waiting']
            count['running'] += step_counts['running']
            count['error'] += step_counts['error']
            count['success'] += step_counts['success']
        return count

    def update_status(self):
        status_list = []
        count = self.get_step_status_count()
        if count['waiting']:
            pluralize = 's' if count['waiting'] > 1 else ''
            status_list.append('%s step%s waiting.' % (count['waiting'], pluralize))
        if count['running']:
            pluralize = 's' if count['running'] > 1 else ''
            status_list.append('%s step%s running.' % (count['running'], pluralize))
        if count['error']:
            pluralize = 's' if count['error'] > 1 else ''
            status_list.append('%s step%s with errors.' % (count['error'], pluralize))
        if count['success']:
            pluralize = 's' if count['success'] > 1 else ''
            status_list.append('%s step%s finished successfully.' % (count['success'], pluralize))
        self.status = ' '.join(status_list)
        self.save()
        self.update_parent_status()

    def create_ready_tasks(self, do_start):
        for step_run in self.step_runs.all():
            step_run.create_ready_tasks(do_start)


class StepRun(AbstractWorkflowRun):

    NAME_FIELD = 'step__name'

    template = models.ForeignKey('StepTemplate',
                                 related_name='step_runs',
                                 on_delete=models.PROTECT)
    @property
    def command(self):
        return self.template.command

    @property
    def interpreter(self):
        return self.template.interpreter

    @property
    def environment(self):
        return self.template.environment

    @property
    def resources(self):
        return self.template.resources

    @property
    def errors(self):
        if self.tasks.count() == 0:
            return TaskAttemptError.objects.none()
        return self.tasks.first().errors

    def is_step(self):
        return True

    def get_step_status_count(self):
        count = {
            'waiting': 0,
            'running': 0,
            'error': 0,
            'success': 0,
        }
        if self.errors.count() > 0:
            count['error'] = 1
        elif self.status.startswith('Waiting'):
            count['waiting'] = 1
        elif self.status.startswith('Finished'):
            count['success'] = 1
        else:
            count['running'] = 1
        return count

    def initialize(self):
        self._initialize_inputs_outputs()

    def _initialize_inputs_outputs(self):
        self._initialize_inputs()
        self._initialize_fixed_inputs()
        self._initialize_outputs()

    def _initialize_inputs(self):
        for input in self.template.inputs.all():
            StepRunInput.objects.create(
                step_run=self,
                channel = input.channel,
                step_input=input)

    def _initialize_fixed_inputs(self):
        for fixed_input in self.template.fixed_inputs.all():
            fixed_step_run_input = FixedStepRunInput.objects.create(
                step_run=self,
                channel=fixed_input.channel,
                step_input=fixed_input)
            fixed_step_run_input._add_scalar_data_from_template()

    def _initialize_outputs(self):
        for output in self.template.outputs.all():
            StepRunOutput.objects.create(
                step_run=self,
                channel=output.channel,
                step_output=output)

    def connect_channels(self):
        pass # no-op

    def get_all_inputs(self):
        inputs = [i for i in self.inputs.all()]
        inputs.extend([i for i in self.fixed_inputs.all()])
        return inputs

    def create_ready_tasks(self, do_start=True):
        # This is a temporary limit. It assumes no parallel workflows, and no
        # failure recovery, so each step has only one Task.
        if self.tasks.count() == 0:
            for input_set in InputNodeSet(
                    self.get_all_inputs()).get_ready_input_sets():
                task = Task.create_from_input_set(input_set, self)
                if do_start:
                    task.run()
            self.update_status()

    def update_status(self):
        if self.tasks.count() == 0:
            missing_inputs = InputNodeSet(
                self.get_all_inputs()).get_missing_inputs()
            if len(missing_inputs) == 1:
                status = 'Waiting for input "%s"' % missing_inputs[0].channel
            else:
                status = 'Waiting for inputs %s' % ', '.join(
                    [input.channel for input in missing_inputs])
        else:
            status = self.tasks.first().status

        if status != self.status:
            self.status = status
            self.save()
        self.update_parent_status()

    
class AbstractStepRunInput(InputOutputNode):
    # This table is needed because it is referenced by TaskInput,
    # and Tasks do not distinguish between fixed and runtime inputs
    pass

    def is_ready(self):
        if self.get_data_as_scalar() is None:
            return False
        return self.get_data_as_scalar().is_ready()


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

    @property
    def mode(self):
        return self.step_input.mode

    @property
    def group(self):
        return self.step_input.group

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

    @property
    def mode(self):
        return self.step_input.mode

    @property
    def group(self):
        return self.step_input.group

    def _add_scalar_data_from_template(self):
        path = [] # Add at root node since we are not handling parallel
        self.add_data_object(path, self.step_input.data_object)


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
    def mode(self):
        return self.step_output.mode

    @property
    def source(self):
        if self.step_output is None:
            return ''
        return self.step_output.source

#    @property
#    def parser(self):
#        if self.step_output is None:
#            return ''
#        return self.step_output.parser


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

    @property
    def type(self):
        return self.workflow_input.type

    def _add_scalar_data_from_template(self):
        path = [] # Add at root node since we are not handling parallel
        self.add_data_object(path, self.workflow_input.data_object)


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
