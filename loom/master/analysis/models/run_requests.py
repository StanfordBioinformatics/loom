from django.core.exceptions import ValidationError
from django.db import transaction

from analysis import get_setting
from universalmodels import fields
from analysis.models.base import AnalysisAppInstanceModel
from analysis.models.channels import Channel, InputOutputNode
from analysis.models.data_objects import DataObject
from analysis.models.workflow_runs import AbstractWorkflowRun
from analysis.models.workflows import Workflow


class RunRequest(AnalysisAppInstanceModel):

    template = fields.ForeignKey('AbstractWorkflow')
    inputs = fields.OneToManyField('RunRequestInput', related_name='run_request')
    outputs = fields.OneToManyField('RunRequestOutput', related_name='run_request')
    run = fields.OneToOneField('AbstractWorkflowRun', null=True)

    cancel_requests = fields.OneToManyField('CancelRequest', related_name='run_request')
    restart_requests = fields.OneToManyField('RestartRequest', related_name='run_request')
    failure_notices = fields.OneToManyField('FailureNotice', related_name='run_request')

    is_running = fields.BooleanField(default=True)
    is_stopping = fields.BooleanField(default=False)
    is_hard_stop = fields.BooleanField(default=False)
    is_failed = fields.BooleanField(default=False)
    is_canceled = fields.BooleanField(default=False)
    is_completed = fields.BooleanField(default=False)

    def after_create_or_update(self, data):
        self._initialize_run()
        self._initialize_outputs()
        self._initialize_channels()
        if not get_setting('DISABLE_AUTO_PUSH'):
            self._initial_push()
        self._validate_run_request()
        self.is_initialized = True

    def _initialize_run(self):
        if not self.run:
            # Workaround--not using the "update" method here to avoid infinite recursion
            self.run = AbstractWorkflowRun.create({'template': self.template})
            self.save()

    def _initialize_outputs(self):
        for workflow_output in self.template.outputs.all():
            if not self.outputs.filter(channel=workflow_output.channel):
                # Workaround--not using the "update" method here to avoid infinite recursion
                self.outputs.add(
                    RunRequestOutput.create({
                        'channel': workflow_output.channel
                    })
                )

    def _initialize_channels(self):
        for source in self._get_sources():
            destination = self._get_destination(source.channel)
            if not source.has_destination(destination):
                channel = Channel.create_from_sender(source, source.channel)
                channel.add_receiver(destination)

    def _initial_push(self):
        for input in self.inputs.all():
            input.initial_push()
        self.run.initial_push()
        
    def _validate_run_request(self):
        # Verify that there is 1 WorkflowInput for each RunRequestInput and that their channel names match
        workflow_inputs = set([input.channel for input in self.template.inputs.all()])
        for input in self.inputs.all():
            if not input.channel in workflow_inputs:
                raise ValidationError('Run request is invalid. Input channel "%s" does not correspond to any channel in the workflow' % input.channel)
            workflow_inputs.remove(input.channel)
        if len(workflow_inputs) > 0:
            raise ValidationError('Missing input for channel(s) "%s"' %
                                  ', '.join([channel for channel in workflow_inputs]))

        # Verify that there is 1 WorkflowOutput for each RunRequestOutput and that their channel names match
        workflow_outputs = set([output.channel for output in self.template.outputs.all()])
        for output in self.outputs.all():
            if not output.channel in workflow_outputs:
                raise ValidationError('Run request is invalid. Output channel "%s" does not correspond to any channel in the workflow' % output.channel)
            workflow_outputs.remove(output.channel)
        if len(workflow_outputs) > 0:
            raise ValidationError('Missing output for channel(s) "%s"' %
                                  ', '.join([channel for channel in workflow_outputs]))

    def _get_sources(self):
        sources = [source for source in self.inputs.all()]
        sources.extend([source for source in self.run.downcast().outputs.all()])
        return sources

    def _get_destination(self, channel):
        destinations = [dest for dest in self.run.downcast().inputs.filter(channel=channel)]
        destinations.extend([dest for dest in self.outputs.filter(channel=channel)])
        assert len(destinations) == 1
        return destinations[0]

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
        for run_request in cls.objects.filter(running=True):
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

    channel = fields.CharField(max_length=255)
    value = fields.CharField(max_length=255)

    def initial_push(self):
        data_object = self._get_data_object()
        self.to_channel.push(data_object)
        self.to_channel.close()

    def _get_data_object(self):
        return DataObject.get_by_value(self.value, self.get_type())

    def get_type(self):
        return self.run_request.run.get_input(self.channel).type


class RunRequestOutput(InputOutputNode):

    channel = fields.CharField(max_length=255)
    data_object = fields.ForeignKey('DataObject', null=True)

    def push(self, data_object):
        self.update(
            {'data_object': self.from_channel.pop()}
        )
        self.run_request.push()

    def is_completed(self):
        if self.data_object is not None:
            return self.data_object.is_ready()
        else:
            return False


class CancelRequest(AnalysisAppInstanceModel):

    is_hard_stop = fields.BooleanField()

    @classmethod
    def before_create_or_update(cls, data):
        if data.get('is_hard_stop') is None:
            data.update({
                'is_hard_stop': get_setting('HARD_STOP_ON_CANCEL')
            })

    def after_create_or_update(self, data):
        self.run_request.refresh_status()


class RestartRequest(AnalysisAppInstanceModel):

    def after_create_or_update(self, data):
        self.run_request.refresh_status()


class FailureNotice(AnalysisAppInstanceModel):

    is_hard_stop = fields.BooleanField()

    @classmethod
    def before_create_or_update(cls, data):
        if data.get('is_hard_stop') is None:
            data.update({
                'is_hard_stop': get_setting('HARD_STOP_ON_FAIL')
            })

    def after_create_or_update(self, data):
        self.run_request.refresh_status()
