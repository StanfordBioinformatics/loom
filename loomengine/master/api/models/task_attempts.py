from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils import timezone
import jsonfield
import os

from . import render_from_template, render_string_or_list
from .base import BaseModel
from .data_channels import DataChannel
from api import get_setting
from api import async
from api.models import uuidstr
from api.models.data_objects import DataObject, FileResource
from api.models import validators


class TaskAttempt(BaseModel):

    uuid = models.CharField(default=uuidstr, editable=False,
                            unique=True, max_length=255)
    task = models.ForeignKey('Task',
                             related_name='all_task_attempts',
                             on_delete=models.CASCADE)
    interpreter = models.CharField(max_length=1024)
    command = models.TextField()
    environment = jsonfield.JSONField()
    resources = jsonfield.JSONField(blank=True)
    last_heartbeat = models.DateTimeField(auto_now=True)
    datetime_created = models.DateTimeField(default=timezone.now,
                                            editable=False)
    datetime_finished = models.DateTimeField(null=True, blank=True)
    status_is_finished = models.BooleanField(default=False)
    status_is_failed = models.BooleanField(default=False)
    status_is_killed = models.BooleanField(default=False)
    status_is_running = models.BooleanField(default=True)
    status_is_cleaned_up = models.BooleanField(default=False)

    @property
    def status(self):
        if self.status_is_failed:
            return 'Failed'
        elif self.status_is_finished:
            return 'Finished'
        elif self.status_is_killed:
            return 'Killed'
        elif self.status_is_running:
            return 'Running'
        else:
            return 'Unknown'

    def heartbeat(self):
        # Saving with an empty set of attributes will update
        # last_heartbeat since auto_now=True
        self.setattrs_and_save_with_retries({})

    def get_output(self, channel):
        return self.outputs.get(channel=channel)

    def fail(self, detail=''):
        if self.has_terminal_status():
            return
        self.setattrs_and_save_with_retries(
            {'status_is_failed': True,
             'status_is_running': False})
        self.add_event("TaskAttempt failed", detail=detail, is_error=True)
        try:
            self.active_task.fail(
                detail="Child TaskAttempt %s failed" % self.uuid)
        except ObjectDoesNotExist:
            # This attempt is no longer active
            # and will be ignored.
            pass

    def has_terminal_status(self):
        return self.status_is_finished \
            or self.status_is_failed \
            or self.status_is_killed

    def finish(self):
        if self.has_terminal_status():
            return
        self.setattrs_and_save_with_retries({
            'datetime_finished': timezone.now(),
            'status_is_finished': True,
            'status_is_running': False })
        try:
            task = self.active_task
        except ObjectDoesNotExist:
            # This attempt is no longer active
            # and will be ignored.
            return
        task.finish()

    def add_event(self, event, detail='', is_error=False):
        event = TaskAttemptEvent.objects.create(
            event=event, task_attempt=self, detail=detail[-1000:], is_error=is_error)

    @classmethod
    def create_from_task(cls, task):
        task_attempt = cls.objects.create(
            task=task,
            interpreter=task.interpreter,
            command=task.command,
            environment=task.environment,
            resources=task.resources,
        )
        task_attempt.initialize()
        return task_attempt

    def initialize(self):
        if self.inputs.count() == 0:
            self._initialize_inputs()

        if self.outputs.count() == 0:
            self._initialize_outputs()

    def _initialize_inputs(self):
        for input in self.task.inputs.all():
            TaskAttemptInput.objects.create(
                task_attempt=self,
                type=input.type,
                channel=input.channel,
                mode=input.mode,
                data_node=input.data_node.flattened_clone())

    def _initialize_outputs(self):
        for task_output in self.task.outputs.all():
            task_attempt_output = TaskAttemptOutput.objects.create(
                task_attempt=self,
                type=task_output.type,
                channel=task_output.channel,
                mode=task_output.mode,
                source=self._render_output_source(task_output.source),
                parser=task_output.parser
            )

    def _render_output_source(self, task_output_source):
        input_context = self.task.get_input_context()

        stream = task_output_source.get('stream')
        filename = render_from_template(
            task_output_source.get('filename'), input_context)
        filenames = render_string_or_list(
            task_output_source.get('filenames'),
            input_context)
        glob = render_from_template(
            task_output_source.get('glob'), input_context)

        output_source = {}
        if stream:
            output_source['stream'] = stream
        if filename:
            output_source['filename'] = filename
        if filenames:
            output_source['filenames'] = filenames
        if glob:
            output_source['glob'] = glob
        return output_source        

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

    def kill(self, detail):
        if self.has_terminal_status():
            return
        self.setattrs_and_save_with_retries(
            {'status_is_killed': True,
             'status_is_running': False})
        self.add_event('TaskAttempt was killed', detail=detail, is_error=True)
        self.cleanup()

    def cleanup(self):
        if self.status_is_cleaned_up:
            return
        if get_setting('PRESERVE_ALL'):
            self.add_event('Skipped cleanup because PRESERVER_ALL is True',
                           is_error=False)
            return
        if get_setting('PRESERVE_ON_FAILURE') and self.status_is_failed:
            self.add_event('Skipped cleanup because PRESERVER_ON_FAILURE is True',
                           is_error=False)
            return
        async.cleanup_task_attempt(self.uuid)


