from django.db import models

from .common import AnalysisAppBaseModel
from immutable.models import MutableModel


class StepRun(MutableModel, AnalysisAppBaseModel):
    step_definition = models.ForeignKey('StepDefinition')
    step_result = models.ManyToManyField('StepResult')
    is_complete = models.BooleanField(default=False)
