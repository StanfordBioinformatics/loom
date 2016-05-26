from django.core.exceptions import ValidationError

from universalmodels import fields
from .base import AnalysisAppInstanceModel
from .workflows import Workflow
from .data_objects import FileDataObject


class RunRequest(AnalysisAppInstanceModel):

    workflow = fields.ForeignKey('AbstractWorkflow')
    inputs = fields.OneToManyField('RunRequestInput')

    def _create_or_update_fields(self, data):
        o = super(RunRequest, self)._create_or_update_fields(data)
        self._validate_run_request()

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
            raise ValidationError('Run request is invalid. Inputs were not provided for %s' %
                                  ', '.join([channel for channel in workflow_inputs]))


class RunRequestInput(AnalysisAppInstanceModel):
    
    id = fields.CharField(max_length=255)
    channel = fields.CharField(max_length=255)
