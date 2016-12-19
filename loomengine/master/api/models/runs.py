from django.db import models
from django.dispatch import receiver
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

from .base import BaseModel
from api import get_setting
from api.models.input_output_nodes import InputOutputNode, InputNodeSet
from api.models.data_objects import DataObject
from api.models.tasks import Task, TaskInput, TaskOutput, TaskAttemptError
from api.models import uuidstr
from api import tasks

"""
This module defines WorkflowRun and other classes related to
running an analysis
"""

class WorkflowRunManager(object):

    def __init__(self, run):
        assert run.type == 'workflow'
        self.run = run

    def get_inputs(self):
        return self.run.workflowrun.inputs

    def get_outputs(self):
        return self.run.workflowrun.outputs

    def create_ready_tasks(self, do_start):
        return self.run.workflowrun.create_ready_tasks(do_start=do_start)

    def get_tasks(self):
        raise Exception('No tasks on run of type "workflow"')


class StepRunManager(object):

    def __init__(self, run):
        assert run.type == 'step'
        self.run = run

    def get_inputs(self):
        return self.run.steprun.inputs

    def get_outputs(self):
        return self.run.steprun.outputs

    def create_ready_tasks(self, do_start):
        return self.run.steprun.create_ready_tasks(do_start=do_start)

    def get_tasks(self):
        return self.run.steprun.tasks


class Run(BaseModel):
    """AbstractWorkflowRun represents the process of executing a Workflow on 
    a particular set of inputs. The workflow may be either a Step or a 
    Workflow composed of one or more Steps.
    """

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
    status = models.CharField(
        max_length=255,
        default='',
    )
    template = models.ForeignKey('Template',
                                 related_name='runs',
                                 on_delete=models.PROTECT,
                                 null=True) # For testing only
    saving_status = models.CharField(
        max_length=255,
        default='saving',
        choices=(('saving', 'Saving'),
                 ('ready', 'Ready'),
                 ('error', 'Error'))
    )

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

    def create_ready_tasks(self, do_start=True):
        return self._get_manager().create_ready_tasks(do_start=do_start)
    
    def get_input(self, channel):
        inputs = [i for i in self.inputs.filter(channel=channel)]
        assert len(inputs) == 1
        return inputs[0]

    def get_output(self, channel):
        outputs = [o for o in self.outputs.filter(channel=channel)]
        assert len(outputs) == 1
        return outputs[0]

#    def update_parent_status(self):
#        if self.parent:
#            self.parent.update_status()

    def get_run_request(self):
        try:
            return self.run_request
        except ObjectDoesNotExist:
            pass
        return self.parent.get_run_request()

    @classmethod
    def create_from_template(cls, template, parent=None, no_delay=True):
        if template.type == 'step':
            run = StepRun.objects.create(template=template,
                                         name=template.name,
                                         type=template.type,
                                         command=template.step.command,
                                         interpreter=template.step.interpreter,
                                         parent=parent).run_ptr
            if no_delay:
                tasks._postprocess_step_run(run.id)
            else:
                tasks.postprocess_step_run(run.id)
        else:
            assert template.type == 'workflow', \
                'Invalid template type "%s"' % template.type
            run = WorkflowRun.objects.create(template=template,
                                             name=template.name,
                                             type=template.type,
                                             parent=parent).run_ptr
            if no_delay:
                tasks._postprocess_workflow_run(run.id)
            else:
                tasks.postprocess_workflow_run(run.id)

        return run.downcast()

    def downcast(self):
        if self.type == 'step':
            try:
                return self.steprun
            except AttributeError:
                return self
        else:
            assert self.type == 'workflow'
            try:
                return self.workflowrun
            except AttributeError:
                return self

    def _get_destinations(self):
        run = self.downcast()
        return [dest for dest in run.inputs.all()]

    def _get_source(self, channel):
        run = self.downcast()
        # Four possible sources for this step's inputs:
        # 1. inputs from parent
        # 2. outputs from siblings
        # 3. user-provided inputs in run_request
        # 4. fixed_inputs on template
        sources = []
        if run.parent:
            sources.extend(run.parent.inputs.filter(channel=channel))
            siblings = run.parent.workflowrun.steps.exclude(id=run.id)
            for sibling in siblings:
                sources.extend(sibling.outputs.filter(channel=channel))
        try:
            run_request = run.run_request
            sources.extend(run_request.inputs.filter(channel=channel))
        except ObjectDoesNotExist:
            pass
        sources.extend(run.template.fixed_inputs.filter(channel=channel))
        assert len(sources) == 1
        return sources[0]

    def connect_channels(self):
        run = self.downcast()
        # Channels must be connected in order from the outside in,
        # so this function connects the current run outward
        # but does not connect to its steps.
        for destination in run._get_destinations():
            source = run._get_source(destination.channel)
            # Make sure matching source and destination nodes are connected
            source.connect(destination)
        try:
            for step in run.workflowrun.steps.all():
                step.connect_channels()
        except ObjectDoesNotExist:
            # run.workflowrun does not exist for a StepRun
            pass


