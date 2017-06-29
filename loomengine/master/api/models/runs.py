from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned, ValidationError
from django.db import models
from django.dispatch import receiver
from django.utils import timezone
from mptt.models import MPTTModel, TreeForeignKey
import jsonfield

from .base import BaseModel
from api import get_setting
from api import async
from api.exceptions import *
from api.models import uuidstr
from api.models import validators
from api.models.data_objects import DataObject
from api.models.input_output_nodes import InputOutputNode
from api.models.input_manager import InputManager
from api.models.tasks import Task, TaskInput, TaskOutput, TaskAlreadyExistsException
from api.models.templates import Template
from api.exceptions import ConcurrentModificationError


"""
This module defines Run and other classes related to
running an analysis
"""


class RunAlreadyClaimedForPostprocessingException(Exception):
    pass


class Run(MPTTModel, BaseModel):
    """AbstractWorkflowRun represents the process of executing a Workflow on
    a particular set of inputs. The workflow may be either a Step or a
    Workflow composed of one or more Steps.
    """

    NAME_FIELD = 'name'
    ID_FIELD = 'uuid'

    uuid = models.CharField(default=uuidstr, editable=False,
                            unique=True, max_length=255)
    name = models.CharField(max_length=255)
    is_leaf = models.BooleanField()
    datetime_created = models.DateTimeField(default=timezone.now,
                                            editable=False)
    datetime_finished = models.DateTimeField(null=True, blank=True)
    environment = jsonfield.JSONField(
        blank=True,
        validators=[validators.validate_environment])
    resources = jsonfield.JSONField(
        blank=True,
        validators=[validators.validate_resources])
    parent = TreeForeignKey('self', null=True, blank=True,
                            related_name='steps', db_index=True,
                            on_delete=models.CASCADE)
    template = models.ForeignKey('Template',
                                 related_name='runs',
                                 on_delete=models.PROTECT,
                                 null=True, # For testing only
                                 blank=True)
    postprocessing_status = models.CharField(
        max_length=255,
        default='not_started',
        choices=(('not_started', 'Not Started'),
                 ('in_progress', 'In Progress'),
                 ('complete', 'Complete'),
                 ('failed', 'Failed'))
    )

    status_is_finished = models.BooleanField(default=False)
    status_is_failed = models.BooleanField(default=False)
    status_is_killed = models.BooleanField(default=False)
    status_is_running = models.BooleanField(default=False)
    status_is_waiting = models.BooleanField(default=True)

    # For leaf nodes only
    command = models.TextField(blank=True)
    interpreter = models.CharField(max_length=1024, blank=True)

    @property
    def status(self):
        if self.status_is_failed:
            return 'Failed'
        elif self.status_is_finished:
            return 'Finished'
        elif self.status_is_killed:
            return 'Killed'
        elif self.status_is_running:
            return 'Running'
        elif self.status_is_waiting:
            return 'Waiting'
        else:
            return 'Unknown'

    def get_input(self, channel):
        inputs = [i for i in self.inputs.filter(channel=channel)]
        assert len(inputs) == 1, 'missing input for channel %s' % channel
        return inputs[0]

    def get_output(self, channel):
        outputs = [o for o in self.outputs.filter(channel=channel)]
        assert len(outputs) == 1, 'missing output for channel %s' % channel
        return outputs[0]

    def get_topmost_run(self):
        try:
            self.run_request
        except ObjectDoesNotExist:
            return self.parent.get_topmost_run()
        return self

    def is_topmost_run(self):
        try:
            self.run_request
        except ObjectDoesNotExist:
            return False
        return True

    def set_status_is_finished(self):
        self.setattrs_and_save_with_retries(
            {'status_is_running': False,
             'status_is_waiting': False,
             'status_is_finished': True})
        self.add_timepoint("Run %s@%s finished successfully" %
                           (self.name, self.uuid))
        if self.parent:
            self.parent.add_timepoint(
                "Child Run %s@%s finished successfully" % (self.name, self.uuid))
            if self.parent._are_children_finished():
                self.parent.set_status_is_finished()

    def _are_children_finished(self):
        return all([step.status_is_finished for step in self.steps.all()])

    @classmethod
    def create_from_template(cls, template, parent=None):
        if template.is_leaf:
            run = Run.objects.create(
                template=template,
                is_leaf=template.is_leaf,
                name=template.name,
                command=template.command,
                interpreter=template.interpreter,
                parent=parent)
        else:
            run = Run.objects.create(template=template,
                                     is_leaf=template.is_leaf,
                                     name=template.name,
                                     parent=parent)

        run.add_timepoint("Run %s@%s was created" % (run.name, run.uuid))
        if run.parent:
            run.parent.add_timepoint("Child run %s@%s was created" % (
                run.name, run.uuid))

        return run

    def _connect_input_to_parent(self, input):
        if self.parent:
            try:
                parent_connector = self.parent.connectors.get(
                    channel=input.channel)
                parent_connector.connect(input)
            except ObjectDoesNotExist:
                self.parent._create_connector(input, is_source=False)

    def _connect_input_to_requested_input(self, input):
        try:
            requested_input = self.requested_inputs.get(channel=input.channel)
        except ObjectDoesNotExist:
            return
        requested_input.connect(input)

    def _connect_fixed_inputs(self):
        for input in self.inputs.all():
            self._connect_input_to_template(input)


    def _has_requested_input(self, channel):
        try:
            self.requested_inputs.get(channel=channel)
            return True
        except ObjectDoesNotExist:
            return False

    def _has_parent_connector_with_source(self, channel):
        if self.parent is None:
            return False
        try:
            connector = self.parent.connectors.get(channel=channel)
        except ObjectDoesNotExist:
            return False
        return connector.has_source
        
    def _connect_input_to_template(self, input):
        # Do not connect if parent connector.has_source
        if self._has_parent_connector_with_source(input.channel):
            return
        
        # Do not connect if RequestedInput exists
        if self._has_requested_input(input.channel):                
            return

        template_input = self.template.inputs.get(channel=input.channel)
        if template_input.data_node is None:
            raise ValidationError("No input data available on channel %s" % input.channel)
        template_input.data_node.clone(seed=input.data_node)

    def _connect_output_to_parent(self, output):
        if not self.parent:
            return
        try:
            parent_connector = self.parent.connectors.get(
                channel=output.channel)
            if parent_connector.has_source:
                raise ValidationError(
                    'Channel "%s" has more than one source' % output.channel)
            parent_connector.connect(output)
        except ObjectDoesNotExist:
            self.parent._create_connector(output, is_source=True)

    def fail(self, message, detail=''):
        self.setattrs_and_save_with_retries({
            'status_is_failed': True,
            'status_is_running': False,
            'status_is_waiting': False})
        self.add_timepoint(message, detail=detail, is_error=True)
        if self.parent:
            self.parent.fail('Run %s failed' % self.uuid, detail=detail)
        else:
            self.kill(detail)

    def kill(self, kill_message):
        if self.status_is_finished:
            # Don't kill successfully completed runs
            return
        self.add_timepoint('Run killed', detail=kill_message, is_error=True)
        self.setattrs_and_save_with_retries(
            {'status_is_killed': True,
             'status_is_running': False,
             'status_is_waiting': False})
        for step in self.steps.all():
            step.kill(kill_message)
        for task in self.tasks.all():
            task.kill(kill_message)

    def set_running_status(self):
        if self.status_is_running and not self.status_is_waiting:
            return
        self.setattrs_and_save_with_retries({
            'status_is_running': True,
            'status_is_waiting': False})
        if self.parent:
            self.parent.set_running_status()

    def add_timepoint(self, message, detail='', is_error=False):
        timepoint = RunTimepoint.objects.create(
            message=message, run=self, detail=detail, is_error=is_error)

    def _claim_for_postprocessing(self):
        # There are two paths to get Run.postprocess():
        # 1. user calls "run" on a template that is already ready, and
        #    run is postprocessed right away.
        # 2. user calls "run" on a template that is not ready, and run
        #    is postprocessed only after template is ready.
        # There is a chance of both paths being executed, so we have to
        # protect against that

        assert self.template.postprocessing_status == 'complete', \
            'Template not ready, cannot postprocess run %s' % run.uuid

        self.postprocessing_status = 'in_progress'
        try:
            self.save()
        except ConcurrentModificationError:
            # The "save" method is overridden in our base model to have concurrency
            # protection. This error implies that the run was modified since
            # it was loaded.
            # Let's make sure it's being postprocessed by another
            # process, and we will defer to that process.
            run = Run.objects.get(uuid=run_uuid)
            if run.postprocessing_status != 'not_started':
                # Good, looks like another worker is postprocessing this run,
                # so we're done here
                raise RunAlreadyClaimedForPostprocessingException
            else:
                # Don't know why this run was modified. Raise an error
                raise Exception('Postprocessing failed due to unexpected '\
                                'concurrent modification')

    @classmethod
    def postprocess(cls, run_uuid):
        run = Run.objects.get(uuid=run_uuid)
        if not run.template.postprocessing_status == 'complete':
            # Never mind, we'll postprocess when the template is ready
            return

        if run.postprocessing_status == 'complete':
            # Nothing more to do
            return

        try:
            run._claim_for_postprocessing()
        except RunAlreadyClaimedForPostprocessingException:
            return

        try:
            for step in run.steps.all():
                step.initialize_steps()
                async.postprocess_run(step.uuid)

            run._connect_fixed_inputs()
            run.setattrs_and_save_with_retries({
                'resources': run.template.resources,
                'environment': run.template.environment})
            run._push_all_inputs()
            run.setattrs_and_save_with_retries({
                'postprocessing_status': 'complete'})

        except Exception as e:
            run.setattrs_and_save_with_retries({'postprocessing_status': 'failed'})
            run.fail('Postprocessing failed', detail=str(e))
            raise

    def initialize_inputs(self):
        seen = set()
        for input in self.template.inputs.all():
            assert input.channel not in seen, \
                'Encountered multiple inputs for channel "%s"' \
                % input.channel
            seen.add(input.channel)

            run_input = RunInput.objects.create(
                run=self,
                channel=input.channel,
                type=input.type,
                group=input.group,
                mode=input.mode)

            # Create a connector on the current Run so that
            # children can connect on this channel
            self._create_connector(run_input, is_source=True)
            self._connect_input_to_parent(run_input)
            self._connect_input_to_requested_input(run_input)

            # Do not connect to template data (fixed inputs)
            # yet, because siblings are still initializing
            # so we don't know if defalt data will be overridden.
                
    def initialize_outputs(self):
        if not self.template.outputs:
            return
        for output in self.template.outputs:
            kwargs = {'run': self,
                      'type': output.get('type'),
                      'channel': output.get('channel'),
                      'source': output.get('source'),
                      'parser': output.get('parser')
            }
            if output.get('mode'):
                kwargs.update({'mode': output.get('mode')})
            run_output = RunOutput.objects.create(**kwargs)

            # This takes effect only if the WorkflowRun has a parent
            self._connect_output_to_parent(run_output)

            # Create a connector on the current Run so that
            # children can connect on this channel
            if not self.is_leaf:
                self._create_connector(run_output, is_source=False)

            # If this is a leaf node but has no parents, initialize the
            # DataNode so it will be available for connection by the TaskOutput
            if not run_output.data_node:
                run_output.initialize_data_node()

    def initialize_steps(self):
        """This is executed by the parent to ensure that all siblings are initialized
        before any are postprocessed.
        """
        if self.is_leaf:
            return
        for step in self.template.steps.all():
            child_run = self.create_from_template(step, parent=self)
            child_run.initialize_inputs()
            child_run.initialize_outputs()

    def _create_connector(self, io_node, is_source):
        if self.is_leaf:
            return
        try:
            connector = RunConnectorNode.objects.create(
                run=self,
                channel=io_node.channel,
                type=io_node.type,
                has_source=is_source
            )
        except ValidationError:
            # Connector already exists. Just use it.
            connector = self.connectors.get(channel=io_node.channel)

            # But first make sure it doesn't have multiple data sources
            if is_source:
                if connector.has_source:
                    raise ValidationError('Channel "%s" has more than one source' % io_node.channel_name)
                else:
                    connector.has_source = True
                    connector.save()
        connector.connect(io_node)

    def _push_all_inputs(self):
        if get_setting('TEST_NO_PUSH_INPUTS_ON_RUN_CREATION'):
            return
        if self.inputs.exists():
            for input in self.inputs.all():
                self.push(input.channel, [])
        elif self.is_leaf:
            # Special case: No inputs on leaf node
            self._push_input_set([])

    def push(self, channel, data_path):
        """Called when new data is available at the given data_path 
        on the given channel. This will trigger creation of new tasks if 1)
        other input data for those tasks is available, and 2) the task with
        that data_path was not already created previously.
        """
        if get_setting('TEST_NO_CREATE_TASK'):
            return
        if not self.is_leaf:
            return
        for input_set in InputManager(self.inputs.all(), channel, data_path)\
            .get_input_sets():
            self._push_input_set(input_set)

    def _push_input_set(self, input_set):
        try:
            task = Task.create_from_input_set(input_set, self)
            async.run_task(task.uuid)
        except TaskAlreadyExistsException:
            pass


