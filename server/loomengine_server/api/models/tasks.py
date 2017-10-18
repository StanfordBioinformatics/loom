from django.db import models
from django.utils import timezone
import jsonfield

from . import render_from_template, render_string_or_list, ArrayInputContext
from .base import BaseModel
from .data_channels import DataChannel
from api import get_setting
from api import async
from api.exceptions import ConcurrentModificationError
from api.models import uuidstr
from api.models.task_attempts import TaskAttempt
from api.models import validators


class TaskAlreadyExistsException(Exception):
    pass


class Task(BaseModel):
    """A Task is a Step executed on a particular set of inputs.
    For non-parallel steps, each Run will have one task. For parallel,
    each Run will have one task for each set of inputs.
    """
    uuid = models.CharField(default=uuidstr, editable=False,
                            unique=True, max_length=255)
    interpreter = models.CharField(max_length=1024)
    raw_command = models.TextField()
    command = models.TextField(blank=True)
    environment = jsonfield.JSONField()
    resources = jsonfield.JSONField(blank=True)
    run = models.ForeignKey('Run',
                            related_name='tasks',
                            on_delete=models.CASCADE,
                            null=True, # null for testing only
                            blank=True)
    task_attempt = models.OneToOneField('TaskAttempt',
                                        related_name='active_task',
                                        on_delete=models.CASCADE,
                                        null=True,
                                        blank=True)
    analysis_failure_count = models.IntegerField(default=0)
    system_failure_count = models.IntegerField(default=0)
    data_path = jsonfield.JSONField(
        validators=[validators.validate_data_path],
        blank=True)
    datetime_created = models.DateTimeField(default=timezone.now,
                                            editable=False)
    datetime_finished = models.DateTimeField(null=True, blank=True)
    status_is_finished = models.BooleanField(default=False)
    status_is_failed = models.BooleanField(default=False)
    status_is_killed = models.BooleanField(default=False)
    status_is_running = models.BooleanField(default=False)
    status_is_waiting = models.BooleanField(default=True)

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
        elif self.status_is_waiting:
            return 'Waiting'
        else:
            return 'Unknown'

    def is_unresponsive(self):
        heartbeat = int(get_setting('TASKRUNNER_HEARTBEAT_INTERVAL_SECONDS'))
        timeout = int(get_setting('TASKRUNNER_HEARTBEAT_TIMEOUT_SECONDS'))
        try:
            last_heartbeat = self.task_attempt.last_heartbeat
        except AttributeError:
            # No TaskAttempt selected
            last_heartbeat = self.datetime_created
        return (timezone.now() - last_heartbeat).total_seconds() > timeout

    def _process_error(self, detail, max_retries,
                       failure_count_attribute, failure_text,
                       exponential_delay=False):
        if self.has_terminal_status():
            return
        failure_count = int(getattr(self, failure_count_attribute)) + 1
        if failure_count <= max_retries:
            self.setattrs_and_save_with_retries(
                {failure_count_attribute: failure_count})
            if not detail:
                detail = 'Restarting task after %s (retry %s/%s)'\
                         %(failure_text.lower(), failure_count, max_retries)
            self.add_event(failure_text, detail=detail, is_error=True)
            if exponential_delay:
                delay = 2**failure_count
            else:
                delay = 0
            async.run_task(self.uuid, delay=delay)
            return
        else:
            if not detail:
                detail='%s. Already used all %s retries' \
                        % (failure_text, max_retries)
            self.setattrs_and_save_with_retries(
                {
                    failure_count_attribute: failure_count,
                    'status_is_failed': True,
                    'status_is_running': False,
                    'status_is_waiting': False
                })
            self.add_event(
                'Retries exceeded for %s' % failure_text.lower(),
                detail=detail,
                is_error=True)
            self._kill_children(detail=detail)
            self.run.fail(detail='Task %s failed' % self.uuid)
    
    def system_error(self, detail=''):
        self._process_error(
            detail,
            get_setting('MAXIMUM_RETRIES_FOR_SYSTEM_FAILURE'),
            'system_failure_count',
            'System error',
            exponential_delay=True,
        )

    def analysis_error(self, detail=''):
        self._process_error(
            detail,
            get_setting('MAXIMUM_RETRIES_FOR_ANALYSIS_FAILURE'),
            'analysis_failure_count',
            'Analysis error')
        raise Exception(detail)

    def has_terminal_status(self):
        return self.status_is_finished \
            or self.status_is_failed \
            or self.status_is_killed

    def finish(self):
        if self.has_terminal_status():
            return
        self.setattrs_and_save_with_retries(
            { 'datetime_finished': timezone.now(),
              'status_is_finished': True,
              'status_is_running': False,
              'status_is_waiting': False,
            })
        if self.run.are_tasks_finished():
            self.run.finish()
        for output in self.outputs.all():
            output.push_data(self.data_path)
        for task_attempt in self.all_task_attempts.all():
            task_attempt.cleanup()

    def kill(self, detail=''):
        if self.has_terminal_status():
            return
        self.setattrs_and_save_with_retries({
            'status_is_waiting': False,
            'status_is_running': False,
            'status_is_killed': True
        })
        self.add_event('Task was killed', detail=detail, is_error=True)
        self._kill_children(detail=detail)

    def _kill_children(self, detail=''):
        for task_attempt in self.all_task_attempts.all():
            async.kill_task_attempt(task_attempt.uuid, detail)

    @classmethod
    def create_from_input_set(cls, input_set, run):
        try:
            if input_set:
                data_path = input_set.data_path
                if run.tasks.filter(data_path=data_path).count() > 0:
                    raise TaskAlreadyExistsException
            else:
                # If run has no inputs, we get an empty input_set.
                # Task will go on the root node.
                data_path = []

            task = Task(
                run=run,
                raw_command=run.command,
                interpreter=run.interpreter,
                environment=run.template.environment,
                resources=run.template.resources,
                data_path=data_path,
            )
            task.full_clean()
            task.save()
            for input_item in input_set:
                task_input =TaskInput(
                    task=task,
                    channel=input_item.channel,
                    as_channel=input_item.as_channel,
                    type=input_item.type,
                    mode=input_item.mode,
                    data_node = input_item.data_node)
                task_input.full_clean()
                task_input.save()
            for run_output in run.outputs.all():
                task_output = TaskOutput(
                    channel=run_output.channel,
                    as_channel=run_output.as_channel,
                    type=run_output.type,
                    task=task,
                    mode=run_output.mode,
                    source=run_output.source,
                    parser=run_output.parser,
                    data_node=run_output.data_node.get_or_create_node(data_path))
                task_output.full_clean()
                task_output.save()
            task = task.setattrs_and_save_with_retries(
                { 'command': task.render_command() })
            run.set_running_status()
            return task
        except Exception as e:
            if not isinstance(e,TaskAlreadyExistsException):
                run.fail(detail='Error creating Task: "%s"' % str(e))
            raise

    def create_and_activate_attempt(self):
        try:
            self._kill_children(
                detail="TaskAttempt errored or timed out and was restarted.")
            task_attempt = TaskAttempt.create_from_task(self)
            self.setattrs_and_save_with_retries({
                'task_attempt': task_attempt,
                'status_is_running': True,
                'status_is_waiting': False})
            return task_attempt
        except Exception as e:
            self.system_error(detail='Error creating TaskAttempt: "%s"' % str(e))
            raise

    def get_input_context(self):
        context = {}
        for input in self.inputs.all():
            if input.as_channel:
                channel = input.as_channel
            else:
                channel = input.channel
            if input.data_node.is_leaf:
                context[channel] = input.data_node\
                                        .substitution_value
            else:
                context[channel] = ArrayInputContext(
                    input.data_node.substitution_value,
                    input.type
                )
        return context

    def get_output_context(self, input_context):
        # This returns a value only for Files, where the filename
        # is known beforehand and may be used in the command.
        # For other types, nothing is added to the context.
        context = {}
        for output in self.outputs.all():
            if output.as_channel:
                channel = output.as_channel
            else:
                channel = output.channel
            if output.source.get('filename'):
                context[channel] = render_string_or_list(
                    output.source.get('filename'), input_context)
        return context
    
    def get_full_context(self):
        context = self.get_input_context()
        context.update(self.get_output_context(context))
        return context

    def render_command(self):
        return render_from_template(
            self.raw_command,
            self.get_full_context())

    def get_output(self, channel):
        return self.outputs.get(channel=channel)

    def add_event(self, event, detail='', is_error=False):
        event = TaskEvent(
            event=event, task=self,
            detail=detail[-1000:], is_error=is_error)
        event.full_clean()
        event.save()


