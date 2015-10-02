from django.db import models

from .common import AnalysisAppBaseModel
from .files import DataObject
from .step_definitions import StepDefinitionOutputPort
from immutable.models import ImmutableModel


class StepResult(ImmutableModel, AnalysisAppBaseModel):
    _class_name = ('step_result', 'step_results')
    FOREIGN_KEY_CHILDREN = ['step_definition', 'output_binding']
    step_definition = models.ForeignKey('StepDefinition')
    output_binding = models.ForeignKey('StepResultOutputBinding')

class StepResultOutputBinding(ImmutableModel, AnalysisAppBaseModel):
    _class_name = ('result_output_binding', 'result_output_bindings')
    FOREIGN_KEY_CHILDREN = ['data_object', 'output_port']
    data_object = models.ForeignKey('File')
    output_port = models.ForeignKey('StepDefinitionOutputPort')
