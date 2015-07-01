from django.db import models

from .common import AnalysisAppBaseModel
from .files import File
from .definitions import StepDefinition
from immutable.models import MutableModel


class Request(MutableModel, AnalysisAppBaseModel):
    _class_name = ('request', 'requests')
    analyses = models.ManyToManyField('AnalysisRequest')
    requester = models.CharField(max_length = 100)

    def get_analyses(self):
        return self.analyses.all()

    def is_ready(self):
        # Returns True if all analyses are finished
        for analysis in self.analyses.all():
            if not analysis.is_ready():
                return False
        return True

class AnalysisRequest(MutableModel, AnalysisAppBaseModel):
    _class_name = ('analysis_request', 'analysis_requests')
    # steps: StepRequest has reverse foreign key
    input_bindings = models.ManyToManyField('RequestInputBinding')
    connectors = models.ManyToManyField('RequestConnector')        

    def get_step_request(self, name):
        return self.steps.get(name=name)

    def get_binding(self, step_name, port_name):
        bindings = self.input_bindings.filter(destination__step=step_name, destination__port=port_name)
        if bindings.count() > 1:
            raise Exception("Multiple bindings were found on analysis_request %s for step %s, port %s" % (self, step_name, port_name))
        elif bindings.count() == 1:
            return bindings.first()
        else:
            return None
        
    def get_connector_by_destination_port_name(self, step_name, port_name):
        connectors = self.connectors.filter(destination__step=step_name, destination__port=port_name)
        if connectors.count() > 1:
            raise Exception('Multiple connectors were found on analysis_request %s for step %s, port %s.' % (self, step_name, port_name))
        elif connectors.count() == 1:
            return connectors.first()
        else:
            return None

    def is_ready(self):
        # Returns True if all steps are finished
        for step in self.steps.all():
            if not step.is_ready():
                return False
        return True

class StepRequest(MutableModel, AnalysisAppBaseModel):
    _class_name = ('step_request', 'step_requests')
    name = models.CharField(max_length = 256)
    # input_ports = models.ManyToManyField('RequestInputPort')
    # output_ports = models.ManyToManyField('RequestOutputPort')
    command = models.CharField(max_length = 256)
    environment = models.ForeignKey('EnvironmentRequest')
    resources = models.ForeignKey('ResourceRequest')
    analysis_request = models.ForeignKey('AnalysisRequest', null=True, related_name='steps')
    step = models.ForeignKey('StepDefinition', null=True)

    def get_input_port(self, name):
        return self.input_ports.get(name=name)

    def get_output_port(self, name):
        return self.output_ports.get(name=name)

    def is_ready(self):
        # Returns True if all input files are avaialble
        for port in self.input_ports.all():
            if not port.is_ready():
                return False
        return True

    def create_and_attach_step(self):
        self.update({
                'step': self._render_step()
                }
            )

    def _render_definition(self):
        step = {
            'step_template': {
                'command': self.command,
                'environment': self.get('environment')._render_definition(),
                'input_ports': [port._render_definition() for port in self.input_ports.all()],
                'output_ports': [port._render_definition() for port in self.output_ports.all()],
                },
            'input_bindings': [binding._render_definition() for binding in self.input_bindings.all()]
            }

class EnvironmentRequest(MutableModel, AnalysisAppBaseModel):
    _class_name = ('environment_request', 'environment_requests')

class DockerImageRequest(EnvironmentRequest):
    _class_name = ('docker_image_request', 'docker_image_requests')
    docker_image = models.CharField(max_length = 100)

    def render_environment(self):
        # TODO translate a docker image name into an ID
        return {'docker_image': self.docker_image}

class ResourceRequest(MutableModel, AnalysisAppBaseModel):
    _class_name = ('resource_request', 'resource_requests')
    memory = models.CharField(max_length = 20)
    cores = models.IntegerField()

class RequestOutputPort(MutableModel, AnalysisAppBaseModel):
    _class_name = ('request_output_port', 'request_output_ports')

    # Relative path within the working directory where
    # a file will be found after a step executes
    name = models.CharField(max_length = 256)
    file_path = models.CharField(max_length = 256)
    step_request = models.ForeignKey('StepRequest', related_name='output_ports', null=True)

class RequestInputPort(MutableModel, AnalysisAppBaseModel):
    _class_name = ('request_input_port', 'request_input_ports')

    # Relative path within the working directory where
    # a file will be copied before a step is executed
    name = models.CharField(max_length = 256)
    file_path = models.CharField(max_length = 256)
    step_request = models.ForeignKey('StepRequest', related_name='input_ports', null=True)

    def _render_as_immutable(self):
        return {'file_path': self.file_path}

    def is_ready(self):
        # Returns True if the input file is available
        # TODO

        if self.get_file() is not None:
            return True
        else:
            return False

    def get_file(self):
        bound_file = self.get_bound_file()
        if bound_file is not None:
            return bound_file
        connected_file = self.get_connected_file()
        if connected_file is not None:
            return connected_file
        return None

    def get_bound_file(self):
        binding = self.get_binding()
        if binding is None:
            return None
        else:
            return binding.get_file()

    def get_binding(self):
        return self.step_request.analysis_request.get_binding(port_name=self.name, step_name=self.step_request.name)

    def get_connected_file(self):
        connector = self.get_connector()
        if connector is None:
            return None
        else: 
            return connector.get_file()

    def get_connector(self):
        return self.step_request.analysis_request.get_connector_by_destination_port_name(
            port_name=self.name, step_name=self.step_request.name)

class RequestInputBinding(MutableModel, AnalysisAppBaseModel):
    _class_name = ('request_input_binding', 'request_input_bindings')

    file = models.ForeignKey('File')
    destination = models.ForeignKey('InputBindingPortIdentifier')

    def is_ready(self):
        # Returns True if the input file is available
        if not self.file.exists():
            return False
        else:
            if self.file.is_available():
                return True
            else:
                return False

    def get_file(self):
        return file

class RequestConnector(MutableModel, AnalysisAppBaseModel):
    _class_name = ('request_connector', 'request_connectors')

    source = models.ForeignKey('RequestConnectorSourcePortIdentifier')
    destination = models.ForeignKey('RequestConnectorDestinationPortIdentifier')

    def get_file(self):
        # TODO
        return None

class PortIdentifier(MutableModel, AnalysisAppBaseModel):
    step = models.CharField(max_length = 256)
    port = models.CharField(max_length = 256)

    class Meta:
        abstract = True

class InputBindingPortIdentifier(PortIdentifier):
    _class_name = ('input_binding_port_identifier', 'input_binding_port_identifiers')

class RequestConnectorSourcePortIdentifier(PortIdentifier):
    _class_name = ('request_connector_source_port_identifier', 'request_connector_source_port_identifiers')

class RequestConnectorDestinationPortIdentifier(PortIdentifier):
    _class_name = ('request_connector_destination_port_identifier', 'request_connector_destination_port_identifiers')
