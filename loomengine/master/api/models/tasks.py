from django.db import models
from django.dispatch import receiver
from django.core.exceptions import ObjectDoesNotExist
from django.dispatch import receiver
from django.utils import timezone
import os
import jsonfield

from api import tasks
from api.models import uuidstr
from .base import BaseModel, render_from_template
from api.models.data_objects import DataObject, FileDataObject
# from api.models.workflows import Step, RequestedResourceSet
from api import get_setting
#from api.task_manager.factory import TaskManagerFactory


class Task(BaseModel):

    """A Task is a Step executed on a particular set of inputs.
    For non-parallel steps, each StepRun will have one task. For parallel,
    each StepRun will have one task for each set of inputs.
    """

    uuid = models.CharField(default=uuidstr, editable=False,
                            unique=True, max_length=255)
    datetime_created = models.DateTimeField(default=timezone.now,
                                            editable=False)
    interpreter = models.CharField(max_length=255, default='/bin/bash')
    interpreter_options = models.CharField(max_length=1024, default='-euo pipefail')
    command = models.TextField()
    rendered_command = models.TextField()

    step_run = models.ForeignKey('StepRun',
                                 related_name='tasks',
                                 on_delete=models.CASCADE,
                                 null=True) # null for testing only

    selected_task_attempt = models.OneToOneField('TaskAttempt',
                                               related_name='task_as_selected',
                                               on_delete=models.CASCADE,
                                               null=True)

    # While status_is_running, Loom will continue trying to complete the task
    status_is_running = models.BooleanField(default=True)
    status_is_killed = models.BooleanField(default=False)
    status_is_finished = models.BooleanField(default=False)

    @property
    def status_message(self):
        try:
            return self.selected_task_attempt.status_message
        except AttributeError:
            # No active TaskAttempt. Return human-readable status
            # based on status flags
            if self.task_attempts.count() == 0:
                return 'Initializing'
            else:
                # TaskAttempts exist but none is active. Why?
                return 'Unknown'

    @property
    def status_message_detail(self):
        try:
            return self.selected_task_attempt.status_message_detail
        except AttributeError:
            # No active task Attempt
            return ''

    @property
    def status_is_failed(self):
        try:
            return self.selected_task_attempt.status_is_failed
        except AttributeError:
            return False

    @property
    def datetime_finished(self):
        try:
            return self.selected_task_attempt.datetime_finished
        except AttributeError:
            return None

    @property
    def attempt_number(self):
        return self.task_attempts.count()

    def fail(self):
        if not self.step_run.status_is_failed:
            self.step_run.fail()
    
    def finish(self):
        if self.status_is_finished:
            return
        self.status_is_finished = True
        self.save()
        for output in self.outputs.all():
            output.pull_data_object()
            output.push_data_object()
        self.step_run.update_status()
        self.status_is_running = False
        self.save()
        for task_attempt in self.task_attempts.all():
            task_attempt.cleanup()

    def kill(self):
        self.status_is_running = False
        self.status_is_killed = True
        self.save()
        for task_attempt in self.task_attempts.all():
            task_attempt.kill()
            task_attempt.cleanup()

    def has_been_run(self):
        return self.attempt_number == 0
    
    @classmethod
    def create_from_input_set(cls, input_set, step_run):
        task = Task.objects.create(
            step_run=step_run,
            command=step_run.command,
        )
        for input in input_set:
            TaskInput.objects.create(
                task=task,
                channel=input.channel,
                type=input.type,
                data_object = input.data_object)
        for step_run_output in step_run.outputs.all():
            task_output = TaskOutput.objects.create(
                channel = step_run_output.channel,
                type=step_run_output.type,
                task=task,
                source=step_run_output.source)

        TaskResourceSet.objects.create(
            task=task,
            memory=step_run.template.resources.get('memory'),
            disk_size=step_run.template.resources.get('disk_size'),
            cores=step_run.template.resources.get('cores')
        )
        TaskEnvironment.objects.create(
            task=task,
            docker_image = step_run.template.environment.get('docker_image'),
        )
        task.rendered_command = task.render_command()
        task.save()

        return task

    def create_and_activate_attempt(self):
        task_attempt = TaskAttempt.objects.create(task=self)
        task_attempt.initialize()

        self.selected_task_attempt = task_attempt
        self.save()

        task_attempt.add_timepoint('TaskAttempt created')
        
        return task_attempt

    def get_input_context(self):
        context = {}
        for input in self.inputs.all():
            context[input.channel] = input.data_object\
                                            .substitution_value
        return context

    def get_output_context(self):
        context = {}
        for output in self.outputs.all():
            # This returns a value only for Files, where the filename
            # is known beforehand and may be used in the command.
            # For other types, nothing is added to the context.
            if output.source.get('filename'):
                context[output.channel] = output.source.get('filename')
        return context

    def get_full_context(self):
        context = self.get_input_context()
        context.update(self.get_output_context())
        return context

    def render_command(self):
        return render_from_template(
            self.command,
            self.get_full_context())

    def get_output(self, channel):
        return self.outputs.get(channel=channel)


