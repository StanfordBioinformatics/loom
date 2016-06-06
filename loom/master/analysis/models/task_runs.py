from copy import deepcopy
from django.utils import timezone
from jinja2 import DictLoader, Environment

from analysis.models.base import AnalysisAppInstanceModel, AnalysisAppImmutableModel
from analysis.models.task_definitions import *
from analysis.models.data_objects import DataObject
from analysis.models.workflows import Step, RequestedResourceSet
from analysis.task_manager.factory import TaskManagerFactory
from analysis.task_manager.dummy import DummyTaskManager
from universalmodels import fields


class TaskRun(AnalysisAppInstanceModel):
    """One instance of executing a TaskDefinition, i.e. executing a Step on a particular set
    of inputs.
    """

    task_definition = fields.ForeignKey('TaskDefinition', related_name='task_runs')
    inputs = fields.OneToManyField('TaskRunInput', related_name='task_run')
    outputs = fields.OneToManyField('TaskRunOutput', related_name='task_run')
    resources = fields.ForeignKey('RequestedResourceSet')

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
        input_context = cls._get_task_run_input_context(task_run_inputs)
        task_run_outputs = cls._create_task_run_outputs(step_run, input_context)
        task_definition = cls._create_task_definition(step_run, task_run_inputs, task_run_outputs)
        task_run = TaskRun.create({
            'inputs': [i.to_struct() for i in task_run_inputs],
            'outputs': [o.to_struct() for o in task_run_outputs],
            'task_definition': task_definition,
            'resources': cls._get_task_run_resources(step_run.step.resources, input_context),
        })
        step_run.task_runs.add(task_run)
        return task_run

    @classmethod
    def _create_task_definition(cls, step_run, task_run_inputs, task_run_outputs):
        context = cls._get_task_run_input_context(task_run_inputs)
        context.update(cls._get_task_run_output_context(task_run_outputs))
        
        task_definition_inputs = [i.task_definition_input for i in task_run_inputs]
        task_definition_outputs = [o.task_definition_output for o in task_run_outputs]
        task_definition = TaskDefinition.create({
            'inputs': [i.to_struct() for i in task_definition_inputs],
            'outputs': [o.to_struct() for o in task_definition_outputs],
            'command': cls._render_from_template(step_run.step.command, context),
            'environment': cls._get_task_definition_environment(step_run.step.environment),
        })
        return task_definition.to_struct()

    @classmethod
    def _create_task_run_inputs(cls, step_run):
        inputs = [cls._create_task_run_input(input) for input in step_run.inputs.all()]
        inputs.extend([cls._create_task_run_input(input) for input in step_run.fixed_inputs.all()])
        return inputs

    @classmethod
    def _create_task_run_input(cls, step_run_input):
        data_object = step_run_input.pop()
        task_run_input = TaskRunInput.create(
            {
                'task_definition_input': {
                    'data_object_content': data_object.get_content().to_struct()
                },
                'data_object': data_object.to_struct()
            }
        )
        step_run_input.task_run_inputs.add(task_run_input)
        return task_run_input

    @classmethod
    def _create_task_run_outputs(cls, step_run, input_context):
        return [cls._create_task_run_output(output, input_context) for output in step_run.outputs.all()]

    @classmethod
    def _create_task_run_output(cls, step_run_output, input_context):
        task_run_output = TaskRunOutput.create({
            'task_definition_output': {
                'filename': cls._render_from_template(step_run_output.get_filename(), input_context)
            }
        })
        step_run_output.task_run_outputs.add(task_run_output)
        return task_run_output

    @classmethod
    def _get_task_run_resources(cls, step_resources, input_context):
        return {
            'cores': cls._render_from_template(step_resources.cores, input_context),
            'memory': cls._render_from_template(step_resources.memory, input_context),
            'disk_space': cls._render_from_template(step_resources.disk_space, input_context),
        }

    @classmethod
    def _get_task_run_input_context(cls, task_run_inputs):
        context = {}
        for task_run_input in task_run_inputs:
            channel = task_run_input.get_channel()
            substitution_value = task_run_input.task_definition_input.get_substitution_value()
            context[channel] = substitution_value
        return context
        
    @classmethod
    def _get_task_run_output_context(cls, task_run_outputs):
        context = {}
        for task_run_output in task_run_outputs:
            channel = task_run_output.step_run_output.channel
            substitution_value = task_run_output.task_definition_output.get_substitution_value()
            context[channel] = substitution_value
        return context

    @classmethod
    def _render_from_template(cls, raw_text, context):
        loader = DictLoader({'template': raw_text})
        env = Environment(loader=loader)
        template = env.get_template('template')
        return template.render(**context)

    @classmethod
    def _get_task_definition_environment(cls, raw_environment):
        # TODO get specific docker image ID
        return {
            'docker_image': raw_environment.downcast().docker_image
        }

    def run(self, is_mock=False):
        task_manager = TaskManagerFactory.get_task_manager(is_mock=is_mock)
        task_manager.run(self)

    def mock_run(self):
        return self.run(is_mock=True)


class TaskRunInput(AnalysisAppInstanceModel):
    task_definition_input = fields.ForeignKey('TaskDefinitionInput')
    data_object = fields.ForeignKey('DataObject')

    def get_channel(self):
        if self.step_run_input is not None:
            return self.step_run_input.channel
        else:
            return self.step_run_input_as_fixed.channel


class TaskRunOutput(AnalysisAppInstanceModel):
    task_definition_output = fields.ForeignKey('TaskDefinitionOutput')
    data_object = fields.ForeignKey('DataObject', null=True)

    def push(self, data_object):
        self.data_object = data_object
        self.step_run_output.push(self.data_object)


class TaskRunExecution(AnalysisAppInstanceModel):
    task_run = fields.ForeignKey('TaskRun')
    logs = fields.OneToManyField('TaskRunExecutionLog', related_name='task_run')
    outputs = fields.OneToManyField('TaskRunExecutionOutput', related_name='task_run')
    
    class Meta:
        abstract=True


class MockTaskRunExecution(TaskRunExecution):
    
    pass


class TaskRunExecutionOutput(AnalysisAppInstanceModel):
    task_run_output = fields.ForeignKey('TaskRunOutput')
    data_object = fields.ForeignKey('DataObject', null=True)

    def after_create_or_update(self):
        # Push when data is added
        if self.data_object:
            self.push()

    def push(self):
        self.task_run_output.push(self.data_object)


class TaskRunExecutionLog(AnalysisAppInstanceModel):
    logfile = fields.ForeignKey('FileDataObject')
    logname = fields.CharField(max_length=255)
