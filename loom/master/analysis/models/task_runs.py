from django.core import exceptions
from django.utils import timezone
from jinja2 import DictLoader, Environment

from analysis.models.base import AnalysisAppInstanceModel, AnalysisAppImmutableModel
from analysis.models.task_definitions import *
from analysis.models.data import DataObject
from analysis.models.workflows import Step
from analysis.task_manager.factory import TaskManagerFactory
from analysis.task_manager.dummy import DummyTaskManager
from universalmodels import fields


class TaskRun(AnalysisAppInstanceModel):
    """One instance of executing a TaskDefinition, i.e. executing a Step on a particular set
    of inputs.
    """

    task_definition = fields.ForeignKey('TaskDefinition', related_name='task_runs')
    task_run_inputs = fields.OneToManyField('TaskRunInput', related_name='task_run')
    task_run_outputs = fields.OneToManyField('TaskRunOutput', related_name='task_run')
    logs = fields.OneToManyField('TaskRunLog', related_name='task_run')
    # status = fields.CharField(
    #    max_length=255,
    #    default='ready_to_run',
    #    choices=(
    #        ('ready_to_run', 'Ready to run'),
    #        ('running', 'Running'),
    #        ('completed', 'Completed'),
    #        ('canceled', 'Canceled')
    #    )
    #)

    @classmethod
    def create_from_step_run(cls, step_run):
        task_run_inputs = cls._create_task_run_inputs(step_run)
        task_run_outputs = cls._create_task_run_outputs(step_run)
        task_definition = cls._create_task_definition(step_run, task_run_inputs, task_run_outputs)
        task_run = TaskRun.create({
            'task_run_inputs': [i.to_struct() for i in task_run_inputs],
            'task_run_outputs': [o.to_struct() for o in task_run_outputs],
            'task_definition': task_definition
        })
        step_run.task_runs.add(task_run)
        return task_run

    @classmethod
    def _create_task_definition(cls, step_run, task_run_inputs, task_run_outputs):
        task_definition_inputs = [i.task_definition_input for i in task_run_inputs]
        task_definition_outputs = [o.task_definition_output for o in task_run_outputs]
        task_definition = TaskDefinition.create({
            'inputs': [i.to_struct() for i in task_definition_inputs],
            'outputs': [o.to_struct() for o in task_definition_outputs],
            'command': cls._get_task_definition_command(step_run.step.command, task_run_inputs, task_run_outputs),
            'environment': cls._get_task_definition_environment(step_run.step.environment)
        })
        return task_definition.to_struct()

    @classmethod
    def _create_task_run_inputs(cls, step_run):
        return [cls._create_task_run_input(input) for input in step_run.inputs.all()]

    @classmethod
    def _create_task_run_input(cls, step_run_input):
        data_object = step_run_input.pop()
        task_run_input = TaskRunInput.create(
            {
                'task_definition_input': {
                    'data_object_content': data_object.content.to_struct()
                },
                'data_object': data_object.to_struct()
            }
        )
        step_run_input.task_run_inputs.add(task_run_input)
        return task_run_input

    @classmethod
    def _create_task_run_outputs(cls, step_run):
        return [cls._create_task_run_output(output) for output in step_run.outputs.all()]

    @classmethod
    def _create_task_run_output(cls, step_run_output):
        task_run_output = TaskRunOutput.create({
            'task_definition_output': {
                'filename': step_run_output.get_filename()
            }
        })
        step_run_output.task_run_outputs.add(task_run_output)
        return task_run_output

    @classmethod
    def _get_task_definition_command(cls, raw_command, task_run_inputs, task_run_outputs):
        context = {}
        for task_run_input in task_run_inputs:
            channel = task_run_input.step_run_input.channel
            substitution_value = task_run_input.task_definition_input.get_substitution_value()
            context[channel] = substitution_value
        for task_run_output in task_run_outputs:
            channel = task_run_output.step_run_output.channel
            substitution_value = task_run_output.task_definition_output.get_substitution_value()
            context[channel] = substitution_value
        loader = DictLoader({'template': raw_command})
        env = Environment(loader=loader)
        template = env.get_template('template')
        command = template.render(**context)
        return command

    @classmethod
    def _get_task_definition_environment(cls, raw_environment):
        # TODO get specific docker image ID
        return {
            'docker_image': raw_environment.downcast().docker_image
        }

    def run(self, is_mock=False):
        task_manager = TaskManagerFactory.get_task_manager(is_mock=is_mock)
        step_run = self.step_run
        requested_resources = step_run.step.resources
        task_manager.run(self, requested_resources)

    def mock_run(self):
        return self.run(is_mock=True)

class TaskRunInput(AnalysisAppInstanceModel):
    task_definition_input = fields.ForeignKey('TaskDefinitionInput')
    data_object = fields.ForeignKey('DataObject')


class TaskRunOutput(AnalysisAppInstanceModel):
    task_definition_output = fields.ForeignKey('TaskDefinitionOutput')
    data_object = fields.ForeignKey('DataObject', null=True)

    def after_create_or_update(self):
        if self.data_object:
            self.push()

    def push(self):
        self.step_run_output.push(self.data_object)
        
    
class TaskRunLog(AnalysisAppInstanceModel):
    logfile = fields.ForeignKey('FileDataObject')
    logname = fields.CharField(max_length=255)
