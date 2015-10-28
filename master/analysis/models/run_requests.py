from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import models
import jsonfield

from analysis.models.common import AnalysisAppBaseModel
from analysis.models.files import DataObject
from analysis.models.input_sets import InputSetManagerFactory
from analysis.models.step_definitions import StepDefinition, StepDefinitionOutputPort
from analysis.models.step_runs import StepRun
from analysis.models.template_helper import StepTemplateHelper
from immutable.models import MutableModel


"""
This module contains RunRequests and other classes related to
receiving a request for analysis from a user.
"""


class RunRequest(MutableModel, AnalysisAppBaseModel):
    """A single instance of a user request for work. May contain
    many workflows.
    """

    _class_name = ('run_request', 'run_requests')

    FOREIGN_KEY_CHILDREN = ['workflows']
    JSON_FIELDS = ['constants']

    requester = models.CharField(max_length = 100)
    constants = jsonfield.JSONField(null=True)
    are_results_complete = models.BooleanField(default=False)

    @classmethod
    def update_and_run(cls):
        cls.update_all_statuses()
        StepRun.run_all()

    @classmethod
    def update_and_dry_run(cls):
        cls.update_all_statuses()

    @classmethod
    def update_all_statuses(cls):
        for run_request in cls.objects.filter(are_results_complete=False):
            run_request._update_status()

    def _update_status(self):
        for workflow in self.workflows.filter(are_results_complete=False):
            workflow._update_status()
        if self.workflows.filter(are_results_complete=False).count() == 0:
            self.update({'are_results_complete': True})

    def _reset_status(self):
        for workflow in self.workflows.filter(are_results_complete=True):
            workflow.reset_status()
            self.update({'are_results_complete': False})

    @classmethod
    def get_sorted(cls, count=None):
        run_requests = cls.objects.order_by('datetime_created').reverse()
        if count is not None and (run_requests.count() > count):
            run_requests = run_requests[:count]
        return [r for r in run_requests]


class Workflow(MutableModel, AnalysisAppBaseModel):
    """Each workflow may contain many processing steps, with results from one
    step optionally feeding into another step as input.
    """

    _class_name = ('workflow', 'workflows')

    FOREIGN_KEY_CHILDREN = ['steps', 'data_bindings', 'data_pipes']
    JSON_FIELDS = ['constants']

    # name is used for grouping working directories on the file server.
    name = models.CharField(max_length = 256, null=True)
    constants = jsonfield.JSONField(null=True)
    run_request = models.ForeignKey('RunRequest', related_name='workflows', null=True)
    are_results_complete = models.BooleanField(default=False)

    def _update_status(self):
        for step in self.steps.filter(are_results_complete=False):
            step._update_status()
        if self.steps.filter(are_results_complete=False).count() == 0:
            self.update({'are_results_complete': True})

    def _reset_status(self):
        for step in self.steps.filter(are_results_complete=True):
            step.reset_status()

    def get_step(self, name):
        return self.steps.get(name=name)

    def get_connector(self, step_name, destination_port_name):
        return self.get_step(step_name).get_connector(destination_port_name)

    def _get_binding(self, step_name, port_name):
        bindings = self.data_bindings.filter(destination__step=step_name, destination__port=port_name)
        if bindings.count() > 1:
            raise Exception("Multiple bindings were found on workflow %s for step %s, port %s" % (self, step_name, port_name))
        elif bindings.count() == 1:
            return bindings.first()
        else:
            return None

    def _get_data_pipe(self, step_name, port_name):
        data_pipes = self.data_pipes.filter(destination__step=step_name, destination__port=port_name)
        if data_pipes.count() > 1:
            raise Exception('Multiple data_pipes were found on workflow %s for step %s, port %s.' % (self, step_name, port_name))
        elif data_pipes.count() == 1:
            return data_pipes.first()
        else:
            return None

    def validate_model(self):
        self._validate_port_identifiers()

    def _validate_port_identifiers(self):
        for data_binding in self.data_bindings.all():
            self._validate_destination(data_binding.destination)
        for data_pipe in self.data_pipes.all():
            self._validate_destination(data_pipe.destination)
            self._validate_source(data_pipe.source)

    def _validate_destination(self, destination):
        step = self.get_step(destination.step)
        if step is None:
            raise ValidationError("No step named %s" % destination.step)
        port = step.get_input_port(destination.port)
        if port is None:
            raise ValidationError("No port named %s on step %s" % (destination.port, destination.step))

    def _validate_source(self, source):
        step = self.get_step(source.step)
        if step is None:
            raise ValidationError("No step named %s" % source.step)
        port = step.get_output_port(source.port)
        if port is None:
            raise ValidationError("No port named %s on step %s" % (source.port, source.step))


