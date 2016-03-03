from django.core import exceptions

from analysis.models.base import AnalysisAppInstanceModel, AnalysisAppImmutableModel
from analysis.models.task_definitions import *
from analysis.models.workflows import Step
#from analysis.task_manager import TaskManager
from universalmodels import fields


class TaskRun(AnalysisAppInstanceModel):
    """One instance of executing a step on a particular set of inputs.
    """

    # If multiple steps have the same StepDefinition, they can share a StepRun
    task_definition = fields.ForeignKey('TaskDefinition', null=True, related_name='task_runs')
    task_run_inputs = fields.OneToManyField('TaskRunInput', related_name='task_run')
    task_run_outputs = fields.OneToManyField('TaskRunOutput', related_name='task_run')
    status = fields.CharField(
        max_length=255,
        default='running',
        choices=(('running', 'Running'),
                 ('error', 'Error'),
                 ('canceled', 'Canceled'),
                 ('complete', 'Complete')
        )
    )

    @classmethod
    def create_from_definition(cls, task_definition):
        return cls.create(
            {
                'task_definition': task_definition.to_struct()
            }
        )

    def check_status(self):
        pass
    
    def execute(self):
        print "RUNNING %s" % self._id
        TaskManager.run_task(self)

class TaskRunInput(AnalysisAppInstanceModel):

    name = fields.CharField(max_length = 256)
    task_definition_input = fields.ForeignKey('TaskDefinitionInput', null=True)


class TaskRunOutput(AnalysisAppInstanceModel):

    name = fields.CharField(max_length = 256)
    task_definition_output = fields.ForeignKey('TaskDefinitionOutput', null=True)
    data_object = fields.ForeignKey('DataObject', null=True)
