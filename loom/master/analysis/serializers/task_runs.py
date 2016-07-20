from .base import NestedPolymorphicModelSerializer, POLYMORPHIC_TYPE_FIELD
from analysis.models.task_runs import *
from analysis.serializers.data_objects import AbstractFileImportSerializer, DataObjectSerializer, FileDataObjectSerializer
from analysis.serializers.task_definitions import *
from analysis.serializers.workflows import RequestedResourceSetSerializer


class TaskRunAttemptOutputFileImportSerializer(AbstractFileImportSerializer):

    class Meta:
        model = TaskRunAttemptOutputFileImport


class TaskRunAttemptLogFileImportSerializer(AbstractFileImportSerializer):

    class Meta:
        model =TaskRunAttemptLogFileImport


class TaskRunAttemptOutputSerializer(NestedPolymorphicModelSerializer):

    data_object = DataObjectSerializer(allow_null=True, required=False)

    class Meta:
        model = TaskRunAttemptOutput


class TaskRunAttemptLogFileSerializer(NestedPolymorphicModelSerializer):

    file_data_object = FileDataObjectSerializer(allow_null=True, required=False)

    class Meta:
        model = TaskRunAttemptLogFile


class TaskRunAttemptSerializer(NestedPolymorphicModelSerializer):

    log_files = TaskRunAttemptLogFileSerializer(many=True, allow_null=True, required=False)
    outputs = TaskRunAttemptOutputSerializer(many=True, allow_null=True, required=False)

    class Meta:
        model = TaskRunAttempt


class MockTaskRunAttemptSerializer(TaskRunAttemptSerializer):

    class Meta:
        model = MockTaskRunAttempt


class LocalTaskRunAttemptSerializer(TaskRunAttemptSerializer):

    class Meta:
        model = LocalTaskRunAttempt


class GoogleCloudTaskRunAttemptSerializer(TaskRunAttemptSerializer):

    class Meta:
        model = GoogleCloudTaskRunAttempt


class TaskRunInputSerializer(NestedPolymorphicModelSerializer):

    data_object = DataObjectSerializer()

    class Meta:
        model = TaskRunInput
        nested_x_to_one_serializers = {
            'data_object': 'analysis.serializers.data_objects.DataObjectSerializer'
        }


class TaskRunOutputSerializer(NestedPolymorphicModelSerializer):

    data_object = DataObjectSerializer()

    class Meta:
        model = TaskRunOutput
        nested_x_to_one_serializers = {
            'data_object': 'analysis.serializers.data_objects.DataObjectSerializer'
        }


class TaskRunSerializer(NestedPolymorphicModelSerializer):

    task_definition = TaskDefinitionSerializer()
    resources = RequestedResourceSetSerializer()
    inputs = TaskRunInputSerializer(many=True, allow_null=True, required=False)
    outputs = TaskRunOutputSerializer(many=True, allow_null=True, required=False)
    task_run_attempts = TaskRunAttemptSerializer(many=True, allow_null=True, required=False)

    class Meta:
        model = TaskRun
        nested_x_to_one_serializers = {
            'task_definition': 'analysis.serializers.task_definitions.TaskDefinitionSerializer',
            'resources': 'analysis.serializers.workflows.RequestedResourceSet',
        }
        nested_x_to_many_serializers = {
            'inputs': 'analysis.serializers.task_runs.TaskRunInputSerializer',
            'outputs': 'analysis.serializers.task_runs.TaskRunOutputSerializer',
            'task_run_attempts': 'analysis.serializers.task_runs.TaskRunAttemptSerializer',
        }
