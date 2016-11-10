from django.db import models
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.utils import timezone
import uuid

from .base import BaseModel
from .data_objects import DataObject
from .signals import post_save_children
from api.exceptions import *


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

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type = models.CharField(max_length=255,
                            choices=(('workflow', 'Workflow'),
                                     ('step', 'Step')))
    datetime_created = models.DateTimeField(default=timezone.now,
                                            editable=False)
    name = models.CharField(max_length=255)

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
        return "%s@%s" % (self.name, self.id.hex)

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

    # Workflow extends Template with a separate database table
    # but adds no new properties. Its sole purpose is to
    # provide a ForeingKey for WorkflowImport, WorkflowInput, etc.
    # to point to Workflows but not to Steps.

    def add_steps(self, step_list):
        WorkflowMembership.add_steps_to_workflow(step_list, self)

    def get_steps(self):
        return [member.child_template for member in self.children.all()]

    def validate(self):
        pass


class TemplateImport(BaseModel):

    note = models.TextField(max_length=10000, null=True)
    source_url = models.TextField(max_length=1000)
    template = models.OneToOneField(
        'Template',
        related_name='template_import',
        on_delete=models.CASCADE)


class WorkflowInput(models.Model):

    type = models.CharField(
        max_length=255,
        choices=DataObject.TYPE_CHOICES
    )
    channel = models.CharField(max_length=255)
    workflow = models.ForeignKey('Workflow',
                                 related_name='inputs',
                                 on_delete=models.CASCADE)
    hint = models.CharField(max_length=255, null=True)
    
    class Meta:
        app_label='api'


class FixedWorkflowInput(models.Model):

    type = models.CharField(
        max_length=255,
        choices=DataObject.TYPE_CHOICES
    )
    channel = models.CharField(max_length=255)
    data_object = models.ForeignKey('DataObject') # serialized as 'data'
    workflow = models.ForeignKey(
        'Workflow',
        related_name='fixed_inputs',
        on_delete=models.CASCADE)

    class Meta:
        app_label='api'


class WorkflowOutput(BaseModel):

    type = models.CharField(
        max_length=255,
        choices=DataObject.TYPE_CHOICES,
        blank=False
    )
    channel = models.CharField(max_length=255)
    workflow = models.ForeignKey('Workflow',
                                 related_name='outputs',
                                 on_delete=models.CASCADE)

    class Meta:
        app_label='api'


class Step(Template):

    """Steps are smaller units of processing within a Workflow. A Step can 
    give rise to a single process, or it may iterate over an array to produce 
    many parallel processing tasks.
    """

    command = models.TextField()
    interpreter = models.CharField(max_length=255, default='/bin/bash')

    def validate(self):
        pass


class StepEnvironment(BaseModel):

    step = models.OneToOneField('Step',
                                on_delete=models.CASCADE,
                                related_name='environment')
    docker_image = models.CharField(max_length=255)


class StepResourceSet(BaseModel):

    step = models.OneToOneField('Step',
                                on_delete=models.CASCADE,
                                related_name='resources')
    memory = models.CharField(max_length=255, null=True)
    disk_size = models.CharField(max_length=255, null=True)
    cores = models.CharField(max_length=255, null=True)


class StepInput(models.Model):

    type = models.CharField(
        max_length=255,
        choices=DataObject.TYPE_CHOICES
    )
    channel = models.CharField(max_length=255)
    step = models.ForeignKey('Step',
                                 related_name='inputs',
                                 on_delete=models.CASCADE)
    mode = models.CharField(max_length=255, default='no_gather')
    group = models.IntegerField(default=0)
    hint = models.CharField(max_length=255, null=True)

    class Meta:
        app_label='api'


class FixedStepInput(models.Model):

    type = models.CharField(
        max_length=255,
        choices=DataObject.TYPE_CHOICES
    )
    channel = models.CharField(max_length=255)
    data_object = models.ForeignKey('DataObject') # serialized as 'data'
    step = models.ForeignKey(
        'Step',
        related_name='fixed_inputs',
        on_delete=models.CASCADE)
    mode = models.CharField(max_length=255, default='no_gather')
    group = models.IntegerField(default=0)

    class Meta:
        app_label='api'


class StepOutput(models.Model):

    channel = models.CharField(max_length=255)
    type = models.CharField(
        max_length=255,
        choices=DataObject.TYPE_CHOICES,
        blank=False
    )
    step = models.ForeignKey('Step',
                                 related_name='outputs',
                                 on_delete=models.CASCADE)
    mode = models.CharField(max_length=255, default='no_scatter')

    class Meta:
        app_label='api'


class StepOutputSource(BaseModel):
    output = models.OneToOneField(
        StepOutput,
        related_name='source',
        on_delete=models.CASCADE)
    filename = models.CharField(max_length=1024, null=True)
    stream = models.CharField(max_length=255, null=True)


#class StepOutputParser(BaseModel):
#    step_output = models.OneToOneField(
#        StepOutput,
#        related_name='parser',
#        on_delete=models.CASCADE)
#    delimiter = models.CharField(max_length=255, null=True)


class WorkflowMembership(models.Model):

    parent_template = models.ForeignKey('Workflow', related_name='children')
    child_template = models.ForeignKey('Template', related_name='parents', null=True)
    order = models.IntegerField()

    @classmethod
    def add_steps_to_workflow(cls, step_list, parent):
        for step in step_list:
            WorkflowMembership.objects.create(
                parent_template=parent,
                child_template=step,
                order=parent.children.count())

    class Meta:
        app_label = 'api'
        ordering = ['order',]


'''
class Workflow(Template):
    """A collection of steps and/or workflows
    """


    def _post_save_children(self):
        self._validate()

    def _validate(self):
        """Make sure all channel destinations have exactly one source
        """

        source_counts = {}

        def increment_sources_count(sources, channel):
            sources.setdefault(channel, 0)
            sources[channel] += 1

        for input in self.inputs.all():
            increment_sources_count(source_counts, input.channel)
        for fixed_input in self.fixed_inputs.all():
            increment_sources_count(source_counts, fixed_input.channel)
        for step in self.steps.all():
            for output in step.outputs.all():
                increment_sources_count(source_counts, output.channel)

        for channel, count in source_counts.iteritems():
            if count > 1:
                raise ValidationError(
                    'The workflow %s@%s is invalid. It has more than one '\
                    'source for channel "%s". Check workflow inputs and step '\
                    'outputs.' % (
                        self.name,
                        self.id,
                        channel
                    ))

        destinations = []
        for output in self.outputs.all():
            destinations.append(output.channel)
        for step in self.steps.all():
            for input in step.inputs.all():
                destinations.append(input.channel)

        sources = source_counts.keys()
        for destination in destinations:
            if not destination in sources:
                raise ValidationError('The workflow %s@%s is invalid. '\
                                      'The channel "%s" has no source.' % (
                                          self.name,
                                          self.id,
                                          destination
                                      ))
        
@receiver(post_save_children, sender=AbstractWorkflow)
def _post_save_children_workflow_signal_receiver(sender, instance, **kwargs):
    instance._post_save_children()
'''

