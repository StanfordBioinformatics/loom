from rest_framework import serializers

from .base import CreateWithParentModelSerializer, SuperclassModelSerializer
from api.models.tasks import Task, TaskInput, TaskOutput, TaskOutputSource, \
    TaskResourceSet, TaskEnvironment, TaskAttempt, TaskAttemptOutput, \
    TaskAttemptLogFile, TaskAttemptError
from api.serializers.data_objects import DataObjectSerializer, DataObjectIdSerializer, FileDataObjectSerializer


class TaskResourceSetSerializer(CreateWithParentModelSerializer):

    class Meta:
        model = TaskResourceSet
        fields = ('memory', 'disk_size', 'cores',)


class TaskEnvironmentSerializer(CreateWithParentModelSerializer):

    class Meta:
        model = TaskEnvironment
        fields = ('docker_image',)


class TaskOutputSourceSerializer(CreateWithParentModelSerializer):

    filename = serializers.CharField(read_only=True, required=False)
    stream = serializers.CharField(read_only=True, required=False)

    class Meta:
        model = TaskOutputSource
        fields = ('filename', 'stream')


class TaskAttemptOutputSerializer(CreateWithParentModelSerializer):
    # Used for both TaskOutput and TaskAttemptOutput

    data_object = DataObjectIdSerializer(allow_null=True, required=False)
    type = serializers.CharField(read_only=True)
    channel = serializers.CharField(read_only=True)
    source = TaskOutputSourceSerializer(read_only=True)
    # parser = TaskDefinitionOutputParserSerializer(read_only=True)

    class Meta:
        model = TaskAttemptOutput
        fields = ('id', 'type', 'channel', 'source', 'data_object')

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

    data_object = DataObjectIdSerializer(allow_null=True, required=False)
    type = serializers.CharField(read_only=True)
    channel = serializers.CharField(read_only=True)

    class Meta:
        model = TaskInput
        fields = ('id', 'type', 'channel', 'data_object',)


class FullTaskInputSerializer(TaskInputSerializer):

    data_object = DataObjectSerializer(allow_null=True, required=False)


class TaskAttemptLogFileSerializer(CreateWithParentModelSerializer):

    file = DataObjectIdSerializer(allow_null=True, required=False)

    class Meta:
        model = TaskAttemptLogFile
        fields = ('log_name', 'file',)


class TaskAttemptErrorSerializer(CreateWithParentModelSerializer):

    class Meta:
        model = TaskAttemptError
        fields = ('message', 'detail')


class TaskAttemptSerializer(serializers.ModelSerializer):

    id = serializers.UUIDField(format='hex', required=False)
    name = serializers.CharField(required=False)
    log_files = TaskAttemptLogFileSerializer(
        many=True, allow_null=True, required=False)
    inputs = TaskInputSerializer(many=True, allow_null=True, required=False)
    outputs = TaskAttemptOutputSerializer(
        many=True, allow_null=True, required=False)
    errors = TaskAttemptErrorSerializer(
        many=True, allow_null=True, required=False)
    resources = TaskResourceSetSerializer(read_only=True)
    environment = TaskEnvironmentSerializer(read_only=True)

    class Meta:
        model = TaskAttempt
        fields = ('id', 'datetime_created', 'datetime_finished', 
                  'last_heartbeat', 'status', 'errors', 'log_files', 
                  'inputs', 'outputs', 'name', 'interpreter', 
                  'rendered_command', 'environment', 'resources')

    def update(self, instance, validated_data):
        # Only updates to status field is allowed
        status = validated_data.pop('status', None)

        if status is not None:
            instance.status = status

        instance.save()
        return instance


class TaskAttemptIdSerializer(TaskAttemptSerializer):
    # Renders only the "id" field for deferred lookup

    def to_representation(self, instance):
        if not isinstance(instance, models.Model):
            # If the Serializer was instantiated with data instead of a model,
            # "instance" is an OrderedDict. It may be missing data in fields
            # that are on the subclass but not on the superclass, so we go
            # back to initial_data.
            return { 'id': instance.get('id') }
        else:
            assert isinstance(instance, self.Meta.model)
            # Execute "to_representation" on the correct subclass serializer
            return { 'id': instance.id.hex }


class TaskInputSerializer(CreateWithParentModelSerializer):

    data_object = DataObjectIdSerializer(read_only=True)
    type = serializers.CharField(read_only=True)
    channel = serializers.CharField(read_only=True)

    class Meta:
        model = TaskInput
        fields = ('data_object', 'type', 'channel',)


class TaskOutputSerializer(CreateWithParentModelSerializer):

    data_object = DataObjectIdSerializer(read_only=True)
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
    resources = TaskResourceSetSerializer(read_only=True)
    environment = TaskEnvironmentSerializer(read_only=True)
    inputs = TaskInputSerializer(many=True, read_only=True)
    outputs = TaskOutputSerializer(many=True, read_only=True)
    task_attempts = TaskAttemptSerializer(many=True, read_only=True)
    accepted_task_attempt = TaskAttemptSerializer(read_only=True)
    status = serializers.CharField(read_only=True)
#    errors = TaskAttemptErrorSerializer(many=True, read_only=True)
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
