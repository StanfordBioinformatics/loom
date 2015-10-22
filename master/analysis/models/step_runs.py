from django.db import models
from immutable.models import MutableModel, ImmutableModel
from .common import *


class StepResult(ImmutableModel, AnalysisAppBaseModel):
    _class_name = ('step_result', 'step_results')
    FOREIGN_KEY_CHILDREN = ['step_definition', 'data_object', 'output_port']
    step_definition = models.ForeignKey('StepDefinition')
    data_object = models.ForeignKey('DataObject')
    output_port = models.ForeignKey('StepDefinitionOutputPort')


class StepRunOutputPort:
    # Not a database model, just a runtime construct

    def __init__(self, step_run, step_definition_output_port):
        self.step_run = step_run
        self.step_definition_output_port = step_definition_output_port

    def get_data_object(self):
        return self.step_run.get_output_data_object(self)

    def is_available(self):
        data_object = self.get_data_object()
        if data_object is None:
            return False
        else:
            return data_object.is_available()

class StepRun(MutableModel, AnalysisAppBaseModel):

    _class_name = ('step_run', 'step_runs')

    FOREIGN_KEY_CHILDREN = ['step', 'step_definition', 'process_location', 'data_connector']

    # If multiple steps have the same StepDefinition, they can share a StepRun
    steps = models.ManyToManyField('Step', related_name='step_runs') 
    step_definition = models.ForeignKey('StepDefinition', null=True)
    # One StepResult per StepDefinition.output_port
    step_results = models.ManyToManyField('StepResult') 
    process_location = models.ForeignKey('ProcessLocation', null=True)
    are_results_complete = models.BooleanField(default=False)

    @classmethod
    def create_from_definition(cls, step_definition, step):
        cls.create({
                'step': step.to_serializable_obj(),
                'step_definition': step_definition.to_serializable_obj()
                })

    def _update_status(self):
        # Are all results complete?
        pass

    def _reset_status(self):
        self.are_results_complete = False

    def get_output_data_object(self, step_run_port):
        step_result = self.get_step_result(step_run_port)
        if step_result == None:
            return None
        else:
            return step_result.get('data_object')

    def get_step_result(self, step_run_port):
        try:
            step_result = self.step_results.get(output_port=step_run_port.step_definition_output_port)
        except StepResult.DoesNotExist:
            step_result = None
        return step_result

    def add_step_result(self, step_result_obj):
        step_result = StepResult.create(step_result_obj)
        self.step_results.add(step_result)
        return step_result

    def get_input_bundles(self):
        # Bundles info for a port into a list with port, file, and file locations.
        # Returns a list of these bundles, one for each input port binding
        return self.step_definition.get_input_bundles()

    def get_output_ports(self):
        return [StepRunOutputPort(self, port) for port in self.step_definition.output_ports.all()]

    def has_step(self, step):
        steps = self.steps.filter(_id=step._id)
        return len(steps) > 0

    def add_step(self, step):
        self.steps.add(step)
        self.save()

    def __str__(self):
        return self.step_definition.command


class StepRunConnector(MutableModel, AnalysisAppBaseModel):
    # Connects data source to the input source of a StepRun.
    # Parent class for DatObjectConnectors and PortConnectors
    #
    # StepRunConnectors are distinct from connections to a StepDefinition
    # because StepDefinitions can only be created after the input file exists, where
    # StepRunConnectors can point to a source port.
    # 
    # StepRunConnectors differ from StepConnectors when parallel workflows are used, since each 
    # Step may be executed on many files, each with its own StepRun. StepConnectors point to the source
    # Step but not to the specific StepRun.

    _class_name = ('step_run_data_connector', 'step_run_data_connectors')
    workflow = models.ForeignKey('Workflow')
    destination =  models.ForeignKey('StepRunConnectorDestinationPortIdentifier')


class StepRunDataObjectConnector(StepRunConnector):
    # Connects existing DataObject as input for a StepRun
    _class_name = ('step_run_data_binding', 'step_run_data_bindings')
    data_object = models.ForeignKey('DataObject')


class StepRunPortConnector(StepRunConnector):
    # Connects output from another StepRun as input for a StepRun
    _class_name = ('step_run_data_connector')
    source =  models.ForeignKey('StepRunConnectorSourcePortIdentifier')


class PortIdentifier(MutableModel, AnalysisAppBaseModel):
    step_run = models.ForeignKey('StepRun')
    port = models.CharField(max_length = 256)
    class Meta:
        abstract = True  


class StepRunConnectorDestinationPortIdentifier(PortIdentifier):
    _class_name = ('step_run_connector_destination_port_identifier', 'step_run_connector_destination_port_identifiers')


class StepRunConnectorSourcePortIdentifier(PortIdentifier):
    _class_name = ('step_run_connector_source_port_identifier', 'step_run_connector_source_port_identifiers')


class ProcessLocation(MutableModel, AnalysisAppBaseModel):
    _class_name = ('process_location', 'process_locations')


class LocalProcessLocation(ProcessLocation):
    _class_name = ('local_process_location', 'local_process_locations')
    pid = models.IntegerField()
