from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import models
import jsonfield

from .common import AnalysisAppBaseModel
from .files import DataObject
from .step_definitions import StepDefinition, StepDefinitionOutputPort
from .template_helper import StepTemplateHelper
from immutable.models import MutableModel


"""
This module contains RequestSubmissions and other classes related to
receiving a request for analysis from a user.
"""


class RequestSubmission(MutableModel, AnalysisAppBaseModel):
    _class_name = ('request_submission', 'request_submissions')
    JSON_FIELDS = ['constants']

    requester = models.CharField(max_length = 100)
    constants = jsonfield.JSONField(null=True)

    def get_workflows(self):
        return self.workflows.all()

    def is_complete(self):
        # Returns True if all workflows are finished
        for workflow in self.workflows.all():
            if not workflow.is_complete():
                return False
        return True

    @classmethod
    def get_sorted(cls, count=None):
        request_submissions = cls.objects.order_by('datetime_created').reverse()
        if count is not None:
            if request_submissions.count() > count:
                request_submissions = request_submissions[:count]
        return [r for r in request_submissions]

class Workflow(MutableModel, AnalysisAppBaseModel):
    FOREIGN_KEY_CHILDREN = ['steps', 'data_bindings', 'data_pipes']
    JSON_FIELDS = ['constants']

    _class_name = ('workflow', 'workflows')
    name = models.CharField(max_length = 256, null=True) # name is used to make results more browsable on a file server
    constants = jsonfield.JSONField(null=True)
    request_submission = models.ForeignKey('RequestSubmission', related_name='workflows', null=True)
    # steps: Step foreign key
    # data_bindings: RequestDataBinding foreign key
    # data_pipes: RequestDataPipe foreign key

    def get_steps_ready_to_run(self):
        steps = []
        for step in self.steps.all():
            if step.is_ready() and not step.is_complete():
                steps.append(step)
        return steps

    def get_step(self, name):
        return self.steps.get(name=name)

    def get_binding(self, step_name, port_name):
        bindings = self.data_bindings.filter(destination__step=step_name, destination__port=port_name)
        if bindings.count() > 1:
            raise Exception("Multiple bindings were found on workflow %s for step %s, port %s" % (self, step_name, port_name))
        elif bindings.count() == 1:
            return bindings.first()
        else:
            return None

    def _get_bindings_by_step(self, step_name):
        return self.data_bindings.filter(destination__step=step_name)

    def _get_data_pipes_by_step(self, step_name):
        return self.data_pipes.filter(destination__step=step_name)
        
    def get_data_pipe_by_destination_port_name(self, step_name, port_name):
        data_pipes = self.data_pipes.filter(destination__step=step_name, destination__port=port_name)
        if data_pipes.count() > 1:
            raise Exception('Multiple data_pipes were found on workflow %s for step %s, port %s.' % (self, step_name, port_name))
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
        port = step._get_input_port(destination.port)
        if port is None:
            raise ValidationError("No port named %s on step %s" % (destination.port, destination.step))

    def _validate_source(self, source):
        step = self.get_step(source.step)
        if step is None:
            raise ValidationError("No step named %s" % source.step)
        port = step._get_output_port(source.port)
        if port is None:
            raise ValidationError("No port named %s on step %s" % (source.port, source.step))

class Step(MutableModel, AnalysisAppBaseModel):
    _class_name = ('step', 'steps')
    FOREIGN_KEY_CHILDREN = ['environment', 'resources', 'step_definition', 'step_run', 'input_ports', 'output_ports']
    JSON_FIELDS = ['constants']
    name = models.CharField(max_length = 256)
    command = models.CharField(max_length = 256)
    constants = jsonfield.JSONField(null=True)
    environment = models.ForeignKey('RequestEnvironment')
    resources = models.ForeignKey('RequestResourceSet')
    workflow = models.ForeignKey('Workflow', null=True, related_name='steps')
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
        return self.step_run

    def _create_step_definition(self):
        return StepDefinition.create(self._render_step_definition())

    def _render_step_definition(self):
        step_definition = {
            'template': {
                'command': self._render_command(),
                'environment': self.get('environment')._render_step_definition_environment(),
                'input_ports': [port._render_step_definition_input_port() for port in self.input_ports.all()],
                'output_ports': [port._render_step_definition_output_port() for port in self.output_ports.all()],
                },
            'data_bindings': self._get_step_definition_data_bindings(),
            }
        return step_definition

    def _render_command(self):
        return StepTemplateHelper(self).render(self.command)

    def _get_step_definition_data_bindings(self):
        data_bindings = [binding._render_step_definition_data_bindings(self) for binding in self.workflow._get_bindings_by_step(self.name)]
        data_bindings.extend([data_pipe._render_step_definition_data_bindings(self) for data_pipe in self.workflow._get_data_pipes_by_step(self.name)])
        return data_bindings

    def _get_input_port(self, name):
        try:
            return self.input_ports.get(name=name)
        except ObjectDoesNotExist:
            return None

    def _get_output_port(self, name):
        try:
            return self.output_ports.get(name=name)
        except ObjectDoesNotExist:
            return None

    def is_ready(self):
        if self.has_run():
            return False
        return self._is_input_data_ready()

    def is_complete(self):
        if self.has_run():
            return self.step_run.is_complete
        else:
            return False

    def _is_input_data_ready(self):
        # Returns True if all input files are avaialble
        return all([port.is_input_data_ready() for port in self.input_ports.all()])

    def get_output_data_object(self, port_name):
        if not self.has_run():
            return None
        request_port = self._get_output_port(port_name)
        result_port = request_port.get_step_definition_output_port()
        return self.step_run.get_output_data_object(result_port)

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

    # Relative path within the working directory where
    # a file will be found after a step executes
    file_path = models.CharField(max_length = 256)
    step = models.ForeignKey('Step', related_name='output_ports', null=True)

    def get_step_definition_output_port(self):
        return StepDefinitionOutputPort.get_by_definition(
            self._render_step_definition_output_port()
            )

    def _render_step_definition_output_port(self):
        return {
            'name': self.name,
            'file_path': StepTemplateHelper(self.step).render(self.file_path)
            }