class TaskInput(DataChannel):

    task = models.ForeignKey('Task',
                             related_name='inputs',
                             on_delete=models.CASCADE)
    mode = models.CharField(max_length=255)
    as_channel = models.CharField(max_length=255, null=True, blank=True)


class TaskOutput(DataChannel):

    task = models.ForeignKey('Task',
                             related_name='outputs',
                             on_delete=models.CASCADE)
    mode = models.CharField(max_length=255)
    source = jsonfield.JSONField(blank=True)
    parser = jsonfield.JSONField(
	validators=[validators.OutputParserValidator.validate_output_parser],
        blank=True)
    as_channel = models.CharField(max_length=255, null=True, blank=True)

    def push_data(self, data_path):
        # Copy data from the TaskAttemptOutput to the TaskOutput
        # From there, it is already connected to downstream runs.
        attempt_output = self.task.task_attempt.get_output(self.channel)
        attempt_output.data_node.clone(seed=self.data_node)

        # To trigger new runs we have to push on the root node,
        # but the TaskOutput's data tree may be just a subtree.
        # So we get the root from the run_output.
        run_output = self.task.run.get_output(self.channel)
        data_root = run_output.data_node
        for input in data_root.downstream_run_inputs.all():
            input.run.push(input.channel, data_path)


class TaskEvent(BaseModel):
    task = models.ForeignKey(
        'Task',
        related_name='events',
        on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=timezone.now,
                                     editable=False)
    event = models.CharField(max_length=255)
    detail = models.TextField(blank=True)
    is_error = models.BooleanField(default=False)