class TaskAttemptInput(DataChannel):

    task_attempt = models.ForeignKey('TaskAttempt',
                             related_name='inputs',
                             on_delete=models.CASCADE)
    mode = models.CharField(max_length=255)


class TaskAttemptOutput(DataChannel):

    uuid = models.CharField(default=uuidstr, editable=False,
                            unique=True, max_length=255)
    task_attempt = models.ForeignKey(
        'TaskAttempt',
        related_name='outputs',
        on_delete=models.CASCADE)
    mode = models.CharField(max_length=255)
    source = jsonfield.JSONField(blank=True)
    parser = jsonfield.JSONField(
        validators=[validators.OutputParserValidator.validate_output_parser],
        blank=True)


class TaskAttemptLogFile(BaseModel):

    uuid = models.CharField(default=uuidstr, editable=False,
                            unique=True, max_length=255)
    task_attempt = models.ForeignKey(
        'TaskAttempt',
        related_name='log_files',
        on_delete=models.CASCADE)
    log_name = models.CharField(max_length=255)
    data_object = models.OneToOneField(
        'DataObject',
        null=True,
        blank=True,
        related_name='task_attempt_log_file',
        on_delete=models.PROTECT)
    # datetime_created used only for sorting in index view
    datetime_created = models.DateTimeField(
        default=timezone.now, editable=False)


class TaskAttemptEvent(BaseModel):

    task_attempt = models.ForeignKey(
        'TaskAttempt',
        related_name='events',
        on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=timezone.now,
                                     editable=False)
    event = models.CharField(max_length=255)
    detail = models.TextField(blank=True)
    is_error = models.BooleanField(default=False)


class ArrayInputContext(object):
    """This class is used with jinja templates to make the 
    default representation of an array a space-delimited list.
    """

    def __init__(self, items, type):
        if type == 'file':
            self.items = self._rename_duplicates(items)
        else:
            self.items = items

    def _rename_duplicates(self, filenames):

        # Identify filenames that are unique
        seen = set()
        duplicates = set()
        for filename in filenames:
            if filename in seen:
                duplicates.add(filename)
            seen.add(filename)

        new_filenames = []
        filename_counts = {}
        for filename in filenames:
            if filename in duplicates:
                counter = filename_counts.setdefault(filename, 0)
                filename_counts[filename] += 1
                filename = self._add_counter_suffix(filename, counter)
            new_filenames.append(filename)
        return new_filenames

    def _add_counter_suffix(self, filename, count):
        # Add suffix while preserving file extension:
        #   myfile -> myfile.__1__
        #   myfile.txt --> myfile__1__.txt
        #   my.file.txt --> my.file__1__.txt
        parts = filename.split('.')
        assert len(parts) > 0, 'missing filename'
        if len(parts) == 1:
            return parts[0] + '(%s)' % count
        else:
            return '.'.join(parts[0:len(parts)-1]) + '__%s__.' % count + parts[-1]

    def __iter__(self):
        return self.items.iter()

    def __getitem__(self, i):
        return self.items[i]

    def __str__(self):
        return ' '.join([str(item) for item in self.items])
