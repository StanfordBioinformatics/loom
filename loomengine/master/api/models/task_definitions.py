from django.core.exceptions import ObjectDoesNotExist
from django.db import models

from .base import BaseModel, BasePolymorphicModel, render_from_template
from .data_objects import DataObject
from api import get_setting


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

    task_run = models.OneToOneField('TaskRun',
                                    related_name='task_definition',
                                    on_delete=models.CASCADE)
    interpreter = models.TextField()
    command = models.TextField()

    @classmethod
    def create_from_task_run(cls, task_run):
        task_definition = cls.objects.create(
            task_run=task_run)
        task_definition._initialize_inputs()
        task_definition._initialize_outputs()
        task_definition._initialize_environment()
        task_definition._initialize_command()

    def _initialize_inputs(self):
        for input in self.task_run.inputs.all():
            TaskDefinitionInput.objects.create(
                data_object_content=input.data_object.get_content(),
                task_definition=self,
                task_run_input=input,
                type=input.type)

    def _initialize_outputs(self):
        for task_run_output in self.task_run.outputs.all():
            task_definition_output = TaskDefinitionOutput.objects.create(
                task_definition=self,
                task_run_output=task_run_output,
                type=task_run_output.type,
            )
            self._initialize_output_source(task_definition_output, task_run_output.step_run_output.source),
            self._initialize_output_parser(task_definition_output, task_run_output.step_run_output),

    def _initialize_output_source(self, task_definition_output, step_run_output_source):
        stream=step_run_output_source.stream
        if step_run_output_source.filename:
            filename = render_from_template(
                step_run_output_source.filename,
                self.task_run.get_input_context())
        else:
            filename = None

        return TaskDefinitionOutputSource.objects.create(
            task_definition_output=task_definition_output,
            filename=filename,
            stream=stream)

    def _initialize_output_parser(self, task_definition_output, step_run_output):
        try:
            step_run_output_parser = step_run_output.parser
        except ObjectDoesNotExist:
            return

        return TaskDefinitionOutputParser.objects.create(
            task_definition_output=task_definition_output,
            type=step_run_output_parser.type,
            delimiter=step_run_output_parser.delimiter)

    def _initialize_environment(self):
        # TODO get specific docker image ID
        from api.serializers import TaskDefinitionEnvironmentSerializer
        environment_data = {
            'docker_image':
            self.task_run.step_run.template.environment.docker_image,
        }
        s = TaskDefinitionEnvironmentSerializer(
            data=environment_data,
            context={'parent_field': 'task_definition',
                     'parent_instance': self})
        s.is_valid(raise_exception=True)
        s.save()
        
    def _initialize_command(self):
        self.interpreter = self.task_run.get_interpreter()
        self.command = self.task_run.render_command()
        self.save()
        
        
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
    task_run_input = models.OneToOneField(
        'TaskRunInput',
        related_name='task_definition_input',
        on_delete=models.CASCADE)
    data_object_content = models.ForeignKey(
        'DataObjectContent',
        on_delete=models.PROTECT)
    type = models.CharField(
        max_length=255,
        choices=DataObject.TYPE_CHOICES
    )


class TaskDefinitionOutput(BaseModel):

    task_definition = models.ForeignKey(
        'TaskDefinition',
        related_name='outputs',
        on_delete=models.CASCADE)
    task_run_output = models.OneToOneField(
        'TaskRunOutput',
        related_name='task_definition_output',
        on_delete=models.CASCADE)
    type = models.CharField(
        max_length=255,
        choices=DataObject.TYPE_CHOICES
    )

class TaskDefinitionOutputSource(BaseModel):

    task_definition_output = models.OneToOneField(
        'TaskDefinitionOutput',
        related_name = 'source',
        on_delete=models.CASCADE)
    filename = models.CharField(max_length=1024, null=True)
    stream = models.CharField(max_length=255, null=True)

class TaskDefinitionOutputParser(BaseModel):

    task_definition_output = models.OneToOneField(
        'TaskDefinitionOutput',
        related_name = 'parser',
        on_delete=models.CASCADE)
    type = models.CharField(max_length=255)
    delimiter = models.CharField(max_length=255, null=True)
