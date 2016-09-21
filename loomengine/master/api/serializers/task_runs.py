from rest_framework import serializers

from .base import CreateWithParentModelSerializer, SuperclassModelSerializer
from api.models.task_runs import TaskRun, TaskRunInput, TaskRunOutput,\
    TaskRunAttempt, TaskRunAttemptInput, TaskRunAttemptOutput, \
    TaskRunAttemptLogFile
from api.serializers.data_objects import FileImportSerializer, DataObjectSerializer, FileDataObjectSerializer
from api.serializers.task_definitions import TaskDefinitionSerializer
from api.serializers.workflows import RequestedResourceSetSerializer


class TaskRunAttemptOutputSerializer(CreateWithParentModelSerializer):

    data_object = DataObjectSerializer(allow_null=True, required=False)
    type = serializers.CharField(read_only=True)
    channel = serializers.CharField(read_only=True)
    filename = serializers.CharField(read_only=True)

    class Meta:
        model = TaskRunAttemptOutput
        fields = ('id', 'data_object', 'filename', 'type', 'channel',)

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


class TaskRunAttemptSerializer(serializers.ModelSerializer):

    id = serializers.UUIDField(format='hex', required=False)
    name = serializers.CharField(required=False)
    log_files = TaskRunAttemptLogFileSerializer(many=True, allow_null=True, required=False)
    inputs = TaskRunAttemptInputSerializer(many=True, allow_null=True, required=False)
    outputs = TaskRunAttemptOutputSerializer(many=True, allow_null=True, required=False)
    task_definition = TaskDefinitionSerializer(required=False)

    class Meta:
        model = TaskRunAttempt
        fields = ('id', 'name', 'log_files', 'inputs', 'outputs',
                  'container_id', 'task_definition',
                  'status', 'status_message',
                  'process_status', 'process_status_message',
                  'monitor_status', 'monitor_status_message',
                  'host_status')

    def update(self, instance, validated_data):
        # Only updates to status fields are allowed
        status = validated_data.pop('status', None)
        status_message = validated_data.pop('status_message', None)
        host_status = validated_data.pop('host_status', None)
        process_status = validated_data.pop('process_status', None)
        monitor_status = validated_data.pop('monitor_status', None)
        process_status_message = validated_data.pop('process_status_message', None)
        monitor_status_message = validated_data.pop('monitor_status_message', None)

        if status is not None:
            instance.status = status
        if status_message is not None:
            instance.status_message = status_message
        if host_status is not None:
            instance.host_status = host_status
        if process_status is not None:
            instance.process_status = process_status
        if monitor_status is not None:
            instance.monitor_status = monitor_status
        if process_status_message is not None:
            instance.process_status_message = process_status_message
        if monitor_status_message is not None:
            instance.monitor_status_message = monitor_status_message

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
    filename = serializers.CharField(read_only=True)

    class Meta:
        model = TaskRunOutput
        fields = ('data_object', 'filename', 'type', 'channel',)


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

    class Meta:
        model = TaskRun
        fields = ('id', 'name', 'task_definition', 'resources', 'inputs', 'outputs', 'task_run_attempts',)
