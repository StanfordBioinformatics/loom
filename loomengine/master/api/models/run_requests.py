from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
import uuid

from .base import BaseModel, BasePolymorphicModel
from .channels import InputOutputNode
from .data_objects import DataObject
from .workflow_runs import AbstractWorkflowRun, StepRun, WorkflowRun
from .workflows import Workflow
#from api import get_setting


class RunRequest(BaseModel):

    NAME_FIELD = 'template__name'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    datetime_created = models.DateTimeField(default=timezone.now,
                                            editable=False)
    template = models.ForeignKey('AbstractWorkflow', on_delete=models.PROTECT)
    run = models.OneToOneField('AbstractWorkflowRun',
                               null=True,
                               on_delete=models.PROTECT)
    is_running = models.BooleanField(default=True)
    is_stopping = models.BooleanField(default=False)
    is_hard_stop = models.BooleanField(default=False)
    is_failed = models.BooleanField(default=False)
    is_canceled = models.BooleanField(default=False)
    is_completed = models.BooleanField(default=False)

    def name(self):
        return self.template.name

    def post_create(self):
        self._initialize_run()
        self._validate()
        self._initialize_outputs()
        self._initialize_channels()
        self.initial_push()

    def _initialize_run(self):
        if not self.run:
            self.run = AbstractWorkflowRun.create_from_template(self.template)
            self.save()

    def _initialize_outputs(self):
        for run_request_output in self.run.outputs.all():
            RunRequestOutput.objects.create(
                run_request=self,
                channel=run_request_output.channel)

    def _initialize_channels(self):
        for run_request_input in self.inputs.all():
            run_input = self.run.get_input(run_request_input.channel)
            if not run_input.sender == run_request_input:
                run_input.sender = run_request_input
                run_input.save()
        for run_request_output in self.outputs.all():
            run_output = self.run.get_output(run_request_output.channel)
            if not run_request_output.sender == run_output:
               run_request_output.sender = run_output
               run_request_output.save()

    def initial_push(self):
        for input in self.inputs.all():
            input.push_all()
        self.run.initial_push()

    def _validate(self):
        # Verify that there is 1 WorkflowInput for each RunRequestInput
        # and that their channel names match
        workflow_inputs = [input.channel for input
                           in self.template.inputs.all()]
        for input in self.inputs.all():
            if not input.channel in workflow_inputs:
                raise ValidationError(
                    'Run request is invalid. Input channel "%s" does not '\
                    'correspond to any channel in the workflow'
                    % input.channel)
            workflow_inputs.remove(input.channel)
        if len(workflow_inputs) > 0:
            raise ValidationError(
                'Missing input for channel(s) "%s"' %
                ', '.join([channel for channel in workflow_inputs]))

    @classmethod
    def cancel_all(cls, is_hard_stop=None):
        for run_request in cls.objects.filter(running=True):
            run_request.cancel()

    def cancel(self, is_hard_stop=None):
        self.cancel_requests.add(
            CancelRequest.create(
                {'is_hard_stop': is_hard_stop}
            ))

    def fail(self, is_hard_stop=None):
        self.failure_notices.add(
            FailureNotice.create(
                {'is_hard_stop': is_hard_stop}
            ))

    def restart(self):
        self.restart_requests.add(
            RestartRequest.create({})
        )

    @classmethod
    def refresh_status_for_all(cls):
        for run_request in cls.objects.filter(is_running=True):
            run_request.refresh_status()

    def refresh_status(self):
        """ Arbitrate between 0 or more FailureNotices, CancelRequests, 
        and RestartRequests
        """
        # TODO
        pass


class RunRequestInput(InputOutputNode):

    run_request = models.ForeignKey(
        'RunRequest',
        related_name='inputs',
        on_delete=models.CASCADE)

    def value(self):
        # TODO - handle indices
        if self.indexed_data_objects.count() == 0:
            return None
        return self.indexed_data_objects.first()\
                                        .data_object.get_display_value()

    def get_type(self):
        return self.run_request.run.get_input(self.channel).type


class RunRequestOutput(InputOutputNode):
    
    run_request = models.ForeignKey(
        'RunRequest',
        related_name='outputs',
        on_delete=models.CASCADE)    


class CancelRequest(BaseModel):

    run_request = models.ForeignKey('RunRequest',
                                    related_name='cancel_requests',
                                    on_delete=models.CASCADE)
    is_hard_stop = models.BooleanField()

    @classmethod
    def before_create_or_update(cls, data):
        if data.get('is_hard_stop') is None:
            data.update({
                'is_hard_stop': get_setting('HARD_STOP_ON_CANCEL')
            })

    def after_create_or_update(self, data):
        self.run_request.refresh_status()


class RestartRequest(BaseModel):

    run_request = models.ForeignKey('RunRequest',
                                    related_name='restart_requests',
                                    on_delete=models.CASCADE)
    
    def after_create_or_update(self, data):
        self.run_request.refresh_status()


class FailureNotice(BaseModel):

    run_request = models.ForeignKey('RunRequest',
                                    related_name='failure_notices',
                                    on_delete=models.CASCADE)
    is_hard_stop = models.BooleanField()

    @classmethod
    def before_create_or_update(cls, data):
        if data.get('is_hard_stop') is None:
            data.update({
                'is_hard_stop': get_setting('HARD_STOP_ON_FAIL')
            })

    def after_create_or_update(self, data):
        self.run_request.refresh_status()
