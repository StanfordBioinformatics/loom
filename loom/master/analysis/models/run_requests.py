from universalmodels import fields
from .base import AnalysisAppInstanceModel
from .workflows import Workflow
from .data_objects import DataObject


class RunRequest(AnalysisAppInstanceModel):

    workflow = fields.ForeignKey('AbstractWorkflow')
    inputs = fields.OneToManyField('RunRequestInput')


class RunRequestInput(AnalysisAppInstanceModel):
    
    id = fields.CharField(max_length=255)
    channel = fields.CharField(max_length=255)
