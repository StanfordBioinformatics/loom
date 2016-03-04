from django.core import exceptions

from analysis.models.base import AnalysisAppInstanceModel, AnalysisAppImmutableModel
from analysis.models.task_definitions import *
from analysis.models.workflows import Step
from analysis.task_manager.dummy import DummyTaskManager
from universalmodels import fields


class TaskRun(AnalysisAppInstanceModel):
    """One instance of executing a TaskDefinition, i.e. executing a Step on a particular set
    of inputs.
    """

    # If multiple steps have the same TaskDefinition, they can share a TaskRun.
    task_definition = fields.ForeignKey('TaskDefinition', related_name='task_runs')
    task_run_inputs = fields.OneToManyField('TaskRunInput', related_name='task_run')
    task_run_outputs = fields.OneToManyField('TaskRunOutput', related_name='task_run')
    status = fields.CharField(
        max_length=255,
        default='ready_to_run',
        choices=(
            ('ready_to_run', 'Ready to run'),
            ('running', 'Running'),
            ('completed', 'Completed')
        )
    )

    @classmethod
    def dummy_run_all(cls):
        for task_run in TaskRun.objects.filter(status='ready_to_run'):
            task_run.dummy_run()
                 
    def dummy_run(self):
        self.update({'status': 'running'})
        DummyTaskManager.run_task(self)

    def submit_result(self, out_id, data_object):
        output = self.task_run_outputs.get(_id=out_id)
        output.update({'data_object': data_object})
        # Send to any channels that are attached
        for step_run_output in output.step_run_outputs.all():
            step_run_output.channel.add_data_object(output.data_object)
        
    def update_status(self):
        for output in self.task_run_outputs.all():
            if output.data_object is None:
                return
        self.update({'status': 'completed'})

        
class TaskRunInput(AnalysisAppInstanceModel):

    task_definition_input = fields.ForeignKey('TaskDefinitionInput')


class TaskRunOutput(AnalysisAppInstanceModel):

    task_definition_output = fields.ForeignKey('TaskDefinitionOutput')
    data_object = fields.ForeignKey('DataObject', null=True)

    def has_result(self):
        return self.data_object is not None
