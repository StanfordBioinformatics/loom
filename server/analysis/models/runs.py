from django.db import models

from .common import AnalysisAppBaseModel
from .results import StepResult
from immutable.models import MutableModel


class StepRun(MutableModel, AnalysisAppBaseModel):
    step_definition = models.ForeignKey('StepDefinition')
    step_results = models.ManyToManyField('StepResult')
    is_complete = models.BooleanField(default=False)

    def get_output_file(self, port):
        step_result = self.get_step_result(port)
        if step_result == None:
            return None
        else:
            return step_result.output_binding.file

    def get_step_result(self, port):
        step_results = self.step_results.filter(output_binding__output_port=port)
        if step_results.count() == 1:
            return step_results.first()
        elif step_results.count() == 0:
            return None
        else:
            raise Exception("Multiple step_results found for the same port")

    def add_step_result(self, step_result_obj):
        step_result = StepResult.create(step_result_obj)
        self.step_results.add(step_result)

    def __str__(self):
        return self.step_definition.template.command
