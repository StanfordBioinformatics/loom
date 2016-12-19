from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from .base import BaseModel
from .input_output_nodes import InputOutputNode
from .runs import Run

class RunRequest(BaseModel):

    """RunRequest contains information submitted by a user
    to create a run, in particular the inputs and the template
    to be used. It also points to the corresponding run.
    """

    datetime_created = models.DateTimeField(default=timezone.now,
                                            editable=False)
    template = models.ForeignKey('Template', on_delete=models.PROTECT)
    run = models.OneToOneField('Run',
                               null=True,
                               related_name='run_request',
                               on_delete=models.PROTECT)

    @property
    def uuid(self):
        if not self.run:
            return None
        else:
            return self.run.uuid

    def initialize(self):
        self.run = Run.create_from_template(self.template)
        self.save()
        self._connect_channels()

    def _connect_channels(self):
        # This step is separate from self.run.initialize because
        # channels have to be connected from the outside in, since data 
        # is applied to run_request inputs first.
        for run_request_input in self.inputs.all():
            run_input = self.run.get_input(run_request_input.channel)
            run_input.connect(run_request_input)
        self.run.connect_channels()


class RunRequestInput(InputOutputNode):

    run_request = models.ForeignKey(
        'RunRequest',
        related_name='inputs',
        on_delete=models.CASCADE)


"""
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

"""
