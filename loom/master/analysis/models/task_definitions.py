from django.core import exceptions

from analysis.models.base import AnalysisAppInstanceModel, AnalysisAppImmutableModel
from analysis.models.data_objects import FileStorageLocation, DataObject
from universalmodels import fields


"""Models in this module form the core definition of an anlysis task.

These models are immutable. Their primary key is a hash of the model's
contents, so no identical duplicates exist. Immutable models cannot be 
edited after they are created.

Since TaskDefinitions are ImmutableModels, TaskDefinitions from different 
sources or even different servers are identical, which makes it easy to
know when a task has already been run.
"""


class TaskDefinition(AnalysisAppImmutableModel):
    """Contains the unchanging parts of a step, with inputs specified.
    Excludes requested resources, as these do not alter results.
    """

    inputs = fields.ManyToManyField('TaskDefinitionInput')
    outputs = fields.ManyToManyField('TaskDefinitionOutput')
    command = fields.CharField(max_length=256)
    environment = fields.ForeignKey('TaskDefinitionEnvironment')

    @classmethod
    def render(cls, step_run, input_data_objects):
        return {
            'inputs': [TaskDefinitionInput.render(input, input_data_objects) for input in step_run.step_run_inputs.all()],
            'outputs': [TaskDefinitionOutput.render(output) for output in step_run.step_run_outputs.all()],
            'environment': TaskDefinitionEnvironment.render(step_run.step.environment),
            'command': cls._render_command(step_run.step.command, input_data_objects)
        }

    @classmethod
    def _render_command(cls, raw_command, input_data_objects):
        #TODO Use template to substitute file paths in command
        return raw_command

class TaskDefinitionEnvironment(AnalysisAppImmutableModel):

    @classmethod
    def render(cls, requested_environment):
        # TODO - get Docker image ID
        return {
            'docker_image': requested_environment.downcast().docker_image
        }


class TaskDefinitionDockerImage(TaskDefinitionEnvironment):

    docker_image = fields.CharField(max_length = 100)


class TaskDefinitionInput(AnalysisAppImmutableModel):

    data_object = fields.ManyToManyField('DataObject')

    @classmethod
    def render(cls, step_run_input, input_data_objects):
        return {}

class TaskDefinitionOutput(AnalysisAppImmutableModel):

    path = fields.CharField(max_length=255)

    @classmethod
    def render(cls, step_run_output):
        return {}
