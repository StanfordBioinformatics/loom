from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
import jsonfield
from mptt.models import MPTTModel, TreeForeignKey

from .base import BaseModel
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


class Template(BaseModel):

    NAME_FIELD = 'name'
    ID_FIELD = 'uuid'

    uuid = models.CharField(default=uuidstr, editable=False,
                            unique=True, max_length=255)
    name = models.CharField(max_length=255,
                            validators=[validators.TemplateValidator.validate_name])
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
    environment = jsonfield.JSONField(
        null=True, blank=True,
        validators=[validators.validate_environment])
    resources = jsonfield.JSONField(
        null=True, blank=True,
        validators=[validators.validate_resources])
    comments = models.TextField(null=True, blank=True)
    import_comments = models.TextField(null=True, blank=True)
    imported_from_url = models.TextField(
        null=True, blank=True,
	validators=[validators.validate_url])
    imported = models.BooleanField(default=False)
    steps = models.ManyToManyField(
        'Template',
        through='TemplateMembership',
        through_fields=('parent_template', 'child_template'),
        related_name='templates')
    outputs = jsonfield.JSONField(
        validators=[validators.TemplateValidator.validate_outputs],
        null=True, blank=True
    )
    raw_data = jsonfield.JSONField(null=True, blank=True)

    def get_name_and_id(self):
        return "%s@%s" % (self.name, self.id)

    def get_input(self, channel):
        inputs = self.inputs.filter(channel=channel)
        if inputs.count() == 0:
            raise ObjectDoesNotExist('No input with channel "%s"' % channel)
        assert inputs.count() == 1, \
            'Found %s inputs for channel %s' % (inputs.count(), channel)
        return inputs.first()

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


class TemplateInput(InputOutputNode):

    template = models.ForeignKey(
        'Template',
        related_name='inputs',
        on_delete=models.CASCADE)
    hint = models.CharField(max_length=1000, blank=True)
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


class TemplateNode(MPTTModel, BaseModel):

    parent = TreeForeignKey('self', null=True, blank=True,
                            related_name='children', db_index=True,
                            on_delete=models.SET_NULL)
    template = models.ForeignKey('Template', null=True,
                                 related_name='template_nodes',
                                 on_delete = models.PROTECT)