class WorkflowRun(Run):

    def add_step(self, step_run):
        step_run.parent = self
        step_run.save()

    def get_step_status_count(self):
        count = {
            'waiting': 0,
            'running': 0,
            'error': 0,
            'success': 0,
        }
        for step in self.steps.all():
            step_counts = step.get_step_status_count()
            count['waiting'] += step_counts['waiting']
            count['running'] += step_counts['running']
            count['error'] += step_counts['error']
            count['success'] += step_counts['success']
        return count

    def update_status(self):
        status_list = []
        count = self.get_step_status_count()
        if count['waiting']:
            pluralize = 's' if count['waiting'] > 1 else ''
            status_list.append('%s step%s waiting.' % (count['waiting'], pluralize))
        if count['running']:
            pluralize = 's' if count['running'] > 1 else ''
            status_list.append('%s step%s running.' % (count['running'], pluralize))
        if count['error']:
            pluralize = 's' if count['error'] > 1 else ''
            status_list.append('%s step%s with errors.' % (count['error'], pluralize))
        if count['success']:
            pluralize = 's' if count['success'] > 1 else ''
            status_list.append('%s step%s finished successfully.' % (count['success'], pluralize))
#        self.status = ' '.join(status_list)
        self.save()
#        self.update_parent_status()

    def create_ready_tasks(self, do_start=True):
        for step_run in self.steps.all():
            step_run.create_ready_tasks(do_start=do_start)

    @classmethod
    def postprocess(cls, run_id):
        run = WorkflowRun.objects.get(id=run_id)
        #        try:
        run._initialize_inputs()
        run._initialize_outputs()
        run._initialize_steps()

        # connect_channels must be triggered on the topmost parent.
        # This will connect channels on children as well.
        try:
            run.run_request
            run.connect_channels()
        except ObjectDoesNotExist:
            pass

        run.saving_status = 'ready'
        run.save()
#        except Exception as e:
#            run.saving_status = 'error'
#            run.save()
#            raise e

    def _initialize_inputs(self):
        run = self.downcast()
        all_channels = set()
        if run.template.inputs:
            for input in run.template.inputs:
                assert input.get('channel') not in all_channels
                all_channels.add(input.get('channel'))

                WorkflowRunInput.objects.create(
                    workflow_run=run,
                    channel=input.get('channel'),
                    type=input.get('type'))

        for fixed_input in run.template.fixed_inputs.all():
            assert fixed_input.channel not in all_channels
            all_channels.add(fixed_input.channel)

            WorkflowRunInput.objects.create(
                workflow_run=run,
                channel=fixed_input.channel,
                type=fixed_input.type)

    def _initialize_outputs(self):
        run = self.downcast()
        all_channels = set()
        for output in run.template.outputs:
            assert output.get('channel') not in all_channels
            all_channels.add(output.get('channel'))

            WorkflowRunOutput.objects.create(
                workflow_run=run,
                type=output.get('type'),
                channel=output.get('channel'))

    def _initialize_steps(self):
        run = self.downcast()
        for step in run.template.workflow.steps.all():
            self.create_from_template(step, parent=run, no_delay=True)