class TaskInput(BaseModel):

    task = models.ForeignKey('Task',
                             related_name='inputs',
                             on_delete=models.CASCADE)
    data_object = models.ForeignKey('DataObject', on_delete=models.PROTECT)
    channel = models.CharField(max_length=255)
    type = models.CharField(max_length = 255,
                            choices=DataObject.TYPE_CHOICES)


class TaskOutput(BaseModel):

    task = models.ForeignKey('Task',
                             related_name='outputs',
                             on_delete=models.CASCADE)
    channel = models.CharField(max_length=255)
    type = models.CharField(max_length = 255,
                            choices=DataObject.TYPE_CHOICES)
    source = jsonfield.JSONField(null=True)
    data_object = models.ForeignKey('DataObject', on_delete=models.PROTECT, null=True)

    def pull_data_object(self):
        attempt_output = self.task.selected_task_attempt.get_output(self.channel)
        self.data_object = attempt_output.data_object
        self.save()

    def push_data_object(self):
        step_run_output = self.task.step_run.get_output(self.channel)
        if not step_run_output.has_scalar():
            step_run_output.add_data_object([], self.data_object)


class TaskResourceSet(BaseModel):
    task = models.OneToOneField('Task',
                                on_delete=models.CASCADE,
                                related_name='resources')
    memory = models.CharField(max_length=255, null=True)
    disk_size = models.CharField(max_length=255, null=True)
    cores = models.CharField(max_length=255, null=True)


class TaskEnvironment(BaseModel):

    task = models.OneToOneField(
        'Task',
        on_delete=models.CASCADE,
        related_name='environment')
    docker_image = models.CharField(max_length=255)


class TaskAttempt(BaseModel):

    uuid = models.CharField(default=uuidstr, editable=False,
                            unique=True, max_length=255)
    datetime_created = models.DateTimeField(default=timezone.now,
                                            editable=False)
    datetime_finished = models.DateTimeField(null=True)
    task = models.ForeignKey('Task',
                             related_name='task_attempts',
                             on_delete=models.CASCADE)
    # container_id = models.CharField(max_length=255, null=True)
    last_heartbeat = models.DateTimeField(auto_now=True)
    status_is_failed = models.BooleanField(default=False)
    status_is_finished = models.BooleanField(default=False)
    status_is_killed = models.BooleanField(default=False)
    status_is_running = models.BooleanField(default=True)
    status_is_cleaned_up = models.BooleanField(default=False)
    status_message = models.CharField(
        max_length=255,
        default='Starting')
    status_message_detail = models.CharField(
        max_length=255,
        default='')

    @property
    def is_active(self):
        try:
            self.task_as_selected
        except ObjectDoesNotExist:
            return False
        return True
        
    
    @property
    def interpreter(self):
        return self.task.interpreter

    def interpreter_options(self):
        return self.task.interpreter_options

    @property
    def rendered_command(self):
        return self.task.rendered_command

    @property
    def inputs(self):
        return self.task.inputs

    @property
    def resources(self):
        return self.task.resources

    @property
    def environment(self):
        return self.task.environment

    def get_output(self, channel):
        return self.outputs.get(channel=channel)

    def set_datetime_finished(self):
        if not self.datetime_finished:
            self.datetime_finished = timezone.now()
            self.save()

    def _post_save(self):
        if self.status_is_failed:
            self.set_datetime_finished()
            try:
                self.task_as_selected.fail()
            except ObjectDoesNotExist:
                # This attempt is no longer active
                # and will be ignored.
                pass
        elif self.status_is_finished:
            self.set_datetime_finished()
            try:
                self.task_as_selected.finish()
            except ObjectDoesNotExist:
                # This attempt is no longer active
                # and will be ignored.
                pass

    def add_error(self, message, detail):
        error = TaskAttemptError.objects.create(
            message=message, detail=detail, task_attempt=self)
        error.save()

    def add_timepoint(self, message):
        timepoint = TaskAttemptTimepoint.objects.create(
            message=message, task_attempt=self)
        timepoint.save()
        
    @classmethod
    def create_from_task(cls, task):
        task_attempt = cls.objects.create(task=task)
        task_attempt.initialize()
        return task_attempt

    def initialize(self):
        if self.inputs.count() == 0:
            self._initialize_inputs()

        if self.outputs.count() == 0:
            self._initialize_outputs()

    def _initialize_outputs(self):
        for output in self.task.outputs.all():
            TaskAttemptOutput.objects.create(
                task_attempt=self,
                type=output.type,
                channel=output.channel,
                source=output.source)

    def get_working_dir(self):
        return os.path.join(get_setting('FILE_ROOT_FOR_WORKER'),
                            'runtime_volumes',
                            str(self.uuid),
                            'work')

    def get_log_dir(self):
        return os.path.join(get_setting('FILE_ROOT_FOR_WORKER'),
                            'runtime_volumes',
                            str(self.uuid),
                            'logs')

    def get_worker_log_file(self):
        return os.path.join(self.get_log_dir(), 'worker.log')

    def get_stdout_log_file(self):
        return os.path.join(self.get_log_dir(), 'stdout.log')

    def get_stderr_log_file(self):
        return os.path.join(self.get_log_dir(), 'stderr.log')

    def kill(self):
        self.status_is_killed = True
        self.status_is_running = False
        self.save()
        self.add_timepoint('TaskAttempt killed')

    def cleanup(self):
        if self.status_is_cleaned_up:
            return
        tasks.cleanup_task_attempt(self.uuid)
        self.status_is_cleaned_up = True
        self.save()
        
