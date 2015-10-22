from analysis.models.common import AnalysisAppBaseModel
from analysis.models.files import DataObject
from analysis.models.step_definitions import StepDefinition, StepDefinitionOutputPort
from analysis.models.step_runs import StepRun
from analysis.models.template_helper import StepTemplateHelper
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import models
from immutable.models import MutableModel
import jsonfield


"""
This module contains RunRequests and other classes related to
receiving a request for analysis from a user.
"""


class RunRequest(MutableModel, AnalysisAppBaseModel):

    _class_name = ('run_request', 'run_requests')

    FOREIGN_KEY_CHILDREN = ['workflows']
    JSON_FIELDS = ['constants']

    requester = models.CharField(max_length = 100)
    constants = jsonfield.JSONField(null=True)
    are_results_complete = models.BooleanField(default=False)

    @classmethod
    def update_and_run(cls):
        cls.update_all_statuses()

    @classmethod
    def update_and_dry_run(cls):
        cls.update_all_statuses()

    @classmethod
    def update_all_statuses(cls):
        for run_request in cls.objects.filter(are_results_complete=False):
            run_request._update_status()
            run_request.save()

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

    _class_name = ('workflow', 'workflows')

    FOREIGN_KEY_CHILDREN = ['steps', 'data_bindings', 'data_pipes']
    JSON_FIELDS = ['constants']

    name = models.CharField(max_length = 256, null=True) # name is used to make results more browsable on a file server
    constants = jsonfield.JSONField(null=True)
    run_request = models.ForeignKey('RunRequest', related_name='workflows', null=True)
    are_results_complete = models.BooleanField(default=False)
    # steps: Step foreign key
    # data_bindings: RequestDataBinding foreign key
    # data_pipes: RequestDataPipe foreign key

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

"""
class AbstractInputSetManager:
    def __init__(self, step):
        self.step = step

class ForLoopBeginInputSetManager:
    pass

class ForLoopEndInputSetManager:
    pass

class NoLoopInputSetManager:
    pass

class InputSetManagerFactory:
    @classmethod
    port_type_count = self._count_port_types(step)
    def get_input_set_manager(cls, step):
        if self._is_for_loop_starting(port_type_count):
            return ForLoopBeginInputSetManager(step)
        elif self._is_for_loop_ending(port_type_count):
            return ForLoopEndFromArrayInputSetManager(step)
        elif self._is_no_loop_start_or_end(port_type_count):
            return NoLoopInputSetManager(step)
        else:
            raise Exception('invalid configuration')

    @classmethod
    def _count_port_types(cls, step):
        count = {
            'scalar2scalar': 0
            'array2array': 0,
            'array2scalar': 0,
            'scalar2array': 0,
        }
        for port in step.input_ports:
            source_is_array = port.get_connector().is_source_an_array()
            destination_is_array = port.get_connector().is_destination_an_array()
            if (source_is_array, destination_is_array) == (False, False):
                count['scalar2scalar'] += 1
            elif (source_is_array, destination_is_array) == (True, True):
                count['array2array'] += 1
            elif (source_is_array, destination_is_array) == (True, False):
                count['array2scalar'] += 1
            elif (source_is_array, destination_is_array) == (False, True):
                count['scalar2array'] += 1
            else:
                raise Exception("Port is invalid % port")
        return count

    @classmethod
    def _is_for_loop_starting(cls, port_type_count):
        # One part is array-to-scalar
        # Any other parts are straight pass-through
        if port_type_count['array2scalar'] == 1 and port_type_count['scalar2array'] == 0:
            return True

    @classmethod
    def _is_for_loop_ending(cls, port_type_count):
        if port_type_count['scalar2array'] == 1 and port_type_count['array2scalar'] == 0:
            return True

    @classmethod
    def _is_no_loop_start_or_end(cls, port_type_count):
        if port_type_count['scalar2array'] == 0 and port_type_count['array2scalar'] == 0:
            return True
"""


class InputSet:
    # Handles the set of inputs needed to create one StepDefinition

    def __init__(self, step):
        self.step = step
        self.inputs = {}

    def add_input(self, destination_port_name, source):
        # Source is a DataObject or an output port
        self.inputs[destination_port_name] = source

    def is_data_ready(self):
        return all([source.is_available() for source in self.inputs.values()])

    def create_step_run_if_new(self):
        step_definition = StepDefinition.create(self.step._render_step_definition(self))
        # Does it have a valid StepRun? Then create it.
        existing_step_run = step_definition.get_step_run()
        if existing_step_run is None:
            StepRun.create({
                    'step_definition': step_definition.to_serializable_obj(),
                    'steps': [self.step.to_serializable_obj()]
                    })
        elif not existing_step_run.has_step(self.step):
            existing_step_run.add_step(self.step)
            
    def get_data_object(self, port_name):
        return self.inputs[port_name].get_data_object()

