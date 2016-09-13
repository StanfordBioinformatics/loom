from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
import uuid

from .base import BaseModel, BasePolymorphicModel
from .data_objects import DataObject
from api.exceptions import *


"""
This module defines Workflow and its children.
A Workflow is a template of an analysis to run, where
some inputs may be specified at runtime.
"""

class AbstractWorkflow(BasePolymorphicModel):

    """An AbstractWorkflow is either a step or a collection of steps.
    """

    NAME_FIELD = 'name'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    datetime_created = models.DateTimeField(default=timezone.now,
                                            editable=False)
    name = models.CharField(max_length=255)
    parent_workflow = models.ForeignKey('Workflow',
                                        related_name='steps',
                                        null=True)

    def get_name_and_id(self):
        return "%s@%s" % (self.name, self.id.hex)

    def get_fixed_input(self, channel):
        inputs = self.fixed_inputs.filter(channel=channel)
        assert inputs.count() == 1
        return inputs.first()

    def get_input(self, channel):
        inputs = self.inputs.filter(channel=channel)
        assert inputs.count()
        return inputs.first()

    def get_output(self, channel):
        outputs = self.outputs.filter(channel=channel)
        assert outputs.count() == 1
        return outputs.first()

    class Meta:
        ordering = ['datetime_created']


class Workflow(AbstractWorkflow):
    """A collection of steps and/or workflows
    """

    def after_create(self):
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

    def is_step(self):
        return False


class Step(AbstractWorkflow):
    """Steps are smaller units of processing within a Workflow. A Step can 
    give rise to a single process, or it may iterate over an array to produce 
    many parallel processing tasks.
    """

    command = models.TextField()

    def is_step(self):
        return True


class RequestedEnvironment(BasePolymorphicModel):

    step = models.OneToOneField('Step',
                                on_delete=models.CASCADE,
                                related_name='environment')


class RequestedDockerEnvironment(RequestedEnvironment):

    docker_image = models.CharField(max_length=255)


class RequestedResourceSet(BaseModel):

    step = models.OneToOneField('Step',
                                on_delete=models.CASCADE,
                                related_name='resources')
    memory = models.CharField(max_length=255, null=True)
    disk_size = models.CharField(max_length=255, null=True)
    cores = models.CharField(max_length=255, null=True)


class AbstractWorkflowInput(BasePolymorphicModel):

    type = models.CharField(
        max_length=255,
        choices=DataObject.TYPE_CHOICES
    )
    channel = models.CharField(max_length=255)

    class Meta:
        abstract = True


class AbstractRuntimeWorkflowInput(AbstractWorkflowInput):

    hint = models.CharField(max_length=255, null=True)

    class Meta:
        abstract = True


class AbstractFixedWorkflowInput(AbstractWorkflowInput):

    data_object = models.ForeignKey('DataObject') # serialized as 'value'

    def value(self):
        return self.data_object.get_display_value()
    
    class Meta:
        abstract = True


class WorkflowInput(AbstractRuntimeWorkflowInput):

    workflow = models.ForeignKey('Workflow',
                                 related_name='inputs',
                                 on_delete=models.CASCADE)


class StepInput(AbstractRuntimeWorkflowInput):

    step = models.ForeignKey('Step',
                             related_name='inputs',
                             on_delete=models.CASCADE)


class FixedWorkflowInput(AbstractFixedWorkflowInput):

    workflow = models.ForeignKey(
        'Workflow',
        related_name='fixed_inputs',
        on_delete=models.CASCADE)


class FixedStepInput(AbstractFixedWorkflowInput):

    step = models.ForeignKey(
        'Step',
        related_name='fixed_inputs',
        on_delete=models.CASCADE)


class AbstractOutput(BasePolymorphicModel):

    channel = models.CharField(max_length=255)
    type = models.CharField(
        max_length=255,
        choices=DataObject.TYPE_CHOICES,
        blank=False
    )

    class Meta:
        abstract = True


class WorkflowOutput(AbstractOutput):

    workflow = models.ForeignKey('Workflow',
                                 related_name='outputs',
                                 on_delete=models.CASCADE)


class StepOutput(AbstractOutput):

    filename = models.CharField(max_length=255)
    step = models.ForeignKey('Step',
                             related_name='outputs',
                             on_delete=models.CASCADE)


class WorkflowImport(BaseModel):

    note = models.TextField(max_length=10000, null=True)
    source_url = models.TextField(max_length=1000)
    workflow = models.OneToOneField(
        'AbstractWorkflow',
        related_name='workflow_import',
        on_delete=models.CASCADE)