class StepRun(Run):

    NAME_FIELD = 'template__name'

    command = models.TextField()
    interpreter = models.CharField(max_length=255)

    @property
    def errors(self):
        if self.tasks.count() == 0:
            return TaskAttemptError.objects.none()
        return self.tasks.first().errors

    def get_step_status_count(self):
        count = {
            'waiting': 0,
            'running': 0,
            'error': 0,
            'success': 0,
        }
        if self.errors.count() > 0:
            count['error'] = 1
        elif self.status.startswith('Waiting'):
            count['waiting'] = 1
        elif self.status.startswith('Finished'):
            count['success'] = 1
        else:
            count['running'] = 1
        return count

    def get_all_inputs(self):
        inputs = [i for i in self.inputs.all()]
        inputs.extend([i for i in self.fixed_inputs.all()])
        return inputs

    def create_ready_tasks(self, do_start=True):
        # This is a temporary limit. It assumes no parallel workflows, and no
        # failure recovery, so each step has only one Task.
        if self.tasks.count() == 0:
            for input_set in InputNodeSet(
                    self.get_all_inputs()).get_ready_input_sets():
                task = Task.create_from_input_set(input_set, self)
                if do_start:
                    task.run()
            self.update_status()

    def update_status(self):
        pass
#        if self.tasks.count() == 0:
#            missing_inputs = InputNodeSet(
#                self.get_all_inputs()).get_missing_inputs()
#            if len(missing_inputs) == 1:
#                status = 'Waiting for input "%s"' % missing_inputs[0].channel
#            else:
#                status = 'Waiting for inputs %s' % ', '.join(
#                    [input.channel for input in missing_inputs])
#        else:
#            status = self.tasks.first().status

#        if status != self.status:
#            self.status = status
#            self.save()
        #self.update_parent_status()

    @classmethod
    def postprocess(cls, run_id):
        run = StepRun.objects.get(id=run_id)
        try:
            run._initialize_inputs()
            run._initialize_outputs()

            # connect_channels must be triggered on the topmost parent.
            # This will connect channels on children as well.
            try:
                run.run_request
                run.connect_channels()
            except ObjectDoesNotExist:
                pass
                
            run.saving_status = 'ready'
            run.save()
        except Exception as e:
            run.saving_status = 'error'
            run.save()
            raise e

    def _initialize_inputs(self):
        all_channels = set()
        for input in self.template.inputs:
            assert input.get('channel') not in all_channels
            all_channels.add(input.get('channel'))

            StepRunInput.objects.create(
                step_run=self,
                channel=input.get('channel'),
                type=input.get('type'),
                group=input.get('group'),
                mode=input.get('mode'))

        for fixed_input in self.template.fixed_inputs.all():
            assert fixed_input.channel not in all_channels
            all_channels.add(fixed_input.channel)

            StepRunInput.objects.create(
                step_run=self,
                channel=fixed_input.channel,
                type=fixed_input.type,
                group=fixed_input.group,
                mode=fixed_input.mode)

    def _initialize_outputs(self):
        all_channels = set()
        for output in self.template.outputs:
            assert output.get('channel') not in all_channels
            all_channels.add(output.get('channel'))

            StepRunOutput.objects.create(
                step_run=self,
                type=output.get('type'),
                channel=output.get('channel'))


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

#    @property
#    def parser(self):
#        if self.step_output is None:
#            return ''
#        return self.step_output.parser


class WorkflowRunInput(InputOutputNode):

    workflow_run = models.ForeignKey('WorkflowRun',
                                     related_name='inputs',
                                     on_delete=models.CASCADE)


class WorkflowRunOutput(InputOutputNode):

    workflow_run = models.ForeignKey('WorkflowRun',
                                     related_name='outputs',
                                     on_delete=models.CASCADE)


class StepRunOutputSource(BaseModel):

    output = models.OneToOneField(
        StepRunOutput,
	related_name='source',
        on_delete=models.CASCADE)

    filename = models.CharField(max_length=1024, null=True)
    stream = models.CharField(max_length=255, null=True)
