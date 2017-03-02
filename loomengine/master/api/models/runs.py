from django.db import models, IntegrityError
from django.dispatch import receiver
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
import jsonfield

from .base import BaseModel
from api import get_setting
from api.exceptions import *
from api.models.input_output_nodes import InputOutputNode, InputNodeSet
from api.models.data_objects import DataObject
from api.models.tasks import Task, TaskInput, TaskOutput
from api.models import uuidstr
from api import tasks

"""
This module defines WorkflowRun and other classes related to
running an analysis
"""

class WorkflowRunManager(object):

    def __init__(self, run):
        assert run.type == 'workflow', \
            'Bad run type--expected "workflow" but found "%s"' % run.type
        self.run = run

    def get_inputs(self):
        return self.run.workflowrun.inputs

    def get_outputs(self):
        return self.run.workflowrun.outputs

    def get_tasks(self):
        raise Exception('No tasks on run of type "workflow"')

    def kill(self, kill_message):
        return self.run.workflowrun._kill(kill_message)
    

class StepRunManager(object):

    def __init__(self, run):
        assert run.type == 'step', \
            'Bad run type--expected "step" but found "%s"' % run.type
        self.run = run

    def get_inputs(self):
        return self.run.steprun.inputs

    def get_outputs(self):
        return self.run.steprun.outputs

    def get_tasks(self):
        return self.run.steprun.tasks

    def kill(self, kill_message):
        return self.run.steprun._kill(kill_message)


class Run(BaseModel):
    """AbstractWorkflowRun represents the process of executing a Workflow on 
    a particular set of inputs. The workflow may be either a Step or a 
    Workflow composed of one or more Steps.
    """

    NAME_FIELD = 'template__name'

    _MANAGER_CLASSES = {
        'step': StepRunManager,
        'workflow': WorkflowRunManager
    }
    uuid = models.CharField(default=uuidstr, editable=False,
                            unique=True, max_length=255)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=255,
                            choices = (('step', 'Step'),
                                       ('workflow', 'Workflow')))
    datetime_created = models.DateTimeField(default=timezone.now,
                                            editable=False)
    datetime_finished = models.DateTimeField(null=True)
    parent = models.ForeignKey('WorkflowRun',
                               related_name='steps',
                               null=True,
                               on_delete=models.CASCADE)
    template = models.ForeignKey('Template',
                                 related_name='runs',
                                 on_delete=models.PROTECT,
                                 null=True) # For testing only
    postprocessing_status = models.CharField(
        max_length=255,
        default='saving',
        choices=(('waiting', 'Waiting'),
                 ('in_progress', 'In progress'),
                 ('done', 'Done'),
                 ('error', 'Error'))
    )

    status_is_finished = models.BooleanField(default=False)
    status_is_failed = models.BooleanField(default=False)
    status_is_killed = models.BooleanField(default=False)
    status_is_running = models.BooleanField(default=True)
    # True if ANY input ports have not received all inputs
    # status_waiting_for_inputs = models.BooleanField(default=False)

    @property
    def status(self):
        if self.status_is_failed:
            return 'Failed'
        elif self.status_is_killed:
            return 'Killed'
        elif self.status_is_running:
            return 'Running'
        elif self.status_is_finished:
            return 'Finished'
        else:
            return 'Unknown'
    
    @classmethod
    def _get_manager_class(cls, type):
        return cls._MANAGER_CLASSES[type]

    def _get_manager(self):
        return self._get_manager_class(self.type)(self)

    @property
    def inputs(self):
        return self._get_manager().get_inputs()
    
    @property
    def outputs(self):
        return self._get_manager().get_outputs()

    @property
    def tasks(self):
        return self._get_manager().get_tasks()

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

    @classmethod
    def create_from_template(cls, template, parent=None, run_request=None):
        if template.type == 'step':
            run = StepRun.objects.create(
                template=template,
                name=template.name,
                type=template.type,
                command=template.step.command,
                interpreter=template.step.interpreter,
                interpreter_options = template.step.interpreter_options,
                parent=parent).run_ptr
            if run_request:
                run_request.run = run
                run_request.save()
            # Postprocess run only if postprocessing of template is done.
            # It is possible for the run to be completed before the template
            # is postprocessing_status=='done'. In that case, the run postprocessing
            # will be triggered by the template postprocessing when the template
            # is ready
            if template.postprocessing_status == 'done':
                tasks.postprocess_step_run(run.uuid)
        else:
            assert template.type == 'workflow', \
                'Invalid template type "%s"' % template.type
            run = WorkflowRun.objects.create(template=template,
                                             run_request=run_request,
                                             name=template.name,
                                             type=template.type,
                                             parent=parent).run_ptr
            if run_request:
                run_request.run = run
                run_request.save()
            # Postprocess run only if postprocessing of template is done.
            # It is possible for the run to be completed before the template
            # is postprocessing_status==ready. In that case, the run postprocessing
            # will be triggered by the template postprocessing when the template
            # is ready
            if template.postprocessing_status == 'done':
                tasks.postprocess_workflow_run(run.uuid)

        run.add_timepoint("Run %s@%s was created" % (run.name, run.uuid))
        if run.parent:
            run.parent.add_timepoint("Child run %s@%s was created" % (
                run.name, run.uuid))
        return run.downcast()

    def downcast(self):
        if self.type == 'step':
            try:
                return self.steprun
            except AttributeError:
                # already downcast
                return self
        else:
            assert self.type == 'workflow', \
                'cannot downcast unknown type "%s"' % self.type
            try:
                return self.workflowrun
            except AttributeError:
                # already downcast
                return self

    def _connect_input_to_parent(self, input):
        if self.parent:
            try:
                parent_connector = self.parent.connectors.get(channel=input.channel)
                parent_connector.connect(input)
            except ObjectDoesNotExist:
                self.parent.downcast()._create_connector(input)

    def _connect_input_to_run_request(self, input):
        try:
            run_request = self.run_request
        except ObjectDoesNotExist:
            # No run request here
            return
        run_request_input = run_request.inputs.get(channel=input.channel)
        run_request_input.connect(input)

    def _connect_output_to_parent(self, output):
        if self.parent:
            try:
                parent_connector = self.parent.connectors.get(channel=output.channel)
                parent_connector.connect(output)
            except ObjectDoesNotExist:
                self.parent.downcast()._create_connector(output)

    def fail(self, message, detail=''):
        self.status_is_failed = True
        self.status_is_running = False
        self.save()
        self.add_timepoint(message, detail=detail, is_error=True)
        if self.parent:
            self.parent.fail('Run %s failed' % self.uuid, detail=detail)
        else:
            self.kill(detail)

    def kill(self, kill_message):
        return self._get_manager().kill(kill_message)

    def add_timepoint(self, message, detail='', is_error=False):
        timepoint = RunTimepoint.objects.create(
            message=message, run=self, detail=detail, is_error=is_error)
        timepoint.save()


