from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from analysis.exceptions import *
from .base import AnalysisAppInstanceModel, AnalysisAppImmutableModel
from .data_objects import DataObject
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
    def create_from_run_request(cls, run_request):
        if run_request.workflow.is_step():
            run = StepRun.create(
                {'template_step': run_request.workflow.to_struct()}
            )
        else:
            run = WorkflowRun.create(
                {'template_workflow': run_request.workflow.to_struct()}
            )


class WorkflowRun(AbstractWorkflowRun):

    NAME_FIELD = 'template_workflow__name'
        
    step_runs = fields.OneToManyField('AbstractWorkflowRun', related_name='parent_run')
    inputs = fields.OneToManyField('InputOutputNode', related_name='workflow_run_as_input')
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


class StepRun(AbstractWorkflowRun):
    
    NAME_FIELD = 'template_step__name'
    
    inputs = fields.OneToManyField('InputOutputNode', related_name='step_as_input')
    outputs = fields.OneToManyField('InputOutputNode', related_name='step_as_output')
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


class InputOutputNode(AnalysisAppInstanceModel):

    channel_name = fields.CharField(max_length=255)
