from django.core import exceptions

from analysis.models.base import AnalysisAppInstanceModel, AnalysisAppImmutableModel
from analysis.models.data_objects import FileStorageLocation, DataObject
from universalmodels import fields


"""Models in this module form the core definition of an analysis task to be run.
"""


class TaskDefinition(AnalysisAppImmutableModel):
    """A TaskDefinition is the fundamental unit of analysis work to be done.
    It is an unambiguous definition of an analysis step, its inputs and environment.
    It excludes requested resources, as these do not alter results.
    The TaskDefinition exists so that if someone wants to execute analysis that
    has already been performed, it will match the old TaskDefinition and we can
    locate previously generated results.
    """

    inputs = fields.ManyToManyField('TaskDefinitionInput')
    outputs = fields.ManyToManyField('TaskDefinitionOutput')
    command = fields.CharField(max_length=256)
    environment = fields.ForeignKey('TaskDefinitionEnvironment')


class TaskDefinitionEnvironment(AnalysisAppImmutableModel):

    pass


class TaskDefinitionDockerImage(TaskDefinitionEnvironment):

    docker_image = fields.CharField(max_length = 100)


class TaskDefinitionInput(AnalysisAppImmutableModel):

    data_object = fields.ForeignKey('DataObject')


class TaskDefinitionOutput(AnalysisAppImmutableModel):

    path = fields.CharField(max_length=255)