#    def get_provenance_data(self, files=None, tasks=None, edges=None):
#        if files is None:
#            files = set()
#        if tasks is None:
#            tasks = set()
#        if edges is None:
#            edges = set()

#        tasks.add(self)

#        for input in self.task.inputs.all():
#            data = input.data_object
#            if data.type == 'file':
#                files.add(data)
#                edges.add((data.id.hex, self.id.hex))
#                data.get_provenance_data(files, tasks, edges)
#            else:
                # TODO - nonfile data types
#                pass

#        return files, tasks, edges

@receiver(models.signals.post_save, sender=TaskAttempt)
def _post_save_task_attempt_signal_receiver(sender, instance, **kwargs):
    instance._post_save()


class TaskAttemptOutput(BaseModel):

    # All info here is saved in the TaskOutput,
    # except for the data_object. If multiple
    # attempts are run, each may have a different
    # data_object.

    task_attempt = models.ForeignKey(
        'TaskAttempt',
        related_name='outputs',
        on_delete=models.CASCADE)
    data_object = models.OneToOneField(
        'DataObject',
        null=True,
        related_name='task_attempt_output',
        on_delete=models.PROTECT)
    channel = models.CharField(max_length=255)
    type = models.CharField(max_length = 255,
                            choices=DataObject.TYPE_CHOICES)
    source = jsonfield.JSONField(null=True)


class TaskAttemptLogFile(BaseModel):

    task_attempt = models.ForeignKey(
        'TaskAttempt',
        related_name='log_files',
        on_delete=models.CASCADE)
    log_name = models.CharField(max_length=255)
    file = models.OneToOneField(
        'DataObject',
        null=True,
        related_name='task_attempt_log_file',
        on_delete=models.PROTECT)

    def _post_save(self):
        # Create a blank file_data_object on save.
        # The client will upload the file to this object.
        if self.file is None:
            self.file = FileDataObject.objects.create(
                source_type='log', type='file', filename=self.log_name)
            self.file.initialize()
            self.save()

@receiver(models.signals.post_save, sender=TaskAttemptLogFile)
def _post_save_task_attempt_log_file_signal_receiver(sender, instance, **kwargs):
    instance._post_save()


class TaskAttemptError(BaseModel):

    task_attempt = models.ForeignKey(
        'TaskAttempt',
        related_name='errors',
        on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=timezone.now,
                                     editable=False)
    message = models.CharField(max_length=255)
    detail = models.TextField(null=True, blank=True)

class TaskAttemptTimepoint(BaseModel):
    task_attempt = models.ForeignKey(
        'TaskAttempt',
        related_name='timepoints',
        on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=timezone.now,
                                     editable=False)
    message = models.CharField(max_length=255)
