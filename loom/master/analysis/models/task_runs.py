from copy import deepcopy
from django.db import models
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
import os
import uuid

from analysis.models.task_definitions import *
from analysis.models.data_objects import DataObject, FileDataObject
from analysis.models.workflows import Step, RequestedResourceSet
from analysis import get_setting
from analysis.task_manager.factory import TaskManagerFactory
from .base import BaseModel, BasePolymorphicModel, render_from_template


class TaskRun(BaseModel):

    """One instance of executing a TaskDefinition, i.e. executing a Step on a 
    particular set of inputs.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    step_run = models.ForeignKey('StepRun',
                                 related_name='task_runs',
                                 on_delete=models.CASCADE)

    # No 'environment' field, because this is in the TaskDefinition.
    # 'resources' field included (by FK) since this is not in TaskDefinition.

    @property
    def name(self):
        return self.step_run.name
                    
    @classmethod
    def create_from_input_set(cls, input_set, step_run):
        task_run = TaskRun.objects.create(step_run=step_run)
        for input in input_set:
            step_run_input = step_run.get_input(input.channel)
            TaskRunInput.objects.create(
                step_run_input=step_run_input,
                task_run=task_run,
                data_object = input.data_object)
        for step_run_output in step_run.outputs.all():
            TaskRunOutput.objects.create(
                step_run_output=step_run_output,
                task_run=task_run)
        TaskDefinition.create_from_task_run(task_run)
        return task_run

    def run(self):
        task_manager = TaskManagerFactory.get_task_manager()
        task_manager.run(self)

    def post_create(self):
        self._initialize_inputs_outputs()

    def _initialize_inputs_outputs(self):
        # TODO - check to see if the input already exists
        for step_run_input in self.step_run.inputs.all():
            TaskRunInput.objects.create(
                task_run=self,
                step_run_input=step_run_input,
                task_definition_input=task_definition_input)

    def get_input_context(self):
        context = {}
        for input in self.inputs.all():
            context[input.channel] = input.data_object\
                                            .get_substitution_value()
        return context
        
    def get_output_context(self):
        context = {}
        for output in self.outputs.all():
            # This returns a value only for Files, where the filename
            # is known beforehand and may be used in the command.
            # For other types, nothing is added to the context.
            if output.type == 'file':
                context[output.channel] = output.filename
        return context

    def get_full_context(self):
        context = self.get_input_context()
        context.update(self.get_output_context())
        return context

    def render_command(self):
        return render_from_template(
            self.step_run.template.command,
            self.get_full_context())

    def push_results_from_task_run_attempt(self, attempt):
        for output in attempt.outputs.all():
            output.task_run_output.push(output.data_object)


class TaskRunInput(BaseModel):

    task_run = models.ForeignKey('TaskRun',
                                 related_name='inputs',
                                 on_delete=models.CASCADE)
    data_object = models.ForeignKey('DataObject', on_delete=models.PROTECT)
    step_run_input = models.ForeignKey('AbstractStepRunInput',
                                       related_name='task_run_inputs',
                                       null=True,
                                       on_delete=models.PROTECT)

    @property
    def channel(self):
        return self.step_run_input.channel

    @property
    def type(self):
        return self.step_run_input.type

class TaskRunOutput(BaseModel):

    step_run_output = models.ForeignKey('StepRunOutput',
                                        related_name='task_run_outputs',
                                        on_delete=models.CASCADE,
                                        null=True)
    task_run = models.ForeignKey('TaskRun',
                                 related_name='outputs',
                                 on_delete=models.CASCADE)
    data_object = models.ForeignKey('DataObject',
                                    null=True,
                                    on_delete=models.PROTECT)

    @property
    def filename(self):
        # This will raise ObjectDoesNotExist if task_definition_output
        # is not yet attached.
        return self.task_definition_output.filename

    @property
    def channel(self):
        return self.step_run_output.step_output.channel

    @property
    def type(self):
        return self.step_run_output.step_output.type

    def push(self, data_object):
        if self.data_object is None:
            self.data_object=data_object
            self.save()
        self.step_run_output.push_without_index(data_object)

class TaskRunResourceSet(BaseModel):
    task_run = models.OneToOneField('TaskRun',
                                on_delete=models.CASCADE,
                                related_name='resources')
    memory = models.CharField(max_length=255, null=True)
    disk_size = models.CharField(max_length=255, null=True)
    cores = models.CharField(max_length=255, null=True)


class TaskRunAttempt(BasePolymorphicModel):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task_run = models.ForeignKey('TaskRun',
                                 related_name='task_run_attempts',
                                 on_delete=models.CASCADE)
    status = models.CharField(
        max_length=255,
        default='incomplete',
        choices=(('incomplete', 'Incomplete'),
                 ('complete', 'Complete'),
                 ('failed', 'Failed')))

    @property
    def task_definition(self):
        return self.task_run.task_definition

    @property
    def name(self):
        return self.task_run.name

    @classmethod
    def create_from_task_run(cls, task_run):
        model = cls.objects.create(task_run=task_run)
        model.post_create()
        return model

    def post_create(self):
        self._initialize_inputs_outputs()

    def post_update(self):
        self.task_run.push_results_from_task_run_attempt(self)

    def _initialize_inputs_outputs(self):
        # TODO check if inputs/outputs already exist
        for input in self.task_run.inputs.all():
            TaskRunAttemptInput.objects.create(
                task_run_attempt=self,
                task_run_input=input,
                data_object=input.data_object)
        for output in self.task_run.outputs.all():
            TaskRunAttemptOutput.objects.create(
                task_run_attempt=self,
                task_run_output=output)

    @classmethod
    def get_working_dir(cls, task_run_attempt_id):
        return os.path.join(get_setting('FILE_ROOT_FOR_WORKER'),
                            'runtime_volumes',
                            task_run_attempt_id,
                            'work')
    
    @classmethod
    def get_log_dir(cls, task_run_attempt_id):
        return os.path.join(get_setting('FILE_ROOT_FOR_WORKER'),
                            'runtime_volumes',
                            task_run_attempt_id,
                            'logs')

    def get_provenance_data(self, files=None, tasks=None, edges=None):
        if files is None:
            files = set()
        if tasks is None:
            tasks = set()
        if edges is None:
            edges = set()

        tasks.add(self)

        for input in self.task_run.inputs.all():
            data = input.data_object
            if data.type == 'file':
                files.add(data)
                edges.add((data.id.hex, self.id.hex))
                data.get_provenance_data(files, tasks, edges)
            else:
                # TODO
                pass

        return files, tasks, edges


class TaskRunAttemptInput(BaseModel):

    task_run_attempt = models.ForeignKey(
        'TaskRunAttempt',
        related_name='inputs',
        on_delete=models.CASCADE)
    data_object = models.ForeignKey(
        'DataObject',
        null=True,
        related_name='task_run_attempt_inputs',
        on_delete=models.PROTECT)
    task_run_input = models.ForeignKey(
        'TaskRunInput',
        related_name='task_run_attempt_inputs',
        null=True, on_delete=models.PROTECT)

    @property
    def type(self):
        return self.task_run_input.type

    @property
    def channel(self):
        return self.task_run_input.channel

class TaskRunAttemptOutput(BaseModel):

    task_run_attempt = models.ForeignKey(
        'TaskRunAttempt',
        related_name='outputs',
        on_delete=models.CASCADE)
    data_object = models.OneToOneField(
        'DataObject',
        null=True,
        related_name='task_run_attempt_output',
        on_delete=models.PROTECT)
    task_run_output = models.ForeignKey(
        'TaskRunOutput',
        related_name='task_run_attempt_outputs',
        on_delete=models.PROTECT)

    @property
    def type(self):
        return self.task_run_output.type

    @property
    def channel(self):
        return self.task_run_output.channel

    @property
    def filename(self):
        return self.task_run_output.filename

    def push(self, data_object):
        self.task_run_output.push(data_object)


class TaskRunAttemptLogFile(BaseModel):

    task_run_attempt = models.ForeignKey(
        'TaskRunAttempt',
        related_name='log_files',
        on_delete=models.CASCADE)
    log_name = models.CharField(max_length=255)
    file_data_object = models.OneToOneField(
        'FileDataObject',
        null=True,
        related_name='task_run_attempt_log_file',
        on_delete=models.PROTECT)

    def post_create(self):
        if self.file_data_object is None:
            self.file_data_object = FileDataObject.objects.create(source_type='log')
            self.save()
