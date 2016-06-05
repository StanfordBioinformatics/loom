from django.core.exceptions import ValidationError
from django.db import transaction

from universalmodels import fields
from .base import AnalysisAppInstanceModel
from .channels import Channel
from .data import FileDataObject
from .workflow_runs import AbstractWorkflowRun, InputOutput
from .workflows import Workflow


class RunRequest(AnalysisAppInstanceModel):

    workflow = fields.ForeignKey('AbstractWorkflow')
    inputs = fields.OneToManyField('RunRequestInput', related_name='run_request')
    outputs = fields.OneToManyField('RunRequestOutput', related_name='run_request')
    run = fields.ForeignKey('AbstractWorkflowRun', null=True)
    status = fields.CharField(
        max_length=255,
        default='running',
        choices=(
            ('running', 'Running'),
            ('completed', 'Completed')
        )
    )

    def after_create_or_update(self):
        self._create_outputs()
        self._validate_run_request()
        self.run = AbstractWorkflowRun.create_run_from_workflow(self.workflow)
        self.save()
        self._initialize_channels()
        for input in self.inputs.all():
            input.push()

    def _create_outputs(self):
        for workflow_output in self.workflow.outputs.all():
            if not self.outputs.filter(channel=workflow_output.channel):
                self.outputs.add(
                    RunRequestOutput.create({
                        'channel': workflow_output.channel
                    })
                )

    def _validate_run_request(self):
        # Verify that there is 1 WorkflowInput for each RunRequestInput and that their channel names match
        workflow_inputs = set([input.channel for input in self.workflow.inputs.all()])
        for input in self.inputs.all():
            if not input.channel in workflow_inputs:
                raise ValidationError('Run request is invalid. Input channel "%s" does not correspond to any channel in the workflow' % input.channel)
            workflow_inputs.remove(input.channel)

            # Verify that all input values match exactly one DataObject
            matches = FileDataObject.get_by_name_and_full_id(input.value)
            if matches.count() < 1:
                raise ValidationError('Could not find file with ID "%s"' % input.value)
            if matches.count() > 1:
                raise ValidationError('Found multiple files with ID "%s"' % input.value)

        if len(workflow_inputs) > 0:
            raise ValidationError('Missing input for channel(s) "%s"' %
                                  ', '.join([channel for channel in workflow_inputs]))

        # Verify that there is 1 WorkflowOutput for each RunRequestOutput and that their channel names match
        workflow_outputs = set([output.channel for output in self.workflow.outputs.all()])
        for output in self.outputs.all():
            if not output.channel in workflow_outputs:
                raise ValidationError('Run request is invalid. Output channel "%s" does not correspond to any channel in the workflow' % output.channel)
            workflow_outputs.remove(output.channel)
        if len(workflow_outputs) > 0:
            raise ValidationError('Missing output for channel(s) "%s"' %
                                  ', '.join([channel for channel in workflow_outputs]))

    def _initialize_channels(self):
        for source in self._get_sources():
            destination = self._get_destination(source.channel)
            channel = Channel.create_from_sender(source, source.channel)
            channel.add_receiver(destination)

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
    def check_status_for_all(cls):
        pass


class RunRequestInput(InputOutput):

    channel = fields.CharField(max_length=255)
    value = fields.CharField(max_length=255)
    
    def push(self):
        file_data_object = FileDataObject.get_by_name_and_full_id(self.value)
        assert len(file_data_object) == 1
        self.to_channel.push(file_data_object.first())

class RunRequestOutput(InputOutput):

    channel = fields.CharField(max_length=255)

    def push(self):
        # TODO - mark run as complete
        pass
