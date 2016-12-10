from django.db import models
from django.dispatch import receiver
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
import uuid

from .base import BaseModel
from api import get_setting
from api.models.input_output_nodes import InputOutputNode, InputNodeSet
from api.models.data_objects import DataObject
from api.models.tasks import Task, TaskInput, TaskOutput, TaskAttemptError


"""
This module defines WorkflowRun and other classes related to
running an analysis
"""

class WorkflowRunManager(object):

    def __init__(self, run):
        assert run.type == 'workflow'
        self.run = run

    def get_inputs(self):
        return self.run.workflowrun.inputs

    def get_outputs(self):
        return self.run.workflowrun.outputs

    def connect_channels(self):
        return self.run.workflowrun.connect_channels()

    def create_ready_tasks(self, do_start):
        return self.run.workflowrun.create_ready_tasks(do_start=do_start)

    def get_tasks(self):
        raise Exception('No tasks on run of type "workflow"')


class StepRunManager(object):

    def __init__(self, run):
        assert run.type == 'step'
        self.run = run

    def get_inputs(self):
        return self.run.steprun.inputs

    def get_outputs(self):
        return self.run.steprun.outputs

    def connect_channels(self):
        return self.run.steprun.connect_channels()

    def create_ready_tasks(self, do_start):
        return self.run.steprun.create_ready_tasks(do_start=do_start)

    def get_tasks(self):
        return self.run.steprun.tasks


class Run(BaseModel):
    """AbstractWorkflowRun represents the process of executing a Workflow on 
    a particular set of inputs. The workflow may be either a Step or a 
    Workflow composed of one or more Steps.
    """

    _MANAGER_CLASSES = {
        'step': StepRunManager,
        'workflow': WorkflowRunManager
    }
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=255,
                            choices = (('step', 'Step'),
                                       ('workflow', 'Workflow')))
    datetime_created = models.DateTimeField(default=timezone.now,
                                            editable=False)
    datetime_finished = models.DateTimeField(null=True)
    parent = models.ForeignKey('WorkflowRun',
                               related_name='steps',
                               null=True,
                               on_delete=models.CASCADE)
    status = models.CharField(
        max_length=255,
        default='',
    )
    template = models.ForeignKey('Template',
                                 related_name='runs',
                                 on_delete=models.PROTECT,
                                 null=True) # For testing only
    saving_status = models.CharField(
        max_length=255,
        default='saving',
        choices=(('saving', 'Saving'),
                 ('ready', 'Ready'),
                 ('error', 'Error'))
    )

    @classmethod
    def _get_manager_class(cls, type):
        return cls._MANAGER_CLASSES[type]

    def _get_manager(self):
        return self._get_manager_class(self.type)(self)

    @property
    def inputs(self):
        return self._get_manager().get_inputs()
    
    @property
    def outputs(self):
        return self._get_manager().get_outputs()

    @property
    def tasks(self):
        return self._get_manager().get_tasks()

    def connect_channels(self):
        return self._get_manager().connect_channels()

    def create_ready_tasks(self, do_start=True):
        return self._get_manager().create_ready_tasks(do_start=do_start)
    
    def get_input(self, channel):
        inputs = [i for i in self.inputs.filter(channel=channel)]
        assert len(inputs) == 1
        return inputs[0]

    def get_output(self, channel):
        outputs = [o for o in self.outputs.filter(channel=channel)]
        assert len(outputs) == 1
        return outputs[0]

#    def update_parent_status(self):
#        if self.parent:
#            self.parent.update_status()

    def get_run_request(self):
        try:
            return self.run_request
        except ObjectDoesNotExist:
            pass
        return self.parent.get_run_request()


class WorkflowRun(Run):

    def add_step(self, step_run):
        step_run.parent = self
        step_run.save()

    def get_step_status_count(self):
        count = {
            'waiting': 0,
            'running': 0,
            'error': 0,
            'success': 0,
        }
        for step in self.steps.all():
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
#        self.status = ' '.join(status_list)
        self.save()
#        self.update_parent_status()

    def create_ready_tasks(self, do_start=True):
        for step_run in self.steps.all():
            step_run.create_ready_tasks(do_start=do_start)


class StepRun(Run):

    NAME_FIELD = 'template__name'

    command = models.TextField()
    interpreter = models.CharField(max_length=255)

    @property
    def errors(self):
        if self.tasks.count() == 0:
            return TaskAttemptError.objects.none()
        return self.tasks.first().errors

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
        pass
#        if self.tasks.count() == 0:
#            missing_inputs = InputNodeSet(
#                self.get_all_inputs()).get_missing_inputs()
#            if len(missing_inputs) == 1:
#                status = 'Waiting for input "%s"' % missing_inputs[0].channel
#            else:
#                status = 'Waiting for inputs %s' % ', '.join(
#                    [input.channel for input in missing_inputs])
#        else:
#            status = self.tasks.first().status

#        if status != self.status:
#            self.status = status
#            self.save()
        #self.update_parent_status()


class AbstractStepRunInput(InputOutputNode):

    def is_ready(self):
        if self.get_data_as_scalar() is None:
            return False
        return self.get_data_as_scalar().is_ready()

    class Meta:
        abstract=True

class StepRunInput(AbstractStepRunInput):

    step_run = models.ForeignKey('StepRun',
                                 related_name='inputs',
                                 on_delete=models.CASCADE)
    mode = models.CharField(max_length=255)
    group = models.IntegerField()


class StepRunOutput(InputOutputNode):

    step_run = models.ForeignKey('StepRun',
                                 related_name='outputs',
                                 on_delete=models.CASCADE,
                                 null=True) # for testing only
    mode = models.CharField(max_length=255)

#    @property
#    def parser(self):
#        if self.step_output is None:
#            return ''
#        return self.step_output.parser


class WorkflowRunInput(InputOutputNode):

    workflow_run = models.ForeignKey('WorkflowRun',
                                     related_name='inputs',
                                     on_delete=models.CASCADE)


class WorkflowRunOutput(InputOutputNode):

    workflow_run = models.ForeignKey('WorkflowRun',
                                     related_name='outputs',
                                     on_delete=models.CASCADE)


class StepRunOutputSource(BaseModel):

    output = models.OneToOneField(
        StepRunOutput,
	related_name='source',
        on_delete=models.CASCADE)

    filename = models.CharField(max_length=1024, null=True)
    stream = models.CharField(max_length=255, null=True)
