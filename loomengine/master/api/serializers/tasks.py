from rest_framework import serializers

from .base import CreateWithParentModelSerializer, SuperclassModelSerializer
from api.models.tasks import Task, TaskInput, TaskOutput, TaskOutputSource, \
    TaskResourceSet, TaskEnvironment, TaskAttempt, TaskAttemptOutput, \
    TaskAttemptLogFile, TaskAttemptError
from api.serializers.data_objects import DataObjectSerializer, FileDataObjectSerializer
from api.serializers.workflows import RequestedResourceSetSerializer


class TaskOutputSourceSerializer(CreateWithParentModelSerializer):

    filename = serializers.CharField(read_only=True, required=False)
    stream = serializers.CharField(read_only=True, required=False)

    class Meta:
        model = TaskOutputSource
        fields = ('filename', 'stream')


class TaskAttemptOutputSerializer(CreateWithParentModelSerializer):

    data_object = DataObjectSerializer(allow_null=True, required=False)
    type = serializers.CharField(read_only=True)
    channel = serializers.CharField(read_only=True)
    source = TaskOutputSourceSerializer(read_only=True)
    # parser = TaskDefinitionOutputParserSerializer(read_only=True)

    class Meta:
        model = TaskAttemptOutput
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


class TaskInputSerializer(CreateWithParentModelSerializer):

    data_object = DataObjectSerializer(allow_null=True, required=False)
    type = serializers.CharField(read_only=True)
    channel = serializers.CharField(read_only=True)

    class Meta:
        model = TaskInput
        fields = ('id', 'data_object', 'type', 'channel',)


class TaskAttemptLogFileSerializer(CreateWithParentModelSerializer):

    file_data_object = FileDataObjectSerializer(allow_null=True, required=False)

    class Meta:
        model = TaskAttemptLogFile
        fields = ('log_name', 'file_data_object',)


class TaskAttemptErrorSerializer(CreateWithParentModelSerializer):

    class Meta:
        model = TaskAttemptError
        fields = ('message', 'detail')


class TaskAttemptSerializer(serializers.ModelSerializer):

    id = serializers.UUIDField(format='hex', required=False)
    name = serializers.CharField(required=False)
    log_files = TaskAttemptLogFileSerializer(many=True, allow_null=True, required=False)
    inputs = TaskInputSerializer(many=True, allow_null=True, required=False)
    outputs = TaskAttemptOutputSerializer(many=True, allow_null=True, required=False)
    errors = TaskAttemptErrorSerializer(many=True, allow_null=True, required=False)

    class Meta:
        model = TaskAttempt
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

class TaskInputSerializer(CreateWithParentModelSerializer):

    data_object = DataObjectSerializer(read_only=True)
    type = serializers.CharField(read_only=True)
    channel = serializers.CharField(read_only=True)

    class Meta:
        model = TaskInput
        fields = ('data_object', 'type', 'channel',)


class TaskOutputSerializer(CreateWithParentModelSerializer):

    data_object = DataObjectSerializer(read_only=True)
    type = serializers.CharField(read_only=True)
    channel = serializers.CharField(read_only=True)
    source = TaskOutputSourceSerializer(read_only=True)

    class Meta:
        model = TaskOutput
        fields = ('data_object', 'source', 'type', 'channel')


class TaskIdSerializer(serializers.ModelSerializer):

    id = serializers.UUIDField(format='hex', required=False)

    class Meta:
        model = Task
        fields = ('id',)


class TaskSerializer(serializers.ModelSerializer):

    id = serializers.UUIDField(format='hex', read_only=True)
    resources = RequestedResourceSetSerializer(read_only=True)
    inputs = TaskInputSerializer(many=True, read_only=True)
    outputs = TaskOutputSerializer(many=True, read_only=True)
    task_attempts = TaskAttemptSerializer(many=True, read_only=True)
    accepted_task_attempt = TaskAttemptSerializer(read_only=True)
    status = serializers.CharField(read_only=True)
    errors = TaskAttemptErrorSerializer(many=True, read_only=True)
    command = serializers.CharField(read_only=True)
    rendered_command = serializers.CharField(read_only=True)
    interpreter = serializers.CharField(read_only=True)
    datetime_finished = serializers.CharField(read_only=True)
    datetime_created = serializers.CharField(read_only=True)

    class Meta:
        model = Task
        fields = ('id', 'resources', 'inputs', 'outputs', 'task_attempts',
                  'accepted_task_attempt', 'status', 'errors', 'command',
                  'rendered_command', 'interpreter', 'datetime_finished',
                  'datetime_created')
