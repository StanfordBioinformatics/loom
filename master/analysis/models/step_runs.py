from django.core import exceptions
from django.db import models

from analysis.models.common import AnalysisAppBaseModel
from analysis.models.step_definitions import StepDefinitionOutputPort
from analysis.models.files import DataObject
from immutable.models import MutableModel, ImmutableModel


class StepResult(MutableModel, AnalysisAppBaseModel):
    """Assigns a DataObject result to one OutputPort of one StepRun"""

    _class_name = ('step_result', 'step_results')

    FOREIGN_KEY_CHILDREN = ['data_object', 'output_port']

    data_object = models.ForeignKey('DataObject', related_name='step_results')
    output_port = models.OneToOneField('StepRunOutputPort', related_name='step_result')


class StepRunOutputPort(MutableModel, AnalysisAppBaseModel):

    _class_name = ('step_run_output_port', 'step_run_output_ports')

    FOREIGN_KEY_CHILDREN = ['step_definition_output_port']

    name = models.CharField(max_length = 256)
    step_run = models.ForeignKey('StepRun', related_name='output_ports', null=True)
    step_definition_output_port = models.ForeignKey('StepDefinitionOutputPort', null=True)

    def get_data_object(self):
        try:
            return self.step_result.get('data_object')
        except exceptions.ObjectDoesNotExist:
            return None

    def is_available(self):
        data_object = self.get_data_object()
        if data_object is None:
            return False
        else:
            return data_object.is_available()


class StepRunInputPort(MutableModel, AnalysisAppBaseModel):

    _class_name = ('step_run_input_port', 'step_run_input_ports')

    FOREIGN_KEY_CHILDREN = ['step_definition_input_port']

    name = models.CharField(max_length = 256)
    step_run = models.ForeignKey('StepRun', related_name='input_ports', null=True)
    step_definition_input_port = models.ForeignKey('StepDefinitionInputPort', null=True)


class StepRun(MutableModel, AnalysisAppBaseModel):
    """One instance of executing a step. A step can have many InputSets
    if there is a parallel workflow, and each InputSet will generate at 
    least one StepRun. A step can also have distinct StepRuns for reruns
    with the same InputSet.
    """

    _class_name = ('step_run', 'step_runs')

    FOREIGN_KEY_CHILDREN = ['step', 'step_definition', 'process_location', 'input_ports', 'output_ports']

    # If multiple steps have the same StepDefinition, they can share a StepRun
    steps = models.ManyToManyField('Step', related_name='step_runs') 
    step_definition = models.ForeignKey('StepDefinition', null=True, related_name='step_runs')
    process_location = models.ForeignKey('ProcessLocation', null=True)
    are_results_complete = models.BooleanField(default=False)
    is_running = models.BooleanField(default=False)

    @classmethod
    def create_step_run(cls, step_definition, step):
        cls.create({
                'step': step.to_serializable_obj(),
                'step_definition': step_definition.to_serializable_obj()
                })

    def _update_status(self):
        if all([ port.is_available() for port in self.output_ports.all()]):
            self.update({'are_results_complete': True})

    def _reset_status(self):
        self.update({'are_results_complete': False})

    def get_input_bundles(self):
        # Bundles info for a port into a list with port, file, and file locations.
        # Returns a list of these bundles, one for each input port binding
        return self.step_definition.get_input_bundles()

    def has_step(self, step):
        steps = self.steps.filter(_id=step._id)
        return len(steps) > 0

    def add_step(self, step):
        self.steps.add(step)
        self.save()

    def get_input_port(self, name):
        try:
            return self.input_ports.get(name=name)
        except ObjectDoesNotExist:
            return None

    def get_output_port(self, name):
        try:
            return self.output_ports.get(name=name)
        except ObjectDoesNotExist:
            return None

    @classmethod
    def run_all(cls):
        from analysis.worker_manager.factory import WorkerManagerFactory
        worker_manager = WorkerManagerFactory.get_worker_manager()
        for step_run in StepRun.objects.filter(are_results_complete=False, is_running=False):
            worker_manager.run(step_run)

    def get_step_run_output_port_by_step_definition_output_port(self, step_definition_output_port):
        return self.output_ports.get(step_definition_output_port=step_definition_output_port._id)

    def add_step_result(self, data_object, step_definition_output_port):
        step_run_output_port = self.get_step_run_output_port_by_step_definition_output_port(step_definition_output_port)
        return StepResult.create(
            {
                'data_object': data_object.to_serializable_obj(),
                'output_port': step_run_output_port.to_serializable_obj()
                }
            )

    @classmethod
    def submit_result(cls, result_info_obj_or_json):
        result_info_obj = StepResult._any_to_obj(result_info_obj_or_json)
        step_definition_output_port = StepDefinitionOutputPort.get_by_definition(result_info_obj.get('step_result').get('output_port'))
        data_object = DataObject.create(result_info_obj.get('step_result').get('data_object'))
        step_run = StepRun.get_by_definition(result_info_obj.get('step_run'))
        return step_run.add_step_result(data_object, step_definition_output_port)

    def __str__(self):
        return self.step_definition.command


class StepRunDataBinding(MutableModel, AnalysisAppBaseModel):
    """ Connects existing DataObject as input for a StepRun"""

    _class_name = ('step_run_data_binding', 'step_run_data_bindings')

    destination =  models.ForeignKey('StepRunDataBindingDestinationPortIdentifier')
    source = models.ForeignKey('DataObject')


class StepRunDataPipe(MutableModel, AnalysisAppBaseModel):
    """Connects output from another StepRun as input for a StepRun"""

    _class_name = ('step_run_data_pipe', 'step_run_data_pipes')

    destination =  models.ForeignKey('StepRunDataPipeDestinationPortIdentifier')
    source =  models.ForeignKey('StepRunDataPipeSourcePortIdentifier')


class StepRunPortIdentifier(MutableModel, AnalysisAppBaseModel):

    FOREIGN_KEY_CHILDREN = ['port']

    step_run = models.ForeignKey('StepRun')
    port = models.CharField(max_length = 256, null=True)

    class Meta:

        abstract = True


class StepRunDataBindingDestinationPortIdentifier(StepRunPortIdentifier):

    _class_name = ('step_run_data_binding_destination_port_identifier', 'step_run_data_binding_destination_port_identifiers')


class StepRunDataPipeDestinationPortIdentifier(StepRunPortIdentifier):

    _class_name = ('step_run_data_pipe_destination_port_identifier', 'step_run_data_pipe_destination_port_identifiers')


class StepRunDataPipeSourcePortIdentifier(StepRunPortIdentifier):

    _class_name = ('step_run_data_pipe_source_port_identifier', 'step_run_data_pipe_source_port_identifiers')


class ProcessLocation(MutableModel, AnalysisAppBaseModel):

    _class_name = ('process_location', 'process_locations')


class LocalProcessLocation(ProcessLocation):

    _class_name = ('local_process_location', 'local_process_locations')

    pid = models.IntegerField()
