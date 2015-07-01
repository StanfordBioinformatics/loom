from django.db import models

from .common import AnalysisAppBaseModel
from .files import File
from .definitions import StepDefinitionOutputPort
from immutable.models import ImmutableModel


class StepResult(ImmutableModel, AnalysisAppBaseModel):
    step_definition = models.ForeignKey('StepDefinition')
    output_bindings = models.ManyToManyField('OutputBinding')

class OutputBinding(ImmutableModel, AnalysisAppBaseModel):
    _class_name = ('step_result_input_binding', 'step_result_input_bindings')

    file = models.ForeignKey('File')
    output_port = models.ForeignKey('StepDefinitionOutputPort')
