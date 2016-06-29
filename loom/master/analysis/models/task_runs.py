from copy import deepcopy
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from jinja2 import DictLoader, Environment
import os

from analysis.models.base import AnalysisAppInstanceModel, AnalysisAppImmutableModel
from analysis.models.task_definitions import *
from analysis.models.data_objects import DataObject, AbstractFileImport
from analysis.models.workflows import Step, RequestedResourceSet
from analysis import get_setting
from analysis.task_manager.factory import TaskManagerFactory
from universalmodels import fields


class TaskRun(AnalysisAppInstanceModel):
    """One instance of executing a TaskDefinition, i.e. executing a Step on a particular set
    of inputs.
    """

    task_definition = fields.ForeignKey('TaskDefinition', related_name='task_runs')
    inputs = fields.OneToManyField('TaskRunInput', related_name='task_run')
    outputs = fields.OneToManyField('TaskRunOutput', related_name='task_run')
    resources = fields.ForeignKey('RequestedResourceSet')

    def run(self, is_mock=False):
        task_manager = TaskManagerFactory.get_task_manager(is_mock=is_mock)
        task_manager.run(self)

    def mock_run(self):
        return self.run(is_mock=True)


class TaskRunInput(AnalysisAppInstanceModel):
    task_definition_input = fields.ForeignKey('TaskDefinitionInput')
    data_object = fields.ForeignKey('DataObject')

    def get_step_run_input(self, step_run):
        # Get the related StepRunInput in the given StepRun
        step_run_inputs = self.step_run_inputs.filter(step_run=step_run)
        if step_run_inputs.count() == 1:
            return step_run_inputs.first()
        elif step_run_inputs.count() == 0:
            fixed_step_run_inputs = self.fixed_step_run_inputs.filter(step_run=step_run)
            if step_run_inputs.count() == 1:
                return fixed_step_run_inputs.first()
        else:
            assert False

    def get_channel(self, step_run):
        return self.get_step_run_input(step_run).channel


class TaskRunOutput(AnalysisAppInstanceModel):
    task_definition_output = fields.ForeignKey('TaskDefinitionOutput')
    data_object = fields.ForeignKey('DataObject', null=True)

    def get_step_run_output(self, step_run):
        # Get the related StepRunOutput in the given StepRun
        step_run_outputs = self.step_run_outputs.filter(step_run=step_run)
        assert step_run_outputs.count() == 1
        return step_run_outputs.first()

    def get_channel(self, step_run):
        return self.get_step_run_output(step_run).channel

    def push(self, data_object, step_run=None):
        if self.data_object is None:
            self.update({'data_object': data_object})
            # Sometimes this is called to push to a specific StepRun that was added late
            # Otherwise, we push to all StepRuns available
            if step_run is not None:
                self.get_step_run_output(step_run).push(self.data_object)
            else:
                for step_run_output in self.step_run_outputs.all():
                    step_run_output.push(self.data_object)


class TaskRunAttempt(AnalysisAppInstanceModel):
    task_run = fields.ForeignKey('TaskRun')
    log_files = fields.OneToManyField('TaskRunAttemptLogFile', related_name='task_run_attempt')
    outputs = fields.OneToManyField('TaskRunAttemptOutput', related_name='task_run_attempt')

    def after_create_or_update(self, data):
        if self.outputs.count() == 0:
            for output in self.task_run.outputs.all():
                self.outputs.add(
                    TaskRunAttemptOutput.create(
                        {'task_run_output': output}
                    ))

    @classmethod
    def get_working_dir(cls, task_run_attempt_id):
        return os.path.join(get_setting('FILE_ROOT_FOR_WORKER'), 'runtime_volumes', task_run_attempt_id, 'work')
    
    @classmethod
    def get_log_dir(cls, task_run_attempt_id):
        return os.path.join(get_setting('FILE_ROOT_FOR_WORKER'), 'runtime_volumes', task_run_attempt_id, 'logs')

    def create_log_file(self, log_file_struct):
        log_file = TaskRunAttemptLogFile.create(log_file_struct)
        self.log_files.add(log_file)
        return log_file

class MockTaskRunAttempt(TaskRunAttempt):

    pass


class LocalTaskRunAttempt(TaskRunAttempt):

    pass

class GoogleCloudTaskRunAttempt(TaskRunAttempt):

    pass


class TaskRunAttemptOutput(AnalysisAppInstanceModel):

    task_run_output = fields.ForeignKey('TaskRunOutput')
    data_object = fields.OneToOneField('DataObject', null=True, related_name='task_run_attempt_output')

    def after_create_or_update(self, data):
        if not get_setting('DISABLE_AUTO_PUSH'):
            if self.data_object:
                if self.data_object.is_ready():
                    self.push(self.data_object)

    def push(self, data_object):
        self.task_run_output.push(data_object)


class TaskRunAttemptLogFile(AnalysisAppInstanceModel):

    log_name = fields.CharField(max_length=255)
    file_data_object = fields.OneToOneField('FileDataObject', null=True, related_name='task_run_attempt_log_file')

    def after_create_or_update(self, data):
        if self.file_data_object is None:
            self.update(
                {
                    'file_data_object': {
                        'file_import': TaskRunAttemptLogFileImport.create({})
                    }
                }
            )

