from copy import deepcopy
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.dispatch import receiver
import os
import uuid

from .base import BaseModel, BasePolymorphicModel, render_from_template
from api.models.task_definitions import *
from api.models.data_objects import DataObject, FileDataObject
from api.models.workflows import Step, RequestedResourceSet
from api import get_setting
from api.task_manager.factory import TaskManagerFactory
from loomengine.utils.connection import TASK_RUN_ATTEMPT_STATUSES

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

    @property
    def errors(self):
        if self.task_run_attempts.count() == 0:
            return TaskRunAttemptError.objects.none()
        return self.task_run_attempts.first().errors

    @property
    def status(self):
        if self.task_run_attempts.count() == 0:
            return ''
        return self.task_run_attempts.first().status

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
            if output.source.filename:
                context[output.channel] = output.source.filename
        return context

    def get_full_context(self):
        context = self.get_input_context()
        context.update(self.get_output_context())
        return context

    def get_interpreter(self):
        return self.step_run.template.interpreter
    
    def render_command(self):
        return render_from_template(
            self.step_run.template.command,
            self.get_full_context())

    def update_status(self):
        self.step_run.update_status()

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
    def source(self):
        # This will raise ObjectDoesNotExist if task_definition_output
        # is not yet attached.
        return self.task_definition_output.source

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
            self.step_run_output.add_data_object([], data_object)


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
    task_run_as_accepted_attempt = models.OneToOneField(
        'TaskRun',
        related_name='accepted_task_run_attempt',
        on_delete=models.CASCADE,
        null=True)
    container_id = models.CharField(max_length=255, null=True)
    image_id = models.CharField(max_length=255, null=True)
    last_update = models.DateTimeField(auto_now=True)

    STATUSES = TASK_RUN_ATTEMPT_STATUSES

    status = models.CharField(
        max_length=255,
        default=STATUSES.NOT_STARTED
    )

    def add_error(self, message, detail):
        error = TaskRunAttemptError.objects.create(
            message=message, detail=detail, task_run_attempt=self)
        error.save()

    def abort(self):
        self.status = self.STATUSES.ABORTED
        self.save()

    @property
    def task_definition(self):
        return self.task_run.task_definition

    @property
    def name(self):
        return self.task_run.name

    @classmethod
    def create_from_task_run(cls, task_run):
        task_run_attempt = cls.objects.create(task_run=task_run)
        task_run_attempt.initialize()
        return task_run_attempt

    def initialize(self):
        if self.inputs.count() == 0:
            self._initialize_inputs()

        if self.outputs.count() == 0:
            self._initialize_outputs()

    def _initialize_inputs(self):
        for input in self.task_run.inputs.all():
            TaskRunAttemptInput.objects.create(
                task_run_attempt=self,
                task_run_input=input,
                data_object=input.data_object)

    def _initialize_outputs(self):
        for output in self.task_run.outputs.all():
            TaskRunAttemptOutput.objects.create(
                task_run_attempt=self,
                task_run_output=output)

    def get_working_dir(self):
        return os.path.join(get_setting('FILE_ROOT_FOR_WORKER'),
                            'runtime_volumes',
                            self.id.hex,
                            'work')

    def get_log_dir(self):
        return os.path.join(get_setting('FILE_ROOT_FOR_WORKER'),
                            'runtime_volumes',
                            self.id.hex,
                            'logs')

    def get_worker_log_file(self):
        return os.path.join(self.get_log_dir(), 'worker.log')

    def get_stdout_log_file(self):
        return os.path.join(self.get_log_dir(), 'stdout.log')

    def get_stderr_log_file(self):
        return os.path.join(self.get_log_dir(), 'stderr.log')

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

    def push_outputs(self):
        for output in self.outputs.all():
            output.push()
        self.task_run.step_run.get_run_request().create_ready_tasks()

    def delete_worker(self):
        task_manager = TaskManagerFactory.get_task_manager()
        task_manager.delete_worker_by_task_run_attempt(self)

    def _post_save(self):
        if self.status == 'Finished':
            self.push_outputs()
            if get_setting('WORKER_CLEANUP') == 'True':
                self.delete_worker()
        self.task_run.update_status()

@receiver(models.signals.post_save, sender=TaskRunAttempt)
def _post_save_task_run_attempt_signal_receiver(sender, instance, **kwargs):
    instance._post_save()


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
    def source(self):
        return self.task_run_output.source

    def push(self):
        if self.data_object is not None:
            self.task_run_output.push(self.data_object)


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

    def _post_save(self):
        # Create a blank file_data_object on save.
        # The client will upload the file to this object.
        if self.file_data_object is None:
            self.file_data_object = FileDataObject.objects.create(source_type='log')
            self.save()

@receiver(models.signals.post_save, sender=TaskRunAttemptLogFile)
def _post_save_task_run_attempt_log_file_signal_receiver(sender, instance, **kwargs):
    instance._post_save()


class TaskRunAttemptError(BaseModel):

    task_run_attempt = models.ForeignKey(
        'TaskRunAttempt',
        related_name='errors',
        on_delete=models.CASCADE)
    message = models.CharField(max_length=255)
    detail = models.TextField(null=True, blank=True)
