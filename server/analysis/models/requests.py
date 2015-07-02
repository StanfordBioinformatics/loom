from django.db import models

from .common import AnalysisAppBaseModel
from .files import File
from .definitions import StepDefinition
from immutable.models import MutableModel


"""
This module contains Requests and other classes related to
receiving a request for analysis from a user.
"""


class Request(MutableModel, AnalysisAppBaseModel):
    _class_name = ('request', 'requests')
    analyses = models.ManyToManyField('AnalysisRequest')
    requester = models.CharField(max_length = 100)

    def get_analyses(self):
        return self.analyses.all()

    def is_complete(self):
        # Returns True if all analyses are finished
        for analysis in self.analyses.all():
            if not analysis.is_complete():
                return False
        return True

class AnalysisRequest(MutableModel, AnalysisAppBaseModel):
    _class_name = ('analysis_request', 'analysis_requests')
    # steps: StepRequest has reverse foreign key
    data_bindings = models.ManyToManyField('RequestDataBinding')
    data_pipes = models.ManyToManyField('RequestDataPipe')        

    def get_steps_ready_to_run(self):
        steps = []
        for step in self.steps.all():
            if step.are_inputs_ready():
                steps.append(step)
        return steps

    def get_step(self, name):
        return self.steps.get(name=name)

    def get_binding(self, step_name, port_name):
        bindings = self.data_bindings.filter(destination__step=step_name, destination__port=port_name)
        if bindings.count() > 1:
            raise Exception("Multiple bindings were found on analysis %s for step %s, port %s" % (self, step_name, port_name))
        elif bindings.count() == 1:
            return bindings.first()
        else:
            return None

    def _get_bindings_by_step(self, step_name):
        return self.data_bindings.filter(destination__step=step_name)
        
    def get_data_pipe_by_destination_port_name(self, step_name, port_name):
        data_pipes = self.data_pipes.filter(destination__step=step_name, destination__port=port_name)
        if data_pipes.count() > 1:
            raise Exception('Multiple data_pipes were found on analysis %s for step %s, port %s.' % (self, step_name, port_name))
        elif data_pipes.count() == 1:
            return data_pipes.first()
        else:
            return None

    def is_complete(self):
        # Returns True if all steps are finished
        for step in self.steps.all():
            if not step.is_complete():
                return False
        return True

class StepRequest(MutableModel, AnalysisAppBaseModel):
    _class_name = ('step_request', 'step_requests')
    name = models.CharField(max_length = 256)
    command = models.CharField(max_length = 256)
    environment = models.ForeignKey('RequestEnvironment')
    resources = models.ForeignKey('RequestResourceSet')
    analysis = models.ForeignKey('AnalysisRequest', null=True, related_name='steps')
    step_definition = models.ForeignKey('StepDefinition', null=True)
    step_run = models.ForeignKey('StepRun', null=True)

    def attach_to_run_if_one_exists(self):
        step_definition = self._create_step_definition()
        step_run = step_definition.get_step_run()
        if step_run is not None:
            self.update({'step_run': step_run.to_obj()})

    def has_run(self):
        if self.step_run is not None:
            return True
        else:
            return False

    def create_step_run(self):
        step_definition = self._create_step_definition()
        self.update(
            {
                'step_run': {
                    'step_definition': step_definition.to_obj()
                    } 
                }
            )

    def _create_step_definition(self):
        return StepDefinition.create(self._render_step_definition())

    def _render_step_definition(self):
        step_definition = {
            'template': {
                'command': self.command,
                'environment': self.get('environment')._render_step_definition_environment(),
                'input_ports': [port._render_step_definition_input_port() for port in self.input_ports.all()],
                'output_ports': [port._render_step_definition_output_port() for port in self.output_ports.all()],
                },
            'data_bindings': [binding._render_step_definition_data_bindings(self) for binding in self.analysis._get_bindings_by_step(self.name)]
            }
        return step_definition

    def _get_input_port(self, name):
        return self.input_ports.get(name=name)

    def _get_output_port(self, name):
        return self.output_ports.get(name=name)

    def are_inputs_ready(self):
        # Returns True if all input files are avaialble
        for port in self.input_ports.all():
            if not port.has_file():
                return False
        return True

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

    # Relative path within the working directory where
    # a file will be found after a step executes
    name = models.CharField(max_length = 256)
    file_path = models.CharField(max_length = 256)
    step_request = models.ForeignKey('StepRequest', related_name='output_ports', null=True)

    def _render_step_definition_output_port(self):
        return {'file_path': self.file_path}

class RequestInputPort(MutableModel, AnalysisAppBaseModel):
    _class_name = ('request_input_port', 'request_input_ports')

    # Relative path within the working directory where
    # a file will be copied before a step is executed
    name = models.CharField(max_length = 256)
    file_path = models.CharField(max_length = 256)
    step_request = models.ForeignKey('StepRequest', related_name='input_ports', null=True)

    def _render_step_definition_input_port(self):
        return {'file_path': self.file_path}

    def has_file(self):
        if self.get_file() is not None:
            return True
        else:
            return False

    def get_file(self):
        bound_file = self.get_bound_file()
        piped_file = self.get_piped_file()
        if (bound_file is not None) and (piped_file is not None):
            raise Exception('The input port %s has both a bound file %s and a piped file %s.' % (self, bound_file, piped_file))
        elif bound_file is not None:
            return bound_file
        elif piped_file is not None:
            return piped_file
        else:
            return None

    def get_bound_file(self):
        binding = self.get_binding()
        if binding is None:
            return None
        else:
            return binding.get_file()

    def get_binding(self):
        return self.step_request.analysis.get_binding(port_name=self.name, step_name=self.step_request.name)

    def get_piped_file(self):
        data_pipe = self.get_data_pipe()
        if data_pipe is None:
            return None
        else: 
            return data_pipe.get_file()

    def get_data_pipe(self):
        return self.step_request.analysis.get_data_pipe_by_destination_port_name(
            port_name=self.name, step_name=self.step_request.name)

class RequestDataBinding(MutableModel, AnalysisAppBaseModel):
    _class_name = ('request_data_binding', 'request_data_bindings')

    file = models.ForeignKey('File')
    destination = models.ForeignKey('RequestDataBindingPortIdentifier')

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

    def _render_step_definition_data_bindings(self, step_request):
        port = step_request._get_input_port(self.destination.port)
        return {
            'file': self.file.to_obj(),
            'input_port': port._render_step_definition_input_port()
            }

class RequestDataPipe(MutableModel, AnalysisAppBaseModel):
    _class_name = ('request_data_pipe', 'request_data_pipes')

    source = models.ForeignKey('RequestDataPipeSourcePortIdentifier')
    destination = models.ForeignKey('RequestDataPipeDestinationPortIdentifier')

    def get_file(self):
        # TODO
        return None

class PortIdentifier(MutableModel, AnalysisAppBaseModel):
    step = models.CharField(max_length = 256)
    port = models.CharField(max_length = 256)

    class Meta:
        abstract = True

class RequestDataBindingPortIdentifier(PortIdentifier):
    _class_name = ('request_data_binding_port_identifier', 'request_data_binding_port_identifiers')

class RequestDataPipeSourcePortIdentifier(PortIdentifier):
    _class_name = ('request_data_pipe_source_port_identifier', 'request_data_pipe_source_port_identifiers')

class RequestDataPipeDestinationPortIdentifier(PortIdentifier):
    _class_name = ('request_data_pipe_destination_port_identifier', 'request_data_pipe_destination_port_identifiers')
