from rest_framework import serializers

from .base import CreateWithParentModelSerializer, SuperclassModelSerializer, \
    UuidSerializer
from api.models.data_objects import FileDataObject
from api.models.tasks import Task, TaskInput, TaskOutput, \
    TaskResourceSet, TaskEnvironment, TaskAttempt, TaskAttemptOutput, \
    TaskAttemptLogFile, TaskAttemptError
from api.serializers.data_objects import DataObjectSerializer, DataObjectUuidSerializer, FileDataObjectSerializer



class TaskResourceSetSerializer(CreateWithParentModelSerializer):

    class Meta:
        model = TaskResourceSet
        fields = ('memory', 'disk_size', 'cores',)


class TaskEnvironmentSerializer(CreateWithParentModelSerializer):

    class Meta:
        model = TaskEnvironment
        fields = ('docker_image',)


class TaskAttemptOutputSerializer(CreateWithParentModelSerializer):
    # Used for both TaskOutput and TaskAttemptOutput

    data_object = DataObjectUuidSerializer(allow_null=True, required=False)
    type = serializers.CharField(read_only=True)
    channel = serializers.CharField(read_only=True)
    source = serializers.JSONField(required=False)
    # parser = TaskDefinitionOutputParserSerializer(read_only=True)

    class Meta:
        model = TaskAttemptOutput
        fields = ('id', 'type', 'channel', 'source', 'data_object')

    def update(self, instance, validated_data):
        data_object_data = self.initial_data.get('data_object', None)
        validated_data.pop('data_object', None)

        if data_object_data:
            if not instance.data_object:
                if data_object_data.get('type') == 'file':
                    # We can't use the serializer because it fails to initialize
                    # the file data object when it isn't attached to a
                    # task_attempt_output
                    instance.data_object = FileDataObject.objects.create(
                        **data_object_data)
                    instance.save()
                    instance.data_object.initialize()
                else:
                    s = DataObjectSerializer(data=data_object_data)
                    s.is_valid(raise_exception=True)
                    validated_data['data_object'] = s.save()
            else:
                s = DataObjectSerializer(instance.data_object, data=data_object_data)
                s.is_valid(raise_exception=True)
                validated_data['data_object'] = s.save()
        return super(self.__class__, self).update(
            instance,
            validated_data)
                

class TaskInputSerializer(CreateWithParentModelSerializer):

    data_object = DataObjectUuidSerializer(allow_null=True, required=False)
    type = serializers.CharField(read_only=True)
    channel = serializers.CharField(read_only=True)

    class Meta:
        model = TaskInput
        fields = ('id', 'type', 'channel', 'data_object',)


class FullTaskInputSerializer(TaskInputSerializer):

    data_object = DataObjectSerializer(allow_null=True, required=False)


class TaskAttemptLogFileSerializer(CreateWithParentModelSerializer):

    file = DataObjectUuidSerializer(allow_null=True, required=False)

    class Meta:
        model = TaskAttemptLogFile
        fields = ('log_name', 'file',)


class TaskAttemptErrorSerializer(CreateWithParentModelSerializer):

    class Meta:
        model = TaskAttemptError
        fields = ('message', 'detail')


class TaskAttemptSerializer(serializers.ModelSerializer):

    uuid = serializers.CharField(required=False)
    log_files = TaskAttemptLogFileSerializer(
        many=True, allow_null=True, required=False)
    inputs = TaskInputSerializer(many=True, allow_null=True, required=False)
    outputs = TaskAttemptOutputSerializer(
        many=True, allow_null=True, required=False)
    errors = TaskAttemptErrorSerializer(
        many=True, allow_null=True, required=False)
    resources = TaskResourceSetSerializer(read_only=True)
    environment = TaskEnvironmentSerializer(read_only=True)
    is_active = serializers.BooleanField(required=False)
    status_message_detail = serializers.CharField(required=False, allow_null=True)
    
    class Meta:
        model = TaskAttempt
        fields = ('uuid', 'datetime_created', 'datetime_finished', 
                  'last_heartbeat', 'status_message', 'status_message_detail',
                  'status_is_finished', 'status_is_failed',
                  'errors', 'log_files', 'inputs', 'outputs',
                  'interpreter', 'rendered_command', 'environment',
                  'resources', 'is_active')

    def update(self, instance, validated_data):
        # Only updates to status fields are allowed
        status_message = validated_data.pop('status_message', None)
        status_message_detail = validated_data.pop('status_message_detail', None)
        status_is_finished = validated_data.pop('status_is_finished', None)
        status_is_failed = validated_data.pop('status_is_failed', None)

        if status_message is not None:
            instance.status_message = status_message
        if status_message_detail is not None:
            instance.status_message_detail = status_message_detail
        if status_is_finished is not None:
            instance.status_is_finished = status_is_finished
        if status_is_failed is not None:
            instance.status_is_failed = status_is_failed

        instance.save()
        return instance


class TaskAttemptUuidSerializer(UuidSerializer, TaskAttemptSerializer):
    pass


class TaskInputSerializer(CreateWithParentModelSerializer):

    data_object = DataObjectUuidSerializer(read_only=True)
    type = serializers.CharField(read_only=True)
    channel = serializers.CharField(read_only=True)

    class Meta:
        model = TaskInput
        fields = ('data_object', 'type', 'channel',)


class TaskOutputSerializer(CreateWithParentModelSerializer):

    data_object = DataObjectUuidSerializer(read_only=True)
    type = serializers.CharField(read_only=True)
    channel = serializers.CharField(read_only=True)
    source = serializers.JSONField(required=False)

    class Meta:
        model = TaskOutput
        fields = ('data_object', 'source', 'type', 'channel')


class TaskSerializer(serializers.ModelSerializer):

    uuid = serializers.CharField(required=False, read_only=True)
    resources = TaskResourceSetSerializer(read_only=True)
    environment = TaskEnvironmentSerializer(read_only=True)
    inputs = TaskInputSerializer(many=True, read_only=True)
    outputs = TaskOutputSerializer(many=True, read_only=True)
    task_attempts = TaskAttemptUuidSerializer(many=True, read_only=True)
    active_task_attempt = TaskAttemptSerializer(read_only=True)
    command = serializers.CharField(read_only=True)
    rendered_command = serializers.CharField(read_only=True)
    interpreter = serializers.CharField(read_only=True)
    datetime_finished = serializers.CharField(read_only=True)
    datetime_created = serializers.CharField(read_only=True)
    active = serializers.BooleanField(read_only=True)
    status_message = serializers.CharField(read_only=True)
    status_message_detail = serializers.CharField(read_only=True)
    status_is_finished = serializers.BooleanField(read_only=True)
    status_is_failed = serializers.BooleanField(read_only=True)
    attempt_number = serializers.IntegerField(read_only=True)

    class Meta:
        model = Task
        fields = ('uuid', 'resources', 'environment', 'inputs', 
                  'outputs', 'task_attempts', 'active_task_attempt', 
                  'command', 'rendered_command', 'interpreter', 
                  'datetime_finished', 'datetime_created', 'active',
                  'status_message', 'status_message_detail',
                  'status_is_finished', 'status_is_failed',
                  'attempt_number')

class TaskUuidSerializer(UuidSerializer, TaskSerializer):
    pass

