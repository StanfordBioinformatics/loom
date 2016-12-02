from django.db import models
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.utils import timezone
import uuid

from .base import BaseModel
from .data_objects import DataObject
from .input_output_nodes import InputOutputNode
from .signals import post_save_children
from api.exceptions import *
import jsonfield


"""
This module defines Templates. A Template is either 
a Step or a Workflow.
Steps have execution details such as command and runtime
environment, while Workflows are collections of other Steps
or Workflows.
"""

class WorkflowManager(object):

    def __init__(self, template):
        assert template.type == 'workflow'
        self.template = template

    def get_inputs(self):
        return self.template.workflow.inputs

    def get_fixed_inputs(self):
        return self.template.workflow.fixed_inputs

    def get_outputs(self):
        return self.template.workflow.outputs

    def get_resources(self):
        raise Exception('No resources on template of type "workflow"')

    def get_environment(self):
        raise Exception('No environment on template of type "workflow"')


class StepManager(object):

    def __init__(self, template):
        assert template.type == 'step'
        self.template = template

    def get_inputs(self):
        return self.template.step.inputs

    def get_fixed_inputs(self):
        return self.template.step.fixed_inputs

    def get_outputs(self):
        return self.template.step.outputs

    def get_resources(self):
        return self.template.step.resources

    def get_environment(self):
        return self.template.step.environment


class Template(BaseModel):

    _MANAGER_CLASSES = {
        'step': StepManager,
        'workflow': WorkflowManager
    }

    NAME_FIELD = 'name'

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    type = models.CharField(max_length=255,
                            choices=(('workflow', 'Workflow'),
                                     ('step', 'Step')))
    datetime_created = models.DateTimeField(default=timezone.now,
                                            editable=False)
    name = models.CharField(max_length=255)
    template_import = jsonfield.JSONField(null=True)

    @classmethod
    def _get_manager_class(cls, type):
        return cls._MANAGER_CLASSES[type]

    def _get_manager(self):
        return self._get_manager_class(self.type)(self)

    @property
    def inputs(self):
        return self._get_manager().get_inputs()

    @property
    def fixed_inputs(self):
        return self._get_manager().get_fixed_inputs()

    @property
    def outputs(self):
        return self._get_manager().get_outputs()

    @property
    def resources(self):
        return self._get_manager().get_resources()

    @property
    def environment(self):
        return self._get_manager().get_environment()

    def get_name_and_id(self):
        return "%s@%s" % (self.name, self.id)

    def get_fixed_input(self, channel):
        inputs = self.fixed_inputs.filter(channel=channel)
        assert inputs.count() == 1
        return inputs.first()

    def get_input(self, channel):
        inputs = [i for i in self.inputs.filter(channel=channel)]
        inputs.extend([i for i in self.fixed_inputs.filter(
            channel=channel)])
        assert len(inputs) == 1
        return inputs[0]

    def get_output(self, channel):
        outputs = self.outputs.filter(channel=channel)
        assert outputs.count() == 1
        return outputs.first()


class Workflow(Template):

    steps = models.ManyToManyField(
        'Template',
        through='WorkflowMembership',
        through_fields=('parent_template', 'child_template'),
        related_name='workflows')
    outputs = jsonfield.JSONField(null=True)
    inputs = jsonfield.JSONField(null=True)
    raw_data = jsonfield.JSONField(null=True)

    def add_step(self, step):
        WorkflowMembership.add_step_to_workflow(step, self)

    def add_steps(self, step_list):
        for step in step_list:
            self.add_step(step)


class FixedWorkflowInput(InputOutputNode):

    workflow = models.ForeignKey(
        'Workflow',
        related_name='fixed_inputs',
        on_delete=models.CASCADE)


class Step(Template):

    """Steps are smaller units of processing within a Workflow. A Step can 
    give rise to a single process, or it may iterate over an array to produce 
    many parallel processing tasks.
    """

    command = models.TextField()
    interpreter = models.CharField(max_length=255, default='/bin/bash')
    environment = jsonfield.JSONField(null=True)
    outputs = jsonfield.JSONField(null=True)
    inputs = jsonfield.JSONField(null=True)
    resources = jsonfield.JSONField(null=True)
    raw_data = jsonfield.JSONField(null=True)


class FixedStepInput(InputOutputNode):

    step = models.ForeignKey(
        'Step',
        related_name='fixed_inputs',
        on_delete=models.CASCADE)
    mode = models.CharField(max_length=255, default='no_gather')
    group = models.IntegerField(default=0)

    class Meta:
        app_label = 'api'

    @property
    def data(self):
        # Dummy attribute required by serializer
        return


class WorkflowMembership(models.Model):

    parent_template = models.ForeignKey('Workflow', related_name='children')
    child_template = models.ForeignKey('Template', related_name='parents', 
                                       null=True)

    @classmethod
    def add_step_to_workflow(cls, step, parent):
            WorkflowMembership.objects.create(
                parent_template=parent,
                child_template=step)

    class Meta:
        app_label = 'api'