class OversimplifiedInputSetManager:

    # Only handles the case of a single input in each port with no parallel processing

    def __init__(self, step):
        self.step = step

    def are_step_runs_pending(self):
        # TODO. Oversimplified.
        if step.step_runs.exists():
            return False

    def get_available_input_sets(self):
        # For each Port on current Step (here only one)
        # Get source (StepRun, Port) or DataObject (here only one)
        # For Each source, return a set of data needed to create a StepRun

        # Assuming that each port has only 1 input, not an array

        input_set = InputSet()
        for port in self.step.input_ports.all():
            import pdb; pdb.set_trace()
        ####            input_set.add_input(port.name, port.source)
            pass

        return [input_set]
        



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
    are_results_complete = models.BooleanField(default=False)
    # step_runs: StepRun foreign key

    def __init__(self, *args ,**kwargs):
        super(Step, self).__init__(*args, **kwargs)
        self.input_set_manager = OversimplifiedInputSetManager(self)

    def _update_status(self):
        self._update_existing_step_runs()
        self._update_new_step_runs()
        if self._are_all_step_runs_complete():
            self.update({'are_results_complete': True})

    def _are_all_step_runs_complete(self):
        # are any step_runs yet to be created or any existing step_runs incomplete
        return not (self.input_set_manager._are_step_runs_pending()
                or self.step_runs.filter(are_results_complete=False).exists())

    def _update_existing_step_runs(self):
        for step_run in self.step_runs.filter(are_results_complete=False):
            step_run._update_status()

    def _update_new_step_runs(self):
        for input_set in self.input_set_manager.get_available_input_sets():
            input_set.create_step_run_if_new()

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
        connectors = self.get_bindings

    def get_connectors(self):
        connectors = [c for c in self.get_bindings()] + \
            [c for c in self.get_data_pipes()]

    def get_bindings(self):
        return self.workflow.data_bindings.filter(destination__step=self.name)

    def get_data_pipes(self):
        return self.workflow.data_pipes.filter(destination__step=self.step)

    def _render_step_definition(self, input_set):
        return {
                'input_ports': [port._render_step_definition_input_port(input_set.get_data_object(port.name)) for port in self.input_ports.all()],
                'output_ports': [port._render_step_definition_output_port() for port in self.output_ports.all()],
                'command': self._render_command(),
                'environment': self.get('environment')._render_step_definition_environment()
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

    # Relative path within the working directory where
    # a file will be found after a step executes
    file_name = models.CharField(max_length = 256, null=True)
    glob = models.CharField(max_length = 256, null=True)
    step = models.ForeignKey('Step', related_name='output_ports', null=True)

    def _render_step_definition_output_port(self):
        return {
            'file_name': StepTemplateHelper(self.step).render(self.file_name),
            'glob': StepTemplateHelper(self.step).render(self.glob),
            'is_array': self.is_array
            }


class RequestInputPort(MutableModel, AnalysisAppBaseModel):

    _class_name = ('request_input_port', 'request_input_ports')

    name = models.CharField(max_length = 256)
    # Relative path within the working directory where
    # a file will be copied before a step is executed
    file_name = models.CharField(max_length = 256)
    step = models.ForeignKey('Step', related_name='input_ports', null=True)
    is_array = models.BooleanField(default = False)

    def get_connector(self):
        connector = self._get_binding()
        if connector is None:
            connector = self._get_data_pipe()
        return connector

    def _get_binding(self):
        return self.step.workflow._get_binding(port_name=self.name, step_name=self.step.name)

    def _get_data_pipe(self):
        return self.step.workflow._get_data_pipe(
            port_name=self.name, step_name=self.step.name)

    def _render_step_definition_input_port(self, data_object):
        return {
            'file_name': StepTemplateHelper(self.step).render(self.file_name),
            'is_array': self.is_array,
            'data_object': data_object.to_serializable_obj()
            }


class RequestDataBinding(MutableModel, AnalysisAppBaseModel):

    _class_name = ('request_data_binding', 'request_data_bindings')

    FOREIGN_KEY_CHILDREN = ['data_object', 'destination']

    data_object = models.ForeignKey('DataObject') # File or FileArray
    destination = models.ForeignKey('RequestDataBindingPortIdentifier')
    workflow = models.ForeignKey('Workflow', related_name='data_bindings', null=True)

    def is_data_ready(self):
        self.get_data_object().is_available()

    def get_data_object(self):
        return self.get('data_object', downcast=True)

    def is_source_an_array(self):
        return self.data_object.is_array()

    def is_destination_an_array(self):
        return self.get_destination_step().get_input_port(self.destination.port).is_array()

    def get_destination_step(self):
        self._verify_workflow()
        return self.workflow.get_step(self.destination.step)

    def _verify_workflow(self):
        if not self.workflow.exists():
            raise Exception("No workflow defined for RequestDataBinding %s" % self.to_obj())

    def get_destination_port(self):
        return self.get_destination_step().get_input_port(self.destination.port)

    def _render_step_definition_data_bindings(self, step):
        return {
            'data_object': self.data_object.to_obj(),
            'input_port': self.get_destination_port()._render_step_definition_input_port()
            }


class RequestDataPipe(MutableModel, AnalysisAppBaseModel):

    _class_name = ('request_data_pipe', 'request_data_pipes')

    FOREIGN_KEY_CHILDREN = ['source', 'destination']

    source = models.ForeignKey('RequestDataPipeSourcePortIdentifier')
    destination = models.ForeignKey('RequestDataPipeDestinationPortIdentifier')
    workflow = models.ForeignKey('Workflow', related_name='data_pipes', null=True)

    def get_source_step(self):
        return self.workflow.get_step(self.source.step)

    def get_destination_step(self):
        return self.workflow.get_step(self.destination.step)

    def is_source_an_array(self):
        return self.get_source_step().get_output_port(self.source.port).is_array()

    def is_destination_an_array(self):
        return self.get_destination_step().get_input_port(self.destination.port).is_array()

    def _render_step_definition_data_bindings(self, step):
        port = step.get_input_port(self.destination.port)
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

