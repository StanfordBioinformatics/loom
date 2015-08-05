from django.db import models

from immutable.models import MutableModel
from analysis.models import FileLocation, File, StepResult

from .common import AnalysisAppBaseModel


class StepRun(MutableModel, AnalysisAppBaseModel):
    _class_name = ('step_run', 'step_runs')
    FOREIGN_KEY_CHILDREN = ['step_definition', 'process_location']
    step_definition = models.ForeignKey('StepDefinition')
    step_results = models.ManyToManyField('StepResult')
    is_complete = models.BooleanField(default=False)
    process_location = models.ForeignKey('ProcessLocation', null=True)

    def get_output_file(self, port):
        step_result = self.get_step_result(port)
        if step_result == None:
            return None
        else:
            return step_result.output_binding.file

    def get_step_result(self, port):
        try:
            step_result = self.step_results.get(output_binding__output_port=port)
        except StepResult.DoesNotExist:
            step_result = None
        return step_result

    def add_step_result(self, step_result_obj):
        step_result = StepResult.create(step_result_obj)
        self.step_results.add(step_result)
        return step_result

    def get_input_port_bundles(self):
        # Bundles info for a port into a list with port, file, and file locations.
        # Returns a list of these bundles, one for each input_port
        bundles = []
        for binding in self.step_definition.data_bindings.all():
            file = binding.file
            file_locations = FileLocation.get_by_file(file).all()
            input_port = binding.input_port
            bundles.append(
                {
                    'file': file.to_obj(),
                    'file_locations': [file_location.to_obj() for file_location in file_locations],
                    'input_port': input_port.to_obj(),
                    }
                )
        return bundles

    def __str__(self):
        return self.step_definition.template.command


class ProcessLocation(MutableModel, AnalysisAppBaseModel):
    _class_name = ('process_location', 'process_locations')


class LocalProcessLocation(ProcessLocation):
    _class_name = ('local_process_location', 'local_process_locations')

    pid = models.IntegerField()
