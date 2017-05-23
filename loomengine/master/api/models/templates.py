from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import ValidationError
from django.db import models
from django.dispatch import receiver
from django.utils import timezone
import jsonfield

from .base import BaseModel
from .data_objects import DataObject
from .input_output_nodes import InputOutputNode
from api.exceptions import NoTemplateInputMatchError
from api.models import uuidstr
from api.models import validators

"""
This module defines Templates. A Template is either 
a Step or a Workflow.
Steps have execution details such as command and runtime
environment, while Workflows are collections of other Steps
or Workflows.
"""

class WorkflowManager(object):

    def __init__(self, template):
        assert template.type == 'workflow', 'expected template type "workflow"'
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

    def get_bound_channel(self, step_name, channel_name):
        return self.template.workflow.get_bound_channel(step_name, channel_name)
        

class StepManager(object):

    def __init__(self, template):
        assert template.type == 'step', 'Expected template type "step"'
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

    def get_bound_channel(self, step_name, channel_name):
        raise Exception('No method get_bound_channel on template of type "step"')


class Template(BaseModel):

    _MANAGER_CLASSES = {
        'step': StepManager,
        'workflow': WorkflowManager
    }

    NAME_FIELD = 'name'

    uuid = models.CharField(default=uuidstr, editable=False,
                            unique=True, max_length=255)
    type = models.CharField(max_length=255,
                            choices=(('workflow', 'Workflow'),
                                     ('step', 'Step')))
    datetime_created = models.DateTimeField(default=timezone.now,
                                            editable=False)
    name = models.CharField(max_length=255)
    postprocessing_status = models.CharField(
        max_length=255,
        default='incomplete',
        choices=(('incomplete', 'Incomplete'),
                 ('complete', 'Complete'),
                 ('failed', 'Failed'))
    )
    template_import = jsonfield.JSONField(
        validators=[validators.template_import_validator],
        null=True, blank=True)

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
        if inputs.count() == 0:
            raise Exception('No fixed input matching %s' % channel)
        if inputs.count() > 1:
            raise Exception('Found %s fixed inputs for channel %s' \
                            % (inputs.count(), channel))
        return inputs.first()

    def get_input(self, channel):
        inputs = filter(lambda i: i.get('channel')==channel,
                        self.inputs)
        if len(inputs) == 0:
            raise NoTemplateInputMatchError(
                'ERROR! No input named "%s" in template "%s"' % (channel, self.name))
        if len(inputs) > 1:
            raise Exception('Found %s inputs for channel %s' \
                            % (len(inputs), channel))
        return inputs[0]

    def get_output(self, channel):
        outputs = filter(lambda o: o.get('channel')==channel,
                         self.outputs)
        assert outputs.count() == 1, \
            'Found %s outputs for channel %s' %(outputs.count(), channel)
        return outputs.first()

    def get_bound_channel(self, step_name, channel_name):
        return self._get_manager().get_bound_channel(step_name, channel_name)


class Workflow(Template):

    steps = models.ManyToManyField(
        'Template',
        through='WorkflowMembership',
        through_fields=('parent_template', 'child_template'),
        related_name='workflows')
    outputs = jsonfield.JSONField(
        validators=[validators.workflow_outputs_validator],
        null=True, blank=True)
    inputs = jsonfield.JSONField(
        validators=[validators.workflow_inputs_validator],
        null=True, blank=True)
    channel_bindings = jsonfield.JSONField(
        validators=[validators.channel_bindings_validator],
        null=True, blank=True)
    raw_data = jsonfield.JSONField(null=True, blank=True)

    def add_step(self, step):
        WorkflowMembership.add_step_to_workflow(step, self)

    def add_steps(self, step_list):
        for step in step_list:
            self.add_step(step)

    def get_bound_channel(self, step_name, channel_name):
        # By default the channel_name on this parent_workflow is
        # the same as that on the child step. If a different name
        # is assigned in channel_bindings, return that instead.
        if not self.channel_bindings:
	    return channel_name
        # Get bindings that match the requested step_name
        this_channel_bindings = filter(lambda x: x.get('step')==step_name,
                          self.channel_bindings)
        if len(this_channel_bindings) == 0:
            return channel_name
        assert len(this_channel_bindings) == 1
	# Bindings are in the form
        # ['internal_channel_name:external_channel_name',...]
        # Convert this to a dict of {internal:external}
        bindings = {}
        for pair in this_channel_bindings[0].get('bindings'):
            internal, external = pair.split(':')
            bindings[internal] = external
	bound_channel = bindings.get(channel_name)
        if not bound_channel:
            return channel_name
        return bound_channel


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
    interpreter = models.CharField(max_length=1024, default='/bin/bash -euo pipefail')
    environment = jsonfield.JSONField(
        validators=[validators.step_environment_validator],
        null=True, blank=True)
    outputs = jsonfield.JSONField(
        validators=[validators.step_outputs_validator],
        null=True, blank=True)
    inputs = jsonfield.JSONField(
        validators=[validators.step_inputs_validator],
        null=True, blank=True)
    resources = jsonfield.JSONField(
        validators=[validators.step_resources_validator],
        null=True, blank=True)
    raw_data = jsonfield.JSONField(null=True, blank=True)

    def clean(self):
        if self.outputs:
            for output in self.outputs:
                if output.get('mode') == 'scatter' and output.get('type') != 'file':
                    if not output.get('parser'):
                        raise ValidationError(
                            "No parser defined on output '%s'" % output.get('channel'))
                if output.get('mode') == 'no_scatter':
                    if output.get('parser'):
                        raise ValidationError(
                            'Parser not allowed on outputs with mode "no_scatter"')
                if output.get('parser') and output.get('type') == 'file':
                    raise ValidationError(
                        'Parser not allowed on outputs with type "file"')


class FixedStepInput(InputOutputNode):

    step = models.ForeignKey(
        'Step',
        related_name='fixed_inputs',
        on_delete=models.CASCADE)
    mode = models.CharField(max_length=255)
    group = models.IntegerField()

    class Meta:
        app_label = 'api'

    @property
    def data(self):
        # Dummy attribute required by serializer
        return


class WorkflowMembership(BaseModel):

    parent_template = models.ForeignKey('Workflow', related_name='children')
    child_template = models.ForeignKey('Template', related_name='parents', 
                                       null=True, blank=True)

    @classmethod
    def add_step_to_workflow(cls, step, parent):
            WorkflowMembership.objects.create(
                parent_template=parent,
                child_template=step)
