from rest_framework import serializers

from . import CreateWithParentModelSerializer
from api.models.task_attempts import TaskAttempt, TaskAttemptOutput, \
    TaskAttemptInput, TaskAttemptLogFile, TaskAttemptEvent
from api.serializers.data_objects import DataObjectSerializer
from api.serializers.data_channels import DataChannelSerializer, \
    ExpandedDataChannelSerializer


class TaskAttemptInputSerializer(DataChannelSerializer):

    class Meta:
        model = TaskAttemptInput
        fields = ('type', 'channel', 'data', 'mode')

    mode = serializers.CharField()


class TaskAttemptOutputSerializer(DataChannelSerializer):

    class Meta:
        model = TaskAttemptOutput
        fields = ('uuid', 'type', 'channel', 'data', 'mode', 'source', 'parser')

    source = serializers.JSONField(required=False)
    parser = serializers.JSONField(required=False)
    mode = serializers.CharField()


class TaskAttemptOutputUpdateSerializer(ExpandedDataChannelSerializer):
    """This class is needed because some fields that are allowed
    in "create" are not writable in "update".
    """

    class Meta:
        model = TaskAttemptOutput
        fields = ('uuid', 'type', 'channel', 'data', 'mode', 'source', 'parser')

    source = serializers.JSONField(read_only=True)
    parser = serializers.JSONField(read_only=True)


class TaskAttemptLogFileSerializer(CreateWithParentModelSerializer):

    class Meta:
        model = TaskAttemptLogFile
        fields = ('uuid', 'url', 'log_name', 'data_object')

    uuid = serializers.CharField(required=False)
    url = serializers.HyperlinkedIdentityField(
        view_name='task-attempt-log-file-detail',
        lookup_field='uuid')
    data_object = DataObjectSerializer(allow_null=True, required=False)

    def update(self, instance, validated_data):
        data_object_data = self.initial_data.get('data_object', None)
        validated_data.pop('data_object', None)

        if data_object_data:
            if data_object_data.get('type') \
               and not data_object_data.get('type') == 'file':
                raise serializers.ValidationError(
                    'Bad type "%s". Must be type "file".' %
                    data_object_data.get('type'))
            if instance.data_object:
                raise serializers.ValidationError(
                    'Updating existing nested file not allowed')
            
            s = DataObjectSerializer(data=dataobject_data,
                                     context={
                                         'request': self.request,
                                         'task_attempt': instance.task_attempt}
            )
            s.is_valid(raise_exception=True)
            s.save()
        return instance


class TaskAttemptEventSerializer(CreateWithParentModelSerializer):

    class Meta:
        model = TaskAttemptEvent
        fields = ('event', 'detail', 'timestamp', 'is_error')


class TaskAttemptSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = TaskAttempt
        fields = ['uuid',
                  'url',
                  'status',
                  'datetime_created',
                  'datetime_finished',
                  'last_heartbeat',
                  'status_is_finished',
                  'status_is_failed',
                  'status_is_killed',
                  'status_is_running',
                  'status_is_cleaned_up',
                  'log_files',
                  'inputs',
                  'outputs',
                  'interpreter',
                  'command',
                  'environment',
                  'environment_info',
                  'resources',
                  'resources_info',
                  'events'
        ]

    uuid = serializers.CharField(required=False)
    url = serializers.HyperlinkedIdentityField(
        view_name='task-attempt-detail',
        lookup_field='uuid')
    command = serializers.CharField(required=False)
    interpreter = serializers.CharField(required=False)
    log_files = TaskAttemptLogFileSerializer(
        many=True, allow_null=True, required=False)
    inputs = TaskAttemptInputSerializer(many=True, allow_null=True, required=False)
    outputs = TaskAttemptOutputSerializer(
        many=True, allow_null=True, required=False)
    events = TaskAttemptEventSerializer(
        many=True, allow_null=True, required=False)
    resources = serializers.JSONField(required=False)
    resources_info = serializers.JSONField(required=False)
    environment = serializers.JSONField(required=False)
    environment_info = serializers.JSONField(required=False)
    datetime_created = serializers.DateTimeField(required=False, format='iso-8601')
    datetime_finished = serializers.DateTimeField(required=False, format='iso-8601')
    last_heartbeat = serializers.DateTimeField(required=False, format='iso-8601')
    status = serializers.CharField(read_only=True)
    status_is_finished = serializers.BooleanField(required=False)
    status_is_failed = serializers.BooleanField(required=False)
    status_is_killed = serializers.BooleanField(required=False)
    status_is_running = serializers.BooleanField(required=False)
    status_is_cleaned_up = serializers.BooleanField(required=False)

    def update(self, instance, validated_data):
        instance = self.Meta.model.objects.get(uuid=instance.uuid)
        # Only updates to status message fields,
        # status_is_finished, status_is_failed, and status_is_running
        status_is_finished = validated_data.pop('status_is_finished', None)
        status_is_failed = validated_data.pop('status_is_failed', None)
        status_is_running = validated_data.pop('status_is_running', None)
        environment_info = validated_data.pop('environment_info', None)
        resources_info = validated_data.pop('resources_info', None)
        
        attributes = {}
        if status_is_finished is not None:
            attributes['status_is_finished'] = status_is_finished
        if status_is_failed is not None:
            attributes['status_is_failed'] = status_is_failed
        if status_is_running is not None:
            attributes['status_is_running'] = status_is_running
        if environment_info is not None:
            attributes['environment_info'] = environment_info
        if resources_info is not None:
            attributes['resources_info'] = resources_info
        instance = instance.setattrs_and_save_with_retries(attributes)
        return instance

    @classmethod
    def apply_prefetch(cls, queryset):
        queryset = queryset\
                   .prefetch_related('log_files')\
                   .prefetch_related('log_files__data_object__file_resource')\
                   .prefetch_related('inputs')\
                   .prefetch_related('inputs__data_node')\
                   .prefetch_related('outputs')\
                   .prefetch_related('outputs__data_node')\
                   .prefetch_related('outputs__data_node')\
                   .prefetch_related('events')
        return queryset


class URLTaskAttemptSerializer(TaskAttemptSerializer):

    class Meta:
        model = TaskAttempt
        fields = TaskAttemptSerializer.Meta.fields
    
    # readable
    uuid = serializers.CharField(required=False)
    url = serializers.HyperlinkedIdentityField(
        view_name='task-attempt-detail',
        lookup_field='uuid')
    status = serializers.CharField(read_only=True)
    datetime_created = serializers.DateTimeField(
        required=False, format='iso-8601')
    datetime_finished = serializers.DateTimeField(
        required=False, format='iso-8601')

    # write-only
    command = serializers.CharField(required=False, write_only=True)
    interpreter = serializers.CharField(required=False, write_only=True)
    log_files = TaskAttemptLogFileSerializer(
        many=True, allow_null=True, required=False, write_only=True)
    inputs = TaskAttemptInputSerializer(many=True, allow_null=True,
                                        required=False, write_only=True)
    outputs = TaskAttemptOutputSerializer(
        many=True, allow_null=True, required=False, write_only=True)
    events = TaskAttemptEventSerializer(
        many=True, allow_null=True, required=False, write_only=True)
    resources = serializers.JSONField(required=False, write_only=True)
    resources_info = serializers.JSONField(required=False, write_only=True)
    environment = serializers.JSONField(required=False, write_only=True)
    environment_info = serializers.JSONField(required=False, write_only=True)
    last_heartbeat = serializers.DateTimeField(
        required=False, format='iso-8601', write_only=True)
    status_is_finished = serializers.BooleanField(required=False, write_only=True)
    status_is_failed = serializers.BooleanField(required=False, write_only=True)
    status_is_killed = serializers.BooleanField(required=False, write_only=True)
    status_is_running = serializers.BooleanField(required=False, write_only=True)
    status_is_cleaned_up = serializers.BooleanField(required=False, write_only=True)

    @classmethod
    def apply_prefetch(cls, queryset):
        return queryset
