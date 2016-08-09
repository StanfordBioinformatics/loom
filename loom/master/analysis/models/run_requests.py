from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
import uuid

from .base import BaseModel, BasePolymorphicModel
from .channels import InputOutputNode
from .data_objects import DataObject
from .workflow_runs import AbstractWorkflowRun, StepRun, WorkflowRun
from .workflows import Workflow
from analysis import get_setting


class RunRequest(BaseModel):

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

    def template_id(self):
        return self.template.get_name_and_id()

    def post_create(self):
        self._initialize_run()
        self._initialize_outputs()
        self._validate_run_request()
        self._initialize_channels()
        #if not get_setting('DISABLE_AUTO_PUSH'):
        #    self._initial_push()
        
        self.save()

    def _initialize_run(self):
        if not self.run:
            if self.template.is_step():
                self.run = StepRun.objects.create(template=self.template)
            else:
                self.run = WorkflowRun.objects.create(template=self.template)
            self.run.post_create()

    def _initialize_outputs(self):
        """Since the user doesn't explicitly describe outputs for a run
        request, we create RunRequestOutputs from the WorkflowOutputs.
        """
        for workflow_output in self.template.outputs.all():
            if not self.outputs.filter(channel=workflow_output.channel):
                RunRequestOutput.objects.create(
                    channel=workflow_output.channel,
                    run_request=self)

    def _initialize_channels(self):
        for destination in self._get_destinations():
            source = self._get_source(destination.channel)

            # For a matching source and desination, make sure they are
            # sender/receiver on the same channel
            if not destination.sender:
                destination.sender = source
                destination.save()
            else:
                assert destination.sender == source

    def _initial_push(self):
        for input in self.inputs.all():
            input.initial_push()
        self.run.initial_push()
        
    def _validate_run_request(self):
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

        # Verify that there is 1 WorkflowOutput for each RunRequestOutput and
        # that their channel names match
        workflow_outputs = [output.channel for output
                            in self.template.outputs.all()]
        for output in self.outputs.all():
            if not output.channel in workflow_outputs:
                raise ValidationError(
                    'Run request is invalid. Output channel "%s" does not '\
                    'correspond to any channel in the workflow'
                    % output.channel)
            workflow_outputs.remove(output.channel)
        if len(workflow_outputs) > 0:
            raise ValidationError(
                'Missing output for channel(s) "%s"' %
                ', '.join([channel for channel in workflow_outputs]))

    def _get_destinations(self):
        destinations = [dest for dest in self.run.inputs.all()]
        destinations.extend([dest for dest in self.outputs.all()])
        return destinations

    def _get_source(self, channel):
        sources = [source for source in self.inputs.filter(channel=channel)]
        sources.extend([
            source for source in self.run.outputs.filter(channel=channel)])
        assert len(sources) == 1
        return sources[0]

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
        """ Arbitrate between 0 or more FailureNotices, CancelRequests, and RestartRequests
        """
        # TODO
        pass

    def push(self):
        for output in self.outputs.all():
            if not output.is_completed():
                return
        self.update({'is_completed': True})


class RunRequestInput(InputOutputNode):

    run_request = models.ForeignKey(
        'RunRequest',
        related_name='inputs',
        on_delete=models.CASCADE)

    def value(self):
        if not self.data_object:
            return None
        return self.data_object.get_display_value()

    def initial_push(self):
        data_object = self._get_data_object()
        self.to_channel.push(data_object)
        self.to_channel.close()

    def _get_data_object(self):
        return DataObject.get_by_value(self.value, self.get_type())

    def get_type(self):
        return self.run_request.run.get_input(self.channel).type


class RunRequestOutput(InputOutputNode):
    
    run_request = models.ForeignKey(
        'RunRequest',
        related_name='outputs',
        on_delete=models.CASCADE)

    def value(self):
        if not self.data_object:
            return None
        return self.data_object.get_display_value()

    def push(self, data_object):
        if self.data_object is None:
            self.update(
                {'data_object': self.from_channel.pop()}
            )
            self.run_request.push()

    def is_completed(self):
        if self.data_object is not None:
            return self.data_object.is_ready()
        else:
            return False


class CancelRequest(BaseModel):

    run_request = models.ForeignKey('RunRequest', related_name='cancel_requests', on_delete=models.CASCADE)
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

    run_request = models.ForeignKey('RunRequest', related_name='restart_requests', on_delete=models.CASCADE)
    
    def after_create_or_update(self, data):
        self.run_request.refresh_status()


class FailureNotice(BaseModel):

    run_request = models.ForeignKey('RunRequest', related_name='failure_notices', on_delete=models.CASCADE)
    is_hard_stop = models.BooleanField()

    @classmethod
    def before_create_or_update(cls, data):
        if data.get('is_hard_stop') is None:
            data.update({
                'is_hard_stop': get_setting('HARD_STOP_ON_FAIL')
            })

    def after_create_or_update(self, data):
        self.run_request.refresh_status()
