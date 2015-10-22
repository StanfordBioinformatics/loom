from django.db import models

from .common import AnalysisAppBaseModel
from immutable.models import ImmutableModel
from .files import FileStorageLocation, DataObject


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
    FOREIGN_KEY_CHILDREN = ['environment']
    input_ports = models.ManyToManyField('StepDefinitionInputPort')
    output_ports = models.ManyToManyField('StepDefinitionOutputPort')
    command = models.CharField(max_length = 256)
    environment = models.ForeignKey('StepDefinitionEnvironment')

    def get_step_run(self, cutofftime=None):
        # TODO: for stability, return oldest by default
        # For forced reruns, filter any older than given cutoff
        step_runs = self.steprun_set
        if step_runs.count() == 0:
            return None
        else:
            return step_runs.first()

    def get_input_bundles(self):
        return [port.get_input_bundle() for port in self.input_ports.all()]


class StepDefinitionInputPort(ImmutableModel, AnalysisAppBaseModel):
    _class_name = ('step_definition_input_port', 'step_definition_input_ports')
    FOREIGN_KEY_CHILDREN = ['data_object']
    file_name = models.CharField(max_length = 256)
    is_array = models.BooleanField()
    data_object = models.ForeignKey(DataObject)

    def get_files_and_locations_list(self):
        file_list = self.get('data_object').render_as_list()
        return [self._get_file_and_locations(file) for file in file_list]

    def _get_file_and_locations(self, file):
        file_storage_locations = [l.to_serializable_obj() for l in FileStorageLocation.get_by_file(file).all()]
        return {'file': file.to_serializable_obj(),
                'file_storage_locations': file_storage_locations}

    def get_input_bundle(self):
        # Each InputBundle contains info needed by StepRunner
        # to make inputs locally available before executing command
        return {
            'files_and_locations': self.get_files_and_locations_list(),
            'input_port': self.to_serializable_obj()
            }


class StepDefinitionOutputPort(ImmutableModel, AnalysisAppBaseModel):
    _class_name = ('step_definition_output_port', 'step_definition_output_ports')
    file_name = models.CharField(max_length = 256, null=True)
    glob = models.CharField(max_length = 256, null=True)
    is_array = models.BooleanField()


class StepDefinitionEnvironment(ImmutableModel, AnalysisAppBaseModel):
    _class_name = ('step_definition_environment', 'step_definition_environments')


class StepDefinitionDockerImage(StepDefinitionEnvironment):
    _class_name = ('step_definition_docker_image', 'step_definition_docker_images')
    docker_image = models.CharField(max_length = 100)
