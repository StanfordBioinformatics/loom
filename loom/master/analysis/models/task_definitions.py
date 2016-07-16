from django.db import models
from django.core import exceptions

from analysis import get_setting
from analysis.fields import DuplicateManyToManyField

from .base import BaseModel, BasePolymorphicModel
from .data_objects import DataObject, DataObjectContent



"""Models in this module form the core definition of an analysis task to be run.
"""


class TaskDefinition(BaseModel):
    """A TaskDefinition is the fundamental unit of analysis work to be done.
    It is an unambiguous definition of an analysis step, its inputs and environment.
    It excludes requested resources, as these do not alter results.
    The TaskDefinition exists so that if someone wants to execute analysis that
    has already been performed, it will match the old TaskDefinition and we can
    locate previously generated results.
    """

    inputs = DuplicateManyToManyField('TaskDefinitionInput')
    outputs = DuplicateManyToManyField('TaskDefinitionOutput')
    command = models.CharField(max_length=256)
    environment = models.ForeignKey('TaskDefinitionEnvironment')


class TaskDefinitionEnvironment(BasePolymorphicModel):

    pass


class TaskDefinitionDockerEnvironment(TaskDefinitionEnvironment):

    docker_image = models.CharField(max_length = 100)


class TaskDefinitionInput(BaseModel):

    data_object_content = models.ForeignKey('DataObjectContent')
    type = models.CharField(
        max_length=255,
        choices=DataObject.TYPE_CHOICES
    )

class TaskDefinitionOutput(BaseModel):

    filename = models.CharField(max_length=255)
    type = models.CharField(
        max_length=255,
        choices=DataObject.TYPE_CHOICES
    )

    def get_substitution_value(self):
        return self.filename
