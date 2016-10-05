from rest_framework import serializers

from .base import CreateWithParentModelSerializer, SuperclassModelSerializer
from api.models.task_runs import TaskRun, TaskRunInput, TaskRunOutput,\
    TaskRunAttempt, TaskRunAttemptInput, TaskRunAttemptOutput, \
    TaskRunAttemptOutput, TaskRunAttemptLogFile, TaskRunAttemptError
from api.serializers.data_objects import FileImportSerializer, DataObjectSerializer, FileDataObjectSerializer
from api.serializers.task_definitions import TaskDefinitionSerializer, TaskDefinitionOutputSourceSerializer
from api.serializers.workflows import RequestedResourceSetSerializer


class TaskRunAttemptOutputSerializer(CreateWithParentModelSerializer):

    data_object = DataObjectSerializer(allow_null=True, required=False)
    type = serializers.CharField(read_only=True)
    channel = serializers.CharField(read_only=True)
    source = TaskDefinitionOutputSourceSerializer(read_only=True)

    class Meta:
        model = TaskRunAttemptOutput
        fields = ('id', 'data_object', 'type', 'channel', 'source')

    def update(self, instance, validated_data):
        data_object_data = self.initial_data.get('data_object', None)
        validated_data.pop('data_object', None)

        s = DataObjectSerializer(data=data_object_data)
        s.is_valid(raise_exception=True)
        validated_data['data_object'] = s.save()

        return super(self.__class__, self).update(
            instance,
            validated_data)


class TaskRunAttemptInputSerializer(CreateWithParentModelSerializer):

    data_object = DataObjectSerializer(allow_null=True, required=False)
    type = serializers.CharField(read_only=True)
    channel = serializers.CharField(read_only=True)

    class Meta:
        model = TaskRunAttemptInput
        fields = ('id', 'data_object', 'type', 'channel',)


class TaskRunAttemptLogFileSerializer(CreateWithParentModelSerializer):

    file_data_object = FileDataObjectSerializer(allow_null=True, required=False)

    class Meta:
        model = TaskRunAttemptLogFile
        fields = ('log_name', 'file_data_object',)


class TaskRunAttemptErrorSerializer(CreateWithParentModelSerializer):

    class Meta:
        model = TaskRunAttemptError
        fields = ('message', 'detail')


class TaskRunAttemptSerializer(serializers.ModelSerializer):

    id = serializers.UUIDField(format='hex', required=False)
    name = serializers.CharField(required=False)
    log_files = TaskRunAttemptLogFileSerializer(many=True, allow_null=True, required=False)
    inputs = TaskRunAttemptInputSerializer(many=True, allow_null=True, required=False)
    outputs = TaskRunAttemptOutputSerializer(many=True, allow_null=True, required=False)
    task_definition = TaskDefinitionSerializer(required=False)
    errors = TaskRunAttemptErrorSerializer(many=True, allow_null=True, required=False)

    class Meta:
        model = TaskRunAttempt
        fields = ('id', 'name', 'log_files', 'inputs', 'outputs',
                  'container_id', 'task_definition',
                  'status', 'errors',)

    def update(self, instance, validated_data):
        # Only updates to status field is allowed
        status = validated_data.pop('status', None)
        
        if status is not None:
            instance.status = status

        instance.save()
        return instance

class TaskRunInputSerializer(CreateWithParentModelSerializer):

    data_object = DataObjectSerializer()
    type = serializers.CharField(read_only=True)
    channel = serializers.CharField(read_only=True)

    class Meta:
        model = TaskRunInput
        fields = ('data_object', 'type', 'channel',)


class TaskRunOutputSerializer(CreateWithParentModelSerializer):

    data_object = DataObjectSerializer()
    type = serializers.CharField(read_only=True)
    channel = serializers.CharField(read_only=True)
    source = TaskDefinitionOutputSourceSerializer(read_only=True)

    class Meta:
        model = TaskRunOutput
        fields = ('data_object', 'source', 'type', 'channel',)


class TaskRunIdSerializer(serializers.ModelSerializer):

    id = serializers.UUIDField(format='hex', required=False)

    class Meta:
        model = TaskRun
        fields = ('id',)


class TaskRunSerializer(serializers.ModelSerializer):

    id = serializers.UUIDField(format='hex', required=False)
    name = serializers.CharField()
    task_definition = TaskDefinitionSerializer()
    resources = RequestedResourceSetSerializer()
    inputs = TaskRunInputSerializer(many=True, allow_null=True, required=False)
    outputs = TaskRunOutputSerializer(many=True, allow_null=True, required=False)
    task_run_attempts = TaskRunAttemptSerializer(many=True, allow_null=True, required=False)
    errors = TaskRunAttemptErrorSerializer(many=True, read_only=True)

    class Meta:
        model = TaskRun
        fields = ('id', 'name', 'task_definition', 'resources', 'inputs', 'outputs', 'task_run_attempts',
                  'status', 'errors')