class RunTimepoint(BaseModel):
    run = models.ForeignKey(
        'Run',
	related_name='timepoints',
	on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=timezone.now,
                                     editable=False)
    message = models.CharField(max_length=255)
    detail = models.TextField(null=True, blank=True)
    is_error = models.BooleanField(default=False)
    

class WorkflowRun(Run):

    # True if ANY steps are running
    # status_running = models.BooleanField(default=False)

    # status_steps_waiting = models.IntegerField(default=0)
    # status_steps_running = models.IntegerField(default=0)
    # status_steps_finished = models.IntegerField(default=0)

    def add_step(self, step_run):
        step_run.parent = self
        step_run.save()

    @classmethod
    def postprocess(cls, run_uuid):

        # There are two paths to get here:
        # 1. user calls "run" on a template that is already ready, and
        #    run is postprocessed right away.
        # 2. user calls "run" on a template that is not ready, and run
        #    is postprocessed only after template is ready.

        run = WorkflowRun.objects.get(uuid=run_uuid)

        # Don't postprocess twice
        # The "save" method is overridden in our base model to have concurrency
        # protection

        if run.postprocessing_status == 'done' \
           or run.postprocessing_status == 'in_progress':
            return
        
        run.postprocessing_status = 'in_progress'
        try:
            run.save()
        except ConcurrentModificationError:
            # Already being processed. Nothing to do.
            return

        assert run.template.postprocessing_status == 'done', \
            'Template not ready, cannot postprocess run %s' % run.uuid

        try:
            run._initialize_inputs()
            run._initialize_outputs()
            run._initialize_steps()

            run.postprocessing_status = 'done'
            run.save()
        except Exception as e:
            run.postprocessing_status = 'error'
            run.save()
            raise e
        
    def _initialize_inputs(self):
        run = self.downcast()
        visited_channels = set()
        if run.template.inputs:
            for input in run.template.inputs:
                assert input.get('channel') not in visited_channels, \
                    'Encountered multiple inputs for channel "%s"' \
                    % input.get('channel')
                visited_channels.add(input.get('channel'))

                run_input = WorkflowRunInput.objects.create(
                    workflow_run=run,
                    channel=input.get('channel'),
                    type=input.get('type'))

                # One of these two should always take effect. The other is ignored.
                self._connect_input_to_parent(run_input)
                self._connect_input_to_run_request(run_input)

                # Now create a connector on the current WorkflowRun so that
                # children can connect on this channel
                self._create_connector(run_input)

        for fixed_input in run.template.fixed_inputs.all():
            assert fixed_input.channel not in visited_channels, \
                'Encountered multiple inputs/fixed_inputs for channel "%s"' \
                % fixed_input.channel
            visited_channels.add(fixed_input.channel)

            run_input = WorkflowRunInput.objects.create(
                workflow_run=run,
                channel=fixed_input.channel,
                type=fixed_input.type)

            run_input.connect(fixed_input)

            # Now create a connector on the current WorkflowRun so that
            # children can connect on this channel
            self._create_connector(run_input)

    def _initialize_outputs(self):
        run = self.downcast()
        visited_channels = set()
        for output in run.template.outputs:
            assert output.get('channel') not in visited_channels, \
                'Encountered multiple outputs for channel %s' \
                % output.get('channel')
            visited_channels.add(output.get('channel'))

            run_output = WorkflowRunOutput.objects.create(
                workflow_run=run,
                type=output.get('type'),
                channel=output.get('channel'))

            # This takes effect only if the WorkflowRun has a parent
            self._connect_output_to_parent(run_output)

            # Now create a connector on the current WorkflowRun so that
            # children can connect on this channel
            self._create_connector(run_output)

    def _initialize_steps(self):
        run = self.downcast()
        run = Run.objects.get(id=run.id)
        run = run.downcast()
        for step in run.template.workflow.steps.all():
            self.create_from_template(step, parent=run)

    def _create_connector(self, io_node):
        try:
            connector = WorkflowRunConnectorNode.objects.create(
                workflow_run = self,
                channel = io_node.channel,
                type = io_node.type
            )
        except IntegrityError:
            # connector already exists. Just use it.
            connector = self.connectors.get(channel=io_node.channel)
        connector.connect(io_node)

    def update_workflow_status(self):
        if self._are_children_finished():
            self.status_is_running = False
            self.status_is_finished = True
            self.save()
            self.add_timepoint("Run %s@%s finished successfully" % (
                self.name, self.uuid))
            if self.parent:
                self.parent.add_timepoint("Child Run %s@%s finished successfully" % (
                    self.name, self.uuid))
        if self.parent:
            self.parent.update_workflow_status()

    def _are_children_finished(self):
        return all([step.status_is_finished for step in self.steps.all()])

    def _kill(self, kill_message):
        self.add_timepoint('Run killed', detail=kill_message, is_error=True)
        self.status_is_killed = True
        self.status_is_running = False
        self.save()
        for step in self.downcast().steps.all():
            step.kill(kill_message)


