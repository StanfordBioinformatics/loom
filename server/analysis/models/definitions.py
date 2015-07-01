from django.db import models

from .common import AnalysisAppBaseModel
from immutable.models import ImmutableModel


"""
Models in this module form the core definition of an anlysis step.

These models are immutable. Their primary key is a hash of the model's
contents, so no identical duplicates exist. Immutable models cannot be 
edited after they are created.

StepDefinitions from different sources or even different 
servers are identical and considered equivalent, although 
multiple related request or run objects may exist from the
same analysis being run at different times or on different
servers.
"""


class StepDefinition(ImmutableModel, AnalysisAppBaseModel):
    """
    Contains the unchanging parts of a step, with inputs specified.
    Excludes settings that do not alter results, e.g. resources
    """
    _class_name = ('step_definition', 'step_definitions')
    template = models.ForeignKey('StepDefinitionTemplate')
    data_bindings = models.ManyToManyField('StepDefinitionDataBinding')

class StepDefinitionTemplate(ImmutableModel, AnalysisAppBaseModel):
    """
    Everything that defines a an analysis step except for the input data
    """
    _class_name = ('step_definition_template', 'step_definition_templates')
    input_ports = models.ManyToManyField('StepDefinitionInputPort')
    output_ports = models.ManyToManyField('StepDefinitionOutputPort')
    command = models.CharField(max_length = 256)
    environment = models.ForeignKey('StepDefinitionEnvironment')

class StepDefinitionInputPort(ImmutableModel, AnalysisAppBaseModel):
    _class_name = ('step_definition_input_port', 'step_definition_input_ports')
    file_path = models.CharField(max_length = 256)

class StepDefinitionOutputPort(ImmutableModel, AnalysisAppBaseModel):
    _class_name = ('step_definition_output_port', 'step_definition_output_ports')
    file_path = models.CharField(max_length = 256)

class StepDefinitionDataBinding(ImmutableModel, AnalysisAppBaseModel):
    _class_name = ('step_definition_input_binding', 'step_definition_input_bindings')
    file = models.ForeignKey('File')
    input_port = models.ForeignKey('StepDefinitionInputPort')

class StepDefinitionEnvironment(ImmutableModel, AnalysisAppBaseModel):
    _class_name = ('step_definition_environment', 'step_definition_environments')

class StepDefinitionDockerImage(StepDefinitionEnvironment):
    _class_name = ('step_definition_docker_image', 'step_definition_docker_images')
    docker_image = models.CharField(max_length = 100)
