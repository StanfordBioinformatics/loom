from django.core.exceptions import ValidationError
from django.db import transaction

from universalmodels import fields
from .base import AnalysisAppInstanceModel
from .data_objects import FileDataObject
from .workflow_runs import AbstractWorkflowRun
from .workflows import Workflow

class RunRequest(AnalysisAppInstanceModel):

    workflow = fields.ForeignKey('AbstractWorkflow')
    inputs = fields.OneToManyField('RunRequestInput')
    run = fields.ForeignKey('AbstractWorkflowRun', null=True)

    def after_create(self):
        self._validate_run_request()
        self.run = AbstractWorkflowRun.create_run_from_workflow(self.workflow)
        self.save()

    def _validate_run_request(self):
        workflow_inputs = set([input.channel for input in self.workflow.inputs.all()])
        for input in self.inputs.all():
            if not input.channel in workflow_inputs:
                raise ValidationError('Run request is invalid. Input channel "%s" does not correspond to any channel in the workflow' % input.channel)
            workflow_inputs.remove(input.channel)

            matches = FileDataObject.get_by_name_and_full_id(input.id)
            if matches.count() < 1:
                raise ValidationError('Could not find file with ID "%s"' % input.id)
            if matches.count() > 1:
                raise ValidationError('Found multiple files with ID "%s"' % input.id)
            
        if len(workflow_inputs) > 0:
            raise ValidationError('Missing input for channel "%s"' %
                                  ', '.join([channel for channel in workflow_inputs]))


class RunRequestInput(AnalysisAppInstanceModel):

    id = fields.CharField(max_length=255)
    channel = fields.CharField(max_length=255)