class AbstractTaskRunAttemptFileImport(AbstractFileImport):

    def _get_browsable_path_prefix(self):
        try:
            # for output files
            task_run_attempt = self.data_object.task_run_attempt_output.task_run_attempt
        except ObjectDoesNotExist:
            task_run_attempt = self.data_object.task_run_attempt_log_file.task_run_attempt
            
        assert task_run_attempt.task_run.step_runs.count() == 1
        step_run = task_run_attempt.task_run.step_runs.first()
        path = os.path.join(
            "%s-%s" % (
                step_run.template.name,
                step_run.get_id(),
            ),
            "task-%s" % task_run_attempt.task_run.get_id(),
            "attempt-%s" % task_run_attempt.get_id(),
        )
        while step_run.parent_run is not None:
            step_run = step_run.parent_run
            path = os.path.join(
                "%s-%s" % (
                    step_run.template.name,
                    step_run.get_id(),
                ),
                path
            )
        return os.path.join('runs', path)

    class Meta:
        abstract = True

class TaskRunAttemptOutputFileImport(AbstractTaskRunAttemptFileImport):

    def get_browsable_path(self):
        return os.path.join(self._get_browsable_path_prefix(), 'work')


class TaskRunAttemptLogFileImport(AbstractTaskRunAttemptFileImport):

    def get_browsable_path(self):
        return os.path.join(self._get_browsable_path_prefix(), 'logs')


class TaskRunBuilder(object):

    @classmethod
    def create_from_step_run(cls, step_run, input_set):
        task_definition_inputs = cls._create_task_definition_inputs(input_set)
        input_context = cls._get_input_context(input_set)
        task_definition_outputs = cls._create_task_definition_outputs(step_run, input_context)
        output_context = cls._get_output_context(task_definition_outputs, step_run)
        context = deepcopy(input_context)
        context.update(output_context)
        task_definition = cls._create_task_definition(step_run, task_definition_inputs, task_definition_outputs, context)

        if task_definition.task_runs.count() > 0 and not get_setting('FORCE_RERUN'):
            # Re-use an old TaskRun
            task_run = task_definition.task_runs.first()
        else:
            # Create a new TaskRun
            task_run_inputs = cls._create_task_run_inputs(task_definition_inputs, input_set, step_run)
            task_run_outputs = cls._create_task_run_outputs(task_definition_outputs, step_run)
            resources = cls._get_task_run_resources(step_run.template.resources, input_context)
            task_run = cls._create_task_run(task_run_inputs, task_run_outputs, task_definition, resources)

        task_run.step_runs.add(step_run)
        return task_run

    @classmethod
    def _get_input_context(cls, input_set):
        context = {}
        for input_item in input_set:
            context[input_item.channel] = input_item.data_object.get_content().get_substitution_value()
        return context
        
    @classmethod
    def _get_output_context(cls, task_definition_outputs, step_run):
        context = {}
        for (task_definition_output, step_run_output) in zip(task_definition_outputs, step_run.outputs.all()):
            context[step_run_output.channel] = task_definition_output.get_substitution_value()
        return context

    @classmethod
    def _create_task_definition_inputs(cls, input_set):
        return [cls._create_task_definition_input(input_item) for input_item in input_set]

    @classmethod
    def _create_task_definition_input(cls, input_item):
        return TaskDefinitionInput.create({
            'data_object_content': input_item.data_object.get_content(),
            'type': input_item.data_object.get_type()
        })

    @classmethod
    def _create_task_definition_outputs(cls, step_run, input_context):
        return [cls._create_task_definition_output(output, input_context) for output in step_run.outputs.all()]

    @classmethod
    def _create_task_definition_output(cls, step_run_output, input_context):
        return TaskDefinitionOutput.create({
            'filename': cls._render_from_template(step_run_output.get_filename(), input_context),
            'type': step_run_output.get_type()
        })

    @classmethod
    def _create_task_definition(cls, step_run, task_definition_inputs, task_definition_outputs, context):
        task_definition = TaskDefinition.create({
            'inputs': task_definition_inputs,
            'outputs': task_definition_outputs,
            'command': cls._render_from_template(step_run.template.command, context),
            'environment': cls._get_task_definition_environment(step_run.template.environment),
        })
        return task_definition

    @classmethod
    def _create_task_run_inputs(cls, task_definition_inputs, input_sets, step_run):
        return [cls._create_task_run_input(task_definition_input, input_item, step_run) for (task_definition_input, input_item) in zip(task_definition_inputs, input_sets)]

    @classmethod
    def _create_task_run_input(cls, task_definition_input, input_item, step_run):
        task_run_input = TaskRunInput.create(
            {
                'task_definition_input': task_definition_input,
                'data_object': input_item.data_object,
            }
        )
        task_run_input.step_run_inputs.add(step_run.get_input(input_item.channel))
        return task_run_input

    @classmethod
    def _create_task_run_outputs(cls, task_definition_outputs, step_run):
        return [cls._create_task_run_output(task_definition_output, step_run_output)
                for (task_definition_output, step_run_output)
                in zip(task_definition_outputs, step_run.outputs.all())]

    @classmethod
    def _create_task_run_output(cls, task_definition_output, step_run_output):
        task_run_output = TaskRunOutput.create({
            'task_definition_output': task_definition_output,
        })
        task_run_output.step_run_outputs.add(step_run_output)
        return task_run_output


    @classmethod
    def _create_task_run(cls, task_run_inputs, task_run_outputs, task_definition, resources):
        return TaskRun.create({
            'inputs': task_run_inputs,
            'outputs': task_run_outputs,
            'task_definition': task_definition,
            'resources': resources,
        })

    @classmethod
    def _get_task_run_resources(cls, step_resources, input_context):
        return {
            'cores': cls._render_from_template(step_resources.cores, input_context),
            'memory': cls._render_from_template(step_resources.memory, input_context),
            'disk_space': cls._render_from_template(step_resources.disk_space, input_context),
        }

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

