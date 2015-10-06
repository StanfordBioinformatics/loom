from django.db import models

from .common import AnalysisAppBaseModel
from immutable.models import ImmutableModel
from .files import FileStorageLocation

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
    FOREIGN_KEY_CHILDREN = ['template']
    template = models.ForeignKey('StepDefinitionTemplate')
    data_bindings = models.ManyToManyField('StepDefinitionDataBinding')

    def get_step_run(self):
        # TODO handle multiple results according to
        # a sensible policy
        step_runs = self.steprun_set
        if step_runs.count() == 0:
            return None
        else:
            return step_runs.first()

    def get_data_binding(self, port):
        return self.data_bindings.get(input_port=port)

    def get_input_data_object(self, port):
        data_binding = self.get_data_binding(port)
        return data_binding.data_object
        

class StepDefinitionTemplate(ImmutableModel, AnalysisAppBaseModel):
    """
    Everything that defines a an analysis step except for the input data
    """
    _class_name = ('step_definition_template', 'step_definition_templates')
    FOREIGN_KEY_CHILDREN = ['environment']
    input_ports = models.ManyToManyField('StepDefinitionInputPort')
    output_ports = models.ManyToManyField('StepDefinitionOutputPort')
    command = models.CharField(max_length = 256)
    environment = models.ForeignKey('StepDefinitionEnvironment')

class StepDefinitionInputPort(ImmutableModel, AnalysisAppBaseModel):
    _class_name = ('step_definition_input_port', 'step_definition_input_ports')
    name = models.CharField(max_length = 256)
    file_path = models.CharField(max_length = 256)

class StepDefinitionOutputPort(ImmutableModel, AnalysisAppBaseModel):
    _class_name = ('step_definition_output_port', 'step_definition_output_ports')
    name = models.CharField(max_length = 256)
    file_path = models.CharField(max_length = 256)

class StepDefinitionDataBinding(ImmutableModel, AnalysisAppBaseModel):
    _class_name = ('step_definition_data_binding', 'step_definition_data_bindings')
    FOREIGN_KEY_CHILDREN = ['data_object', 'input_port']
    data_object = models.ForeignKey('DataObject')
    input_port = models.ForeignKey('StepDefinitionInputPort')

    def get_files_and_locations_list(self):
        file_list = self.get('data_object').render_as_list()
        return [self.get_file_and_locations(file) for file in file_list]

    def get_file_and_locations(self, file):
        file_storage_locations = [l.to_serializable_obj() for l in FileStorageLocation.get_by_file(file).all()]
        return {'file': file.to_serializable_obj(),
                'file_storage_locations': file_storage_locations}

    def get_input_bundle(self):
        return {
            'files_and_locations': self.get_files_and_locations_list(),
            'input_port': self.input_port.to_serializable_obj()
            }

class StepDefinitionEnvironment(ImmutableModel, AnalysisAppBaseModel):
    _class_name = ('step_definition_environment', 'step_definition_environments')

class StepDefinitionDockerImage(StepDefinitionEnvironment):
    _class_name = ('step_definition_docker_image', 'step_definition_docker_images')
    docker_image = models.CharField(max_length = 100)