class Step(MutableModel, AnalysisAppBaseModel):
    """A step is the template for a task to be run. However it may represent many StepRuns
    in a workflow with parallel steps.
    """

    _class_name = ('step', 'steps')

    FOREIGN_KEY_CHILDREN = ['environment', 'resources', 'step_definition', 'step_run', 'input_ports', 'output_ports']
    JSON_FIELDS = ['constants']

    name = models.CharField(max_length = 256)
    command = models.CharField(max_length = 256)
    constants = jsonfield.JSONField(null=True)
    environment = models.ForeignKey('RequestEnvironment')
    resources = models.ForeignKey('RequestResourceSet')
    workflow = models.ForeignKey('Workflow', null=True, related_name='steps')
    are_results_complete = models.BooleanField(default=False)

    def get_input_set_manager(self):
        return InputSetManagerFactory.get_input_set_manager(self)

    def _update_status(self):
        self._update_existing_step_runs()
        self._update_new_step_runs()
        if self._are_all_step_runs_complete():
            self.update({'are_results_complete': True})

    def _are_all_step_runs_complete(self):
        """Are any step_runs yet to be created or any existing step_runs incomplete"""
        return not (self.get_input_set_manager().are_step_runs_pending()
                or self.step_runs.filter(are_results_complete=False).exists())

    def _update_existing_step_runs(self):
        for step_run in self.step_runs.filter(are_results_complete=False):
            step_run._update_status()

    def _update_new_step_runs(self):
        for input_set in self.get_input_set_manager().get_available_input_sets():
            if input_set.is_data_ready():
                self.create_or_get_step_run(input_set)

    def _reset_status(self):
        for step_run in self.step_runs.filter(are_results_complete=True):
            step_run.reset_status()
        self.update({'are_results_complete': False})

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

    def get_connector(self, destination_port_name):
        connectors = filter(lambda c: c.destination.port==destination_port_name, self.get_connectors())
        if not connectors:
            return None
        if len(connectors) == 1:
            return connectors[0]
        else:
            raise Exception("Found multiple connectors with port name %s" % destination_port_name)

    def get_connectors(self):
        return [c for c in self.get_bindings()] + \
            [c for c in self.get_data_pipes()]

    def get_bindings(self):
        return self.workflow.data_bindings.filter(destination__step=self.name)

    def get_data_pipes(self):
        return self.workflow.data_pipes.filter(destination__step=self)

    def create_or_get_step_run(self, input_set):
        step_definition = self.create_step_definition(input_set)
        step_run = step_definition.attach_step_run_if_one_exists(self, input_set)
        if step_run is None:
            step_run = self.create_step_run(input_set)
        return step_run

    def create_step_run(self, input_set):
        return StepRun.create({
            'step_definition': self._render_step_definition(input_set),
            'steps': [self.to_serializable_obj()],
            'output_ports': [port._render_step_run_output_port() for port in self.output_ports.all()],
            'input_ports': [self.get_input_port(input_port_name)._render_step_run_input_port(source) 
                            for input_port_name, source in input_set.inputs.iteritems()]
            })

    def create_step_definition(self, input_set):
        return StepDefinition.create(self._render_step_definition(input_set))

    def _render_step_definition(self, input_set):
        assert input_set.is_data_ready(), "Refusing to create StepDefinition until all DataObjects are available for this InputSet"
        return {
                'command': self._render_command(),
                'environment': self.get('environment')._render_step_definition_environment(),
                'output_ports': [port._render_step_definition_output_port() for port in self.output_ports.all()],
                'input_ports': [self.get_input_port(port_name)._render_step_definition_input_port(source.get_data_object())
                                for port_name, source in input_set.inputs.iteritems()],
                }

    def _render_command(self):
        return StepTemplateHelper(self).render(self.command)

    def _render_step_definition_data_bindings(self):
        return [c._render_step_definition_data_bindings(self) for c in self.get_connectors()]


class RequestEnvironment(MutableModel, AnalysisAppBaseModel):

    _class_name = ('request_environment', 'request_environments')


class RequestDockerImage(RequestEnvironment):

    _class_name = ('request_docker_image', 'request_docker_images')

    docker_image = models.CharField(max_length = 100)

    def _render_step_definition_environment(self):
        # TODO translate a docker image name into an ID
        return {'docker_image': self.docker_image}


class RequestResourceSet(MutableModel, AnalysisAppBaseModel):

    _class_name = ('request_resource_set', 'request_resource_sets')

    memory = models.CharField(max_length = 20)
    cores = models.IntegerField()


class RequestOutputPort(MutableModel, AnalysisAppBaseModel):

    _class_name = ('request_output_port', 'request_output_ports')

    name = models.CharField(max_length = 256)
    is_array = models.BooleanField(default = False)
    file_name = models.CharField(max_length = 256, null=True)
    glob = models.CharField(max_length = 256, null=True)
    step = models.ForeignKey('Step', related_name='output_ports', null=True)

    def _render_step_definition_output_port(self):
        return {
            'file_name': StepTemplateHelper(self.step).render(self.file_name),
            'glob': StepTemplateHelper(self.step).render(self.glob),
            'is_array': self.is_array
            }

    def _render_step_run_output_port(self):
        return {
            'name': self.name,
            'step_definition_output_port': self._render_step_definition_output_port()
            }


