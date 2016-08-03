from django.db import models

from .base import BaseModel, BasePolymorphicModel
from .data_objects import DataObject
from analysis import get_setting


"""Models in this module form the core definition of an analysis task 
to be run.
"""

class TaskDefinition(BaseModel):
    """A TaskDefinition is the fundamental unit of analysis work to be done.
    It is an unambiguous definition of an analysis step, its inputs and 
    environment. It excludes requested resources, as these do not alter 
    results.

    The TaskDefinition exists so that if someone wants to execute analysis that
    has already been performed, it will match the old TaskDefinition and we can
    locate previously generated results.
    """

    command = models.CharField(max_length=256)


class TaskDefinitionEnvironment(BasePolymorphicModel):

    task_definition = models.OneToOneField(
        'TaskDefinition',
        on_delete=models.CASCADE,
        related_name='environment')


class TaskDefinitionDockerEnvironment(TaskDefinitionEnvironment):

    docker_image = models.CharField(max_length = 100)


class TaskDefinitionInput(BaseModel):

    task_definition = models.ForeignKey(
        'TaskDefinition',
        related_name='inputs',
        on_delete=models.CASCADE)
    data_object_content = models.ForeignKey(
        'DataObjectContent',
        on_delete=models.PROTECT)
    type = models.CharField(
        max_length=255,
        choices=DataObject.TYPE_CHOICES)


class TaskDefinitionOutput(BaseModel):

    task_definition = models.ForeignKey(
        'TaskDefinition',
        related_name='outputs',
        on_delete=models.CASCADE)
    filename = models.CharField(max_length=255)
    type = models.CharField(
        max_length=255,
        choices=DataObject.TYPE_CHOICES
    )

    def get_substitution_value(self):
        return self.filename
