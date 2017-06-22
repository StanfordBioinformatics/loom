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


"""
This module defines Templates. A Template is either 
a Step or a Workflow.
Steps have execution details such as command and runtime
environment, while Workflows are collections of other Steps
or Workflows.
"""

def template_import_validator(value):
    pass

def environment_validator(value):
    pass

def outputs_validator(value):
    pass

def inputs_validator(value):
    pass

def resources_validator(value):
    pass


class Template(BaseModel):

    NAME_FIELD = 'name'

    uuid = models.CharField(default=uuidstr, editable=False,
                            unique=True, max_length=255)
    name = models.CharField(max_length=255)
    is_leaf = models.BooleanField()
    datetime_created = models.DateTimeField(default=timezone.now,
                                            editable=False)
    postprocessing_status = models.CharField(
        max_length=255,
        default='incomplete',
        choices=(('incomplete', 'Incomplete'),
                 ('complete', 'Complete'),
                 ('failed', 'Failed'))
    )
    command = models.TextField(blank=True)
    interpreter = models.CharField(max_length=1024, blank=True)
    environment = jsonfield.JSONField(validators=[environment_validator],
                                      null=True, blank=True)
    resources = jsonfield.JSONField(validators=[resources_validator],
                                      null=True, blank=True)
    template_import = jsonfield.JSONField(validators=[template_import_validator],
                                          null=True, blank=True)
    steps = models.ManyToManyField(
        'Template',
        through='TemplateMembership',
        through_fields=('parent_template', 'child_template'),
        related_name='templates')
    outputs = jsonfield.JSONField(validators=[outputs_validator],
                                  null=True, blank=True)
    inputs = jsonfield.JSONField(validators=[inputs_validator],
                                 null=True, blank=True)
    raw_data = jsonfield.JSONField(null=True, blank=True)

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

    def add_step(self, step):
        TemplateMembership.add_step_to_workflow(step, self)

    def add_steps(self, step_list):
        for step in step_list:
            self.add_step(step)


class FixedInput(InputOutputNode):

    template = models.ForeignKey(
        'Template',
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


class TemplateMembership(BaseModel):

    parent_template = models.ForeignKey('Template', related_name='children')
    child_template = models.ForeignKey('Template', related_name='parents', 
                                       null=True, blank=True)

    @classmethod
    def add_step_to_workflow(cls, step, parent):
            TemplateMembership.objects.create(
                parent_template=parent,
                child_template=step)