class RunTimepoint(BaseModel):

    run = models.ForeignKey(
        'Run',
	related_name='timepoints',
	on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=timezone.now,
                                     editable=False)
    message = models.CharField(max_length=255)
    detail = models.TextField(blank=True)
    is_error = models.BooleanField(default=False)


class RequestedInput(InputOutputNode):

    class Meta:
        unique_together = (("run", "channel"),)

    run = models.ForeignKey(
        'Run',
        related_name='requested_inputs',
        on_delete=models.CASCADE)


class RunInput(InputOutputNode):

    class Meta:
        unique_together = (("run", "channel"),)

    run = models.ForeignKey('Run',
                            related_name='inputs',
                            on_delete=models.CASCADE,
                            null=True, # for testing only
                            blank=True)
    mode = models.CharField(max_length=255, blank=True)
    group = models.IntegerField(null=True, blank=True)

    def is_ready(self, data_path=None):
        if self.data_node:
            return self.data_node.is_ready(data_path=data_path)
        else:
            return False


class RunOutput(InputOutputNode):

    class Meta:
        unique_together = (("run", "channel"),)

    run = models.ForeignKey('Run',
                            related_name='outputs',
                            on_delete=models.CASCADE,
                            null=True, # for testing only
                            blank=True)
    mode = models.CharField(max_length=255, blank=True)
    source = jsonfield.JSONField(blank=True)
    parser = jsonfield.JSONField(
	validators=[validators.OutputParserValidator.validate_output_parser],
        blank=True)