class StepRun(Run):

    command = models.TextField()
    interpreter = models.CharField(max_length=255)
    interpreter_options = models.CharField(max_length=1024)

    # True if ANY tasks are running
    # status_running = models.BooleanField(default=False)

    # status_tasks_running = models.IntegerField(default=0)
    # status_tasks_finished = models.IntegerField(default=0)
    # status_tasks_failed = models.IntegerField(default=0)

    def create_ready_tasks(self, do_start=True):
        # This is a temporary limit. It assumes no parallel workflows, and no
        # failure recovery, so each step has only one Task.
        if self.tasks.count() > 0:
            # Already ran. Nothing new to process
            return []
        else:
            for input_set in InputNodeSet(
                    self.inputs.all()).get_ready_input_sets():
                task = Task.create_from_input_set(input_set, self)
            return self.tasks.all()

    @classmethod
    def postprocess(cls, run_uuid):
        run = StepRun.objects.get(uuid=run_uuid)
        # There are two paths to get here--if user calls "run" on a
        # template that is already ready, run.postprocess will be triggered
        # without delay. If template is not ready, run.postprocess will be
        # triggered only after template is ready. To avoid a race condition,
        # postprocessing is a no-op if the run is already marked ready.
        assert run.template.postprocessing_status == 'done', \
            'Template not ready, cannot postprocess run %s' % run.uuid
        if run.postprocessing_status == 'done':
            return

        try:
            run._initialize_inputs()
            run._initialize_outputs()
            run.postprocessing_status = 'done'
            run.save()
        except Exception as e:
            run.postprocessing_status = 'error'
            run.save()
            raise e

    def _initialize_inputs(self):
        visited_channels = set()
        for input in self.template.inputs:
            assert input.get('channel') not in visited_channels, \
                "steprun has multiple inputs for channel '%s'" \
                % input.get('channel')
            visited_channels.add(input.get('channel'))

            run_input = StepRunInput.objects.create(
                step_run=self,
                channel=input.get('channel'),
                type=input.get('type'),
                group=input.get('group'),
                mode=input.get('mode'))
            
            # One of these two should always take effect. The other is ignored.
            self._connect_input_to_parent(run_input)
            self._connect_input_to_run_request(run_input)

        for fixed_input in self.template.fixed_inputs.all():
            assert fixed_input.channel not in visited_channels, \
                "steprun has multiple inputs or fixed inputs for channel "\
                "'%s'" % input.channel
            visited_channels.add(fixed_input.channel)

            run_input = StepRunInput.objects.create(
                step_run=self,
                channel=fixed_input.channel,
                type=fixed_input.type,
                group=fixed_input.group,
                mode=fixed_input.mode)
            run_input.connect(fixed_input)

    def _initialize_outputs(self):
        visited_channels = set()
        for output in self.template.outputs:
            assert output.get('channel') not in visited_channels, \
                "workflowrun has multiple outputs for channel '%s'"\
                % output.get('channel')

            visited_channels.add(output.get('channel'))

            run_output = StepRunOutput.objects.create(
                step_run=self,
                type=output.get('type'),
                channel=output.get('channel'),
                source=output.get('source'))
                
            self._connect_output_to_parent(run_output)

    def get_output(self, channel):
        return self.outputs.get(channel=channel)

    def update_status(self):
        self.status_is_finished = True
        self.status_is_running = False
        self.save()
        self.add_timepoint("Run %s@%s finished successfully" % (self.name, self.uuid))
        if self.parent:
            self.parent.add_timepoint(
                "Child Run %s@%s finished successfully" % (self.name, self.uuid))
            self.parent.update_workflow_status()
                

    def _kill(self, kill_message):
        self.add_timepoint('Run killed', detail=kill_message, is_error=True)
        self.status_is_killed = True
        self.status_is_running = False
        self.save()
        for task in self.downcast().tasks.all():
            task.kill(kill_message)


