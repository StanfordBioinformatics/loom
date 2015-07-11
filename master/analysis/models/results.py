from django.db import models

from .common import AnalysisAppBaseModel
from .files import File
from .definitions import StepDefinitionOutputPort
from immutable.models import ImmutableModel


class StepResult(ImmutableModel, AnalysisAppBaseModel):
    _class_name = ('step_result', 'step_results')

    step_definition = models.ForeignKey('StepDefinition')
    output_binding = models.ForeignKey('StepResultOutputBinding')

class StepResultOutputBinding(ImmutableModel, AnalysisAppBaseModel):
    _class_name = ('result_output_binding', 'result_output_bindings')

    file = models.ForeignKey('File')
    output_port = models.ForeignKey('StepDefinitionOutputPort')