class RequestInputPort(MutableModel, AnalysisAppBaseModel):
    _class_name = ('request_input_port', 'request_input_ports')

    name = models.CharField(max_length = 256)
    # Relative path within the working directory where
    # a file will be copied before a step is executed
    file_path = models.CharField(max_length = 256)
    step = models.ForeignKey('Step', related_name='input_ports', null=True)
    is_array = models.BooleanField(default = False)

    def get_binding(self):
        return self.step.workflow.get_binding(port_name=self.name, step_name=self.step.name)

    def get_data_pipe(self):
        return self.step.workflow.get_data_pipe_by_destination_port_name(
            port_name=self.name, step_name=self.step.name)

    def has_data_object(self):
        if self.get_input_data() is None:
            return False
        else:
            return True

    def is_input_data_ready(self):
        input_data = self.get_input_data()
        if input_data is None:
            return False
        else:
            return input_data.is_available()

    def get_input_data(self):
        bound_input_data = self.get_bound_input_data()
        piped_input_data = self.get_piped_input_data()
        if (bound_input_data is not None) and (piped_input_data is not None):
            raise Exception('The input port %s has both bound data %s and piped data %s.' % (self, bound_input_data, piped_input_data))
        elif bound_input_data is not None:
            return bound_input_data
        elif piped_input_data is not None:
            return piped_input_data
        else:
            return None

    def get_bound_input_data(self):
        binding = self.get_binding()
        if binding is None:
            return None
        else:
            return binding.get_data_object()

    def get_piped_input_data(self):
        data_pipe = self.get_data_pipe()
        if data_pipe is None:
            return None
        else: 
            return data_pipe.get_data_object()

    def _render_step_definition_input_port(self):
        return {
            'name': self.name,
            'file_path': StepTemplateHelper(self.step).render(self.file_path)
            }

class RequestDataBinding(MutableModel, AnalysisAppBaseModel):
    _class_name = ('request_data_binding', 'request_data_bindings')
    FOREIGN_KEY_CHILDREN = ['data_object', 'destination']
    data_object = models.ForeignKey('DataObject') # File or FileArray
    destination = models.ForeignKey('RequestDataBindingPortIdentifier')
    workflow = models.ForeignKey('Workflow', related_name='data_bindings', null=True)

    def is_ready(self):
        # Returns True if the input file or file array is available
        if not self.data_object.exists():
            return False
        else:
            return data_object.is_available()

    def get_data_object(self):
        return self.get('data_object') # Downcast

    def _render_step_definition_data_bindings(self, step):
        port = step._get_input_port(self.destination.port)
        return {
            'data_object': self.data_object.to_obj(),
            'input_port': port._render_step_definition_input_port()
            }

class RequestDataPipe(MutableModel, AnalysisAppBaseModel):
    _class_name = ('request_data_pipe', 'request_data_pipes')
    FOREIGN_KEY_CHILDREN = ['source', 'destination']
    source = models.ForeignKey('RequestDataPipeSourcePortIdentifier')
    destination = models.ForeignKey('RequestDataPipeDestinationPortIdentifier')
    workflow = models.ForeignKey('Workflow', related_name='data_pipes', null=True)

    def get_data_object(self):
        step = self.workflow.get_step(self.source.step)
        return step.get_output_data_object(self.source.port)

    def _render_step_definition_data_bindings(self, step):
        port = step._get_input_port(self.destination.port)
        return {
            'data_object': self.get_data_object().to_obj(),
            'input_port': port._render_step_definition_input_port()
            }

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