class AbstractStepRunInput(InputOutputNode):

    def is_ready(self):
        if self.get_data_as_scalar() is None:
            return False
        return self.get_data_as_scalar().is_ready()

    class Meta:
        abstract=True

class StepRunInput(AbstractStepRunInput):

    step_run = models.ForeignKey('StepRun',
                                 related_name='inputs',
                                 on_delete=models.CASCADE)
    mode = models.CharField(max_length=255)
    group = models.IntegerField()


class StepRunOutput(InputOutputNode):

    step_run = models.ForeignKey('StepRun',
                                 related_name='outputs',
                                 on_delete=models.CASCADE,
                                 null=True) # for testing only
    mode = models.CharField(max_length=255)
    source = jsonfield.JSONField(null=True)


class WorkflowRunConnectorNode(InputOutputNode):
    # A connector resides in a workflow. All inputs/outputs on the workflow
    # connect internally to connectors, and all inputs/outputs on the
    # nested steps connect externally to connectors on their parent workflow.
    # The primary purpose of this object is to eliminate directly connecting
    # input/output nodes of siblings since their creation order is uncertain.
    # Instead, connections between siblings always pass through a connector
    # in the parent workflow.
    
    workflow_run = models.ForeignKey('WorkflowRun',
                                     related_name='connectors',
                                     on_delete=models.CASCADE)

    class Meta:
        unique_together = (("workflow_run", "channel"),)

class WorkflowRunInput(InputOutputNode):

    workflow_run = models.ForeignKey('WorkflowRun',
                                     related_name='inputs',
                                     on_delete=models.CASCADE)


class WorkflowRunOutput(InputOutputNode):

    workflow_run = models.ForeignKey('WorkflowRun',
                                     related_name='outputs',
                                     on_delete=models.CASCADE)

