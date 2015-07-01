from django.db import models

from .common import AnalysisAppBaseModel
from immutable.models import MutableModel


class AnalysisRun(MutableModel, AnalysisAppBaseModel):
    analysis_request = models.ForeignKey('AnalysisRequest')
    step_runs = models.ManyToManyField('StepRun')

    def get_ready_steps(self):
        import pdb; pdb.set_trace()
#        for step_run in self.step_runs.all():

#            if step_run.is_ready()

class StepRun(MutableModel, AnalysisAppBaseModel):
    step = models.ForeignKey('StepDefinition')
