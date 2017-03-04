from rest_framework import serializers
from django.db import transaction

from api.exceptions import *
from .base import CreateWithParentModelSerializer, SuperclassModelSerializer, \
    UuidSerializer
from api.models.data_objects import FileDataObject
from api.models.tasks import Task, TaskInput, TaskOutput, \
    TaskResourceSet, TaskEnvironment, TaskAttempt, TaskAttemptOutput, \
    TaskAttemptLogFile, TaskAttemptTimepoint, TaskTimepoint
from api.serializers.data_objects import DataObjectSerializer, DataObjectUuidSerializer, FileDataObjectSerializer



class TaskResourceSetSerializer(CreateWithParentModelSerializer):

    class Meta:
        model = TaskResourceSet
        fields = ('memory', 'disk_size', 'cores',)


class TaskEnvironmentSerializer(CreateWithParentModelSerializer):

    class Meta:
        model = TaskEnvironment
        fields = ('docker_image',)

class TaskTimepointSerializer(CreateWithParentModelSerializer):

    class Meta:
        model = TaskTimepoint
        fields = ('message', 'detail', 'timestamp', 'is_error')


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


class TaskAttemptTimepointSerializer(CreateWithParentModelSerializer):

    class Meta:
        model = TaskAttemptTimepoint
        fields = ('message', 'detail', 'timestamp', 'is_error')


class TaskAttemptSerializer(serializers.ModelSerializer):

    uuid = serializers.CharField(required=False)
    log_files = TaskAttemptLogFileSerializer(
        many=True, allow_null=True, required=False)
    inputs = TaskInputSerializer(many=True, allow_null=True, required=False)
    outputs = TaskAttemptOutputSerializer(
        many=True, allow_null=True, required=False)
    timepoints = TaskAttemptTimepointSerializer(
        many=True, allow_null=True, required=False)
    resources = TaskResourceSetSerializer(read_only=True)
    environment = TaskEnvironmentSerializer(read_only=True)
    status_detail = serializers.CharField(required=False, allow_null=True)
    
    class Meta:
        model = TaskAttempt
        fields = ('uuid', 'datetime_created', 'datetime_finished', 
                  'last_heartbeat', 'status_message', 'status_detail',
                  'status_is_finished', 'status_is_failed', 'status_is_killed',
                  'status_is_running', 'status_is_cleaned_up',
                  'log_files', 'inputs', 'outputs', 'interpreter', 
                  'rendered_command', 'environment', 'resources', 'timepoints')
                  

    @transaction.atomic
    def update(self, instance, validated_data):
        instance = self.Meta.model.objects.get(uuid=instance.uuid)
        # Only updates to status message fields,
        # status_is_finished, status_is_failed, and status_is_running
        status_message = validated_data.pop('status_message', None)
        status_detail = validated_data.pop('status_detail', None)
        status_is_finished = validated_data.pop('status_is_finished', None)
        status_is_failed = validated_data.pop('status_is_failed', None)
        status_is_running = validated_data.pop('status_is_running', None)

        if status_message is not None:
            instance.status_message = status_message
        if status_detail is not None:
            instance.status_detail = status_detail
        if status_is_finished is not None:
            instance.status_is_finished = status_is_finished
        if status_is_failed is not None:
            instance.status_is_failed = status_is_failed
        if status_is_running is not None:
            instance.status_is_running = status_is_running
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
    selected_task_attempt = TaskAttemptSerializer(read_only=True)
    command = serializers.CharField(read_only=True)
    rendered_command = serializers.CharField(read_only=True)
    interpreter = serializers.CharField(read_only=True)
    datetime_finished = serializers.CharField(read_only=True)
    datetime_created = serializers.CharField(read_only=True)
    status_message = serializers.CharField(read_only=True)
    status_detail = serializers.CharField(read_only=True)
    status_is_finished = serializers.BooleanField(read_only=True)
    status_is_failed = serializers.BooleanField(read_only=True)
    status_is_killed = serializers.BooleanField(read_only=True)
    status_is_running = serializers.BooleanField(read_only=True)
    attempt_number = serializers.IntegerField(read_only=True)
    timepoints = TaskTimepointSerializer(
        many=True, allow_null=True, required=False)

    class Meta:
        model = Task
        fields = ('uuid', 'resources', 'environment', 'inputs', 
                  'outputs', 'task_attempts', 'selected_task_attempt', 
                  'command', 'rendered_command', 'interpreter',
                  'datetime_finished', 'datetime_created',
                  'status_message', 'status_detail',
                  'status_is_finished', 'status_is_failed', 'status_is_killed',
                  'status_is_running', 'attempt_number', 'timepoints')

class TaskUuidSerializer(UuidSerializer, TaskSerializer):
    pass

