from django.core.exceptions import ValidationError
from django.db import models
from django.dispatch import receiver
from django.utils import timezone
import uuid

from .base import BaseModel, BasePolymorphicModel
from .channels import InputOutputNode
from .data_objects import DataObject
from .signals import post_save_children
from .workflow_runs import AbstractWorkflowRun, StepRun, WorkflowRun
from .workflows import Workflow
from api import get_setting


class RunRequest(BaseModel):

    NAME_FIELD = 'template__name'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    datetime_created = models.DateTimeField(default=timezone.now,
                                            editable=False)
    template = models.ForeignKey('AbstractWorkflow', on_delete=models.PROTECT)
    run = models.OneToOneField('AbstractWorkflowRun',
                               null=True,
                               related_name='run_request',
                               on_delete=models.PROTECT)
    is_running = models.BooleanField(default=True)
    is_stopping = models.BooleanField(default=False)
    is_hard_stop = models.BooleanField(default=False)
    is_failed = models.BooleanField(default=False)
    is_canceled = models.BooleanField(default=False)
    is_completed = models.BooleanField(default=False)

    @property
    def status(self):
        return self.run.status
    
    def name(self):
        return self.template.name

    def _post_save_children(self):
        self._idempotent_initialize()

    def _idempotent_initialize(self):
        self._initialize_run()
        self._validate()
        self._initialize_outputs()
        self._initialize_channels()
        self.push_inputs()

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

    def push_inputs(self):
        for input in self.inputs.all():
            input.push()
        self.run.push_fixed_inputs()

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

@receiver(post_save_children, sender=RunRequest)
def _post_save_children_run_request_signal_receiver(sender, instance, **kwargs):
    instance._post_save_children()


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
