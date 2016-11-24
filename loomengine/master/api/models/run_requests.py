from django.core.exceptions import ValidationError
from django.db import models
from django.dispatch import receiver
from django.utils import timezone
import uuid

from .base import BaseModel
from .input_output_nodes import InputOutputNode
from .data_objects import DataObject
from .runs import Run
from .templates import Template
from api import get_setting


class RunRequest(BaseModel):

    NAME_FIELD = 'template__name'

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    datetime_created = models.DateTimeField(default=timezone.now,
                                            editable=False)
    datetime_finished = models.DateTimeField(null=True)
    template = models.ForeignKey('Template', on_delete=models.PROTECT)
    run = models.OneToOneField('Run',
                               null=True,
                               related_name='run_request',
                               on_delete=models.PROTECT)
#    is_running = models.BooleanField(default=True)
#    is_stopping = models.BooleanField(default=False)
#    is_hard_stop = models.BooleanField(default=False)
#    is_failed = models.BooleanField(default=False)
#    is_canceled = models.BooleanField(default=False)
#    is_completed = models.BooleanField(default=False)

    def initialize(self):
        self._initialize_run()
        self._validate()
        self._initialize_outputs()
        self.connect_channels()

    def _initialize_run(self):
        self.run = Run.create_from_template(self.template)
        self.save()

    def _initialize_outputs(self):
        for run_request_output in self.run.outputs.all():
            RunRequestOutput.objects.create(
                run_request=self,
                channel=run_request_output.channel)

    def connect_channels(self):
        # This step is separate from self.run.initialize because
        # channels have to be connected from the outside in, since data is applied
        # to run_request inputs first.
        for run_request_input in self.inputs.all():
            run_input = self.run.get_input(run_request_input.channel)
            run_input.connect(run_request_input)
        for run_request_output in self.outputs.all():
            run_output = self.run.get_output(run_request_output.channel)
            run_output.connect(run_request_output)
        self.run.connect_channels()

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

    def create_ready_tasks(self, do_start=True):
        self.run.create_ready_tasks(do_start=do_start)


class RunRequestInput(InputOutputNode):

    run_request = models.ForeignKey(
        'RunRequest',
        related_name='inputs',
        on_delete=models.CASCADE)


class RunRequestOutput(InputOutputNode):

    run_request = models.ForeignKey(
        'RunRequest',
        related_name='outputs',
        on_delete=models.CASCADE)    
