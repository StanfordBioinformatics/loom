from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from analysis.exceptions import *
from .base import AnalysisAppInstanceModel, AnalysisAppImmutableModel
from .task_definitions import TaskDefinition
from .task_runs import TaskRun, TaskRunInput, TaskRunOutput
from .workflows import Workflow, Step, WorkflowRuntimeInput, WorkflowFixedInput, \
    WorkflowOutput, StepRuntimeInput, StepFixedInput, StepOutput
from jinja2 import DictLoader, Environment
from universalmodels import fields


"""
This module defines WorkflowRun and other classes related to
running an analysis
"""

class AbstractWorkflowRun(AnalysisAppInstanceModel):
    """AbstractWorkflowRun represents the process of executing a Workflow on a particular
    set of inputs. The workflow may be either a Step or a Workflow composed of one or more Steps.
    """

    @classmethod
    def create_run_from_workflow(cls, workflow):

        workflow = workflow.downcast()

        def _add_inputs_outputs_from_workflow(run, workflow):
            run.update({
                'inputs': [{'channel_name': input.channel, 'type': input.type} for input in workflow.inputs.all()],
                'fixed_inputs': [{'channel_name': input.channel, 'type': input.type} for input in workflow.fixed_inputs.all()],
                'outputs': [{'channel_name': output.channel, 'type': output.type} for output in workflow.outputs.all()]
            })
            return run

        if workflow.is_step():
            run = {'template_step': workflow.to_struct()}
            run = _add_inputs_outputs_from_workflow(run, workflow)
            return StepRun.create(run)
        else:
            run = {'template_workflow': workflow.to_struct()}
            run = _add_inputs_outputs_from_workflow(run, workflow)
            return WorkflowRun.create(run)

    def is_step(self):
        return self.downcast().get_template().is_step()


class WorkflowRun(AbstractWorkflowRun):

    NAME_FIELD = 'template_workflow__name'
        
    step_runs = fields.OneToManyField('AbstractWorkflowRun', related_name='parent_run')
    inputs = fields.OneToManyField('InputOutputNode', related_name='workflow_run_as_input')
    fixed_inputs = fields.OneToManyField('InputOutputNode', related_name='workflow_run_as_fixed_input')
    outputs = fields.OneToManyField('InputOutputNode', related_name='workflow_run_as_output')
    template_workflow = fields.ForeignKey('Workflow')
    #status = fields.CharField(
    #    max_length=255,
    #    default='running',
    #    choices=(('running', 'Running'),
    #             ('canceled', 'Canceled'),
    #             ('completed', 'Completed')
    #    )
    #)

    def get_template(self):
        return self.template_workflow

    def after_create(self):
        self._initialize_step_runs()
        self._initialize_channels()

    def _initialize_step_runs(self):
        """Create a run for each step
        """
        for step in self.template_workflow.steps.all():
            step_run = self.create_run_from_workflow(step)
            self.step_runs.add(step_run)

    def _initialize_channels(self):
        """Create the Channel objects connecting workflow input/outputs to step input/outputs
        """
        from .channels import Channel
        for source_node in self._get_source_nodes():
            destination_nodes = self._get_matching_destination_nodes(source_node.channel_name)
            channel = Channel.create_from_sender(source_node)
            channel.add_receivers(destination_nodes)

    def _get_source_nodes(self):
        nodes = [node for node in self.inputs.all()]
        nodes.extend([node for node in self.fixed_inputs.all()])
        for step_run in self.step_runs.all():
            nodes.extend([node for node in step_run.downcast().outputs.all()])
        return nodes

    def _get_matching_destination_nodes(self, channel_name):
        nodes = [node for node in self.outputs.filter(channel_name=channel_name)]
        for step_run in self.step_runs.all():
            nodes.extend([node for node in step_run.downcast().inputs.filter(channel_name=channel_name)])
        return nodes


class StepRun(AbstractWorkflowRun):
    
    NAME_FIELD = 'template_step__name'
    
    inputs = fields.OneToManyField('InputOutputNode', related_name='step_run_as_input')
    fixed_inputs = fields.OneToManyField('InputOutputNode', related_name='step_run_as_fixed_input')
    outputs = fields.OneToManyField('InputOutputNode', related_name='step_run_as_output')
    template_step = fields.ForeignKey('Step')
    # task_runs = fields.OneToManyField('TaskRun')
    #status = fields.CharField(
    #    max_length=255,
    #    default='waiting',
    #    choices=(('waiting', 'Waiting'),
    #             ('running', 'Running'),
    #             ('completed', 'Completed'),
    #             ('canceled', 'Canceled'),
    #             ('error', 'Error'),
    #    )
    #)

    def get_template(self):
        return self.template_step


class InputOutputNode(AnalysisAppInstanceModel):

    channel_name = fields.CharField(max_length=255)
    type = fields.CharField(
        max_length=255,
        choices=(
            ('file', 'File'),
        )
    )