class RequestInputPort(MutableModel, AnalysisAppBaseModel):

    _class_name = ('request_input_port', 'request_input_ports')

    name = models.CharField(max_length = 256)
    file_name = models.CharField(max_length = 256)
    step = models.ForeignKey('Step', related_name='input_ports', null=True)
    is_array = models.BooleanField(default = False)

    def get_connector(self):
        connector = self._get_binding()
        if connector is None:
            connector = self._get_data_pipe()
        return connector

    def _get_binding(self):
        if not self.step.workflow:
            return None
        return self.step.workflow._get_binding(port_name=self.name, step_name=self.step.name)

    def _get_data_pipe(self):
        if not self.step.workflow:
            return None
        return self.step.workflow._get_data_pipe(
            port_name=self.name, step_name=self.step.name)

    def _render_step_definition_input_port(self, data_object):
        return {
            'file_name': StepTemplateHelper(self.step).render(self.file_name),
            'is_array': self.is_array,
            'data_object': data_object.to_serializable_obj()
            }

    def _render_step_run_input_port(self, source):
        return {
            'name': self.name,
            'step_definition_input_port': self._render_step_definition_input_port(source.get_data_object())
            }


class RequestDataBinding(MutableModel, AnalysisAppBaseModel):
    """Connects an already existing DataObject to the input port of a step"""

    _class_name = ('request_data_binding', 'request_data_bindings')

    FOREIGN_KEY_CHILDREN = ['data_object', 'destination']

    data_object = models.ForeignKey('DataObject')
    destination = models.ForeignKey('RequestDataBindingDestinationPortIdentifier')
    workflow = models.ForeignKey('Workflow', related_name='data_bindings', null=True)

    def is_data_pipe(self):
        return False

    def is_data_ready(self):
        self.get_data_object().is_available()

    def get_data_object(self):
        return self.get('data_object', downcast=True)

    def is_source_an_array(self):
        return self.data_object.is_array

    def is_destination_an_array(self):
        return self.get_destination_step().get_input_port(self.destination.port).is_array

    def get_destination_step(self):
        if not self.workflow:
            raise Exception("No workflow defined for RequestDataBinding %s" % self.to_obj())
        return self.workflow.get_step(self.destination.step)

    def get_destination_port(self):
        return self.get_destination_step().get_input_port(self.destination.port)

    def _render_step_definition_data_bindings(self, step):
        return {
            'data_object': self.data_object.to_obj(),
            'input_port': self.get_destination_port()._render_step_definition_input_port()
            }


class RequestDataPipe(MutableModel, AnalysisAppBaseModel):
    """Connects an output port of a previous step to an input port
    of the current step.
    """

    _class_name = ('request_data_pipe', 'request_data_pipes')

    FOREIGN_KEY_CHILDREN = ['source', 'destination']

    source = models.ForeignKey('RequestDataPipeSourcePortIdentifier')
    destination = models.ForeignKey('RequestDataPipeDestinationPortIdentifier')
    workflow = models.ForeignKey('Workflow', related_name='data_pipes', null=True)

    def is_data_pipe(self):
        return True

    def get_source_step(self):
        return self.workflow.get_step(self.source.step)

    def get_destination_step(self):
        return self.workflow.get_step(self.destination.step)

    def is_source_an_array(self):
        return self.get_source_step().get_output_port(self.source.port).is_array

    def is_destination_an_array(self):
        return self.get_destination_step().get_input_port(self.destination.port).is_array

    def _render_step_definition_data_bindings(self, step):
        port = step.get_input_port(self.destination.port)
        return {
            'data_object': self.get_data_object().to_obj(),
            'input_port': port._render_step_definition_input_port()
            }


class RequestPortIdentifier(MutableModel, AnalysisAppBaseModel):

    step = models.CharField(max_length = 256)
    port = models.CharField(max_length = 256)

    class Meta:
        abstract = True


class RequestDataBindingDestinationPortIdentifier(RequestPortIdentifier):

    _class_name = ('request_data_binding_port_identifier', 'request_data_binding_port_identifiers')


class RequestDataPipeSourcePortIdentifier(RequestPortIdentifier):

    _class_name = ('request_data_pipe_source_port_identifier', 'request_data_pipe_source_port_identifiers')


class RequestDataPipeDestinationPortIdentifier(RequestPortIdentifier):

    _class_name = ('request_data_pipe_destination_port_identifier', 'request_data_pipe_destination_port_identifiers')