class RunConnectorNode(InputOutputNode):
    # A connector resides in a workflow. All inputs/outputs on the workflow
    # connect internally to connectors, and all inputs/outputs on the
    # nested steps connect externally to connectors on their parent workflow.
    # The primary purpose of this object is to eliminate directly connecting
    # input/output nodes of siblings since their creation order is uncertain.
    # Instead, connections between siblings always pass through a connector
    # in the parent workflow.

    has_source = models.BooleanField(default=False)
    run = models.ForeignKey('Run',
                            related_name='connectors',
                            on_delete=models.CASCADE)

    class Meta:
        unique_together = (("run", "channel"),)


class TaskInputManager(object):
    """Manages the set of nodes acting as inputs for one step.
    Each input node may have more than one DataObject,
    and DataObjects may arrive to the node at different times.
    """
    def __init__(self, input_nodes, channel, index):
        self.input_nodes = input_nodes
        self.channel = channel
        self.index = index

    def get_ready_input_sets(self):
        """New data is available at the given channel and index. See whether
        any new tasks can be created with this data.
        """
        for input_node in self.input_nodes:
            if not input_node.is_ready():
                return []
        return [InputSet(self.input_nodes, self.index)]


class InputItem(object):
    """Info needed by the Task to construct a TaskInput
    """

    def __init__(self, input_node, index):
        self.data_object = input_node.get_data_object(index)
        self.type = self.data_object.type
        self.channel = input_node.channel


class InputSet(object):
    """A TaskInputManager can produce one or more InputSets, where each
    InputSet corresponds to a single Task.
    """

    def __init__(self, input_nodes, index):
        self.index = index
        self.input_items = [InputItem(i, index) for i in input_nodes]

    def __iter__(self):
        return self.input_items.__iter__()
