from rest_framework import serializers

from . import CreateWithParentModelSerializer, strip_empty_values
from api.models.data_objects import DataObject
from api.models.tasks import Task, TaskInput, TaskOutput, \
    TaskEvent
from api.serializers.data_channels import DataChannelSerializer, \
    ExpandedDataChannelSerializer
from api.serializers.task_attempts import TaskAttemptSerializer, \
    URLTaskAttemptSerializer, ExpandedTaskAttemptSerializer


class TaskEventSerializer(CreateWithParentModelSerializer):

    class Meta:
        model = TaskEvent
        fields = ('event', 'detail', 'timestamp', 'is_error')


class TaskInputSerializer(DataChannelSerializer):

    class Meta:
        model = TaskInput
        fields = ('data', 'type', 'channel', 'as_channel',  'mode')

    mode = serializers.CharField()
    as_channel = serializers.CharField(required=False, allow_null=True)


class ExpandedTaskInputSerializer(ExpandedDataChannelSerializer):

    class Meta:
        model = TaskInput
        fields = ('data', 'type', 'channel', 'as_channel',  'mode')

    mode = serializers.CharField()
    as_channel = serializers.CharField(required=False, allow_null=True)


class TaskOutputSerializer(DataChannelSerializer):

    class Meta:
        model = TaskOutput
        fields = ('type', 'channel', 'as_channel', 'data', 'mode', 'source', 'parser')

    mode = serializers.CharField()
    source = serializers.JSONField(required=False)
    parser = serializers.JSONField(required=False, allow_null=True)
    as_channel = serializers.CharField(required=False, allow_null=True)


class ExpandedTaskOutputSerializer(ExpandedDataChannelSerializer):

    class Meta:
        model = TaskOutput
        fields = ('type', 'channel', 'as_channel', 'data', 'mode', 'source', 'parser')

    mode = serializers.CharField()
    source = serializers.JSONField(required=False)
    parser = serializers.JSONField(required=False, allow_null=True)
    as_channel = serializers.CharField(required=False, allow_null=True)


_task_serializer_fields = [
    'uuid',
    'url',
    'status',
    'resources',
    'environment',
    'inputs',
    'outputs',
    'all_task_attempts',
    'task_attempt',
    'raw_command',
    'command',
    'interpreter',
    'datetime_finished',
    'datetime_created',
    'status_is_finished',
    'status_is_failed',
    'status_is_killed',
    'status_is_running',
    'status_is_waiting',
    'events',
    'data_path',
    'analysis_failure_count',
    'system_failure_count',
]


class TaskSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Task
        fields = _task_serializer_fields

    uuid = serializers.CharField(required=False)
    url = serializers.HyperlinkedIdentityField(
        view_name='task-detail',
        lookup_field='uuid')
    resources = serializers.JSONField(required=False)
    environment = serializers.JSONField(required=False)
    inputs = TaskInputSerializer(many=True)
    outputs = TaskOutputSerializer(many=True)
    all_task_attempts = TaskAttemptSerializer(many=True)
    task_attempt = TaskAttemptSerializer(required=False)
    raw_command = serializers.CharField(required=False)
    command = serializers.CharField(required=False)
    interpreter = serializers.CharField(required=False)
    datetime_finished = serializers.DateTimeField(format='iso-8601')
    datetime_created = serializers.DateTimeField(format='iso-8601')
    status_is_finished = serializers.BooleanField(required=False)
    status_is_failed = serializers.BooleanField(required=False)
    status_is_killed = serializers.BooleanField(required=False)
    status_is_running = serializers.BooleanField(required=False)
    status_is_waiting = serializers.BooleanField(required=False)
    analysis_failure_count = serializers.IntegerField(required=False)
    system_failure_count = serializers.IntegerField(required=False)
    events = TaskEventSerializer(
        many=True, allow_null=True, required=False)
    data_path = serializers.JSONField(required=True)

    # read-only
    status = serializers.CharField(read_only=True)

    def to_representation(self, instance):
        if not hasattr(instance, '_prefetched_objects_cache'):
            self._prefetch_instance(instance)
        return strip_empty_values(
            super(TaskSerializer, self).to_representation(instance))

    def _prefetch_instance(self, instance):
        queryset = Task\
                   .objects\
                   .filter(uuid=instance.uuid)\
                   .prefetch_related('inputs')\
                   .prefetch_related('inputs__data_node')\
                   .prefetch_related('inputs__data_node__data_object')\
                   .prefetch_related('inputs__data_node__data_object__file_resource')\
                   .prefetch_related('outputs')\
                   .prefetch_related('outputs__data_node')\
                   .prefetch_related('outputs__data_node__data_object')\
                   .prefetch_related('outputs__data_node__data_object__file_resource')\
                   .prefetch_related('events')\
                   .prefetch_related('all_task_attempts')\
                   .prefetch_related('all_task_attempts__inputs')\
                   .prefetch_related('all_task_attempts__inputs__data_node')\
                   .prefetch_related(
                       'all_task_attempts__inputs__data_node__data_object')\
                   .prefetch_related(
                       'all_task_attempts__inputs__data_node__data_object__file_resource')\
                   .prefetch_related('all_task_attempts__outputs')\
                   .prefetch_related('all_task_attempts__outputs__data_node')\
                   .prefetch_related(
                       'all_task_attempts__outputs__data_node__data_object')\
                   .prefetch_related(
                       'all_task_attempts__outputs__data_node__data_object__file_resource')\
                   .prefetch_related('all_task_attempts__events')\
                   .prefetch_related('all_task_attempts__log_files')\
                   .prefetch_related('all_task_attempts__log_files__data_object')\
                   .prefetch_related(
                       'all_task_attempts__log_files__data_object__file_resource')\
                   .prefetch_related('task_attempt')\
                   .prefetch_related('task_attempt__inputs')\
                   .prefetch_related('task_attempt__inputs__data_node')\
                   .prefetch_related(
                       'task_attempt__inputs__data_node__data_object')\
                   .prefetch_related(
                       'task_attempt__inputs__data_node__data_object__file_resource')\
                   .prefetch_related('task_attempt__outputs')\
                   .prefetch_related('task_attempt__outputs__data_node')\
                   .prefetch_related(
                       'task_attempt__outputs__data_node__data_object')\
                   .prefetch_related(
                       'task_attempt__outputs__data_node__data_object__file_resource')\
                   .prefetch_related('task_attempt__events')\
                   .prefetch_related('task_attempt__log_files')\
                   .prefetch_related('task_attempt__log_files__data_object')\
                   .prefetch_related(
                       'task_attempt__log_files__data_object__file_resource')
        instance._prefetched_objects_cache = queryset[0]._prefetched_objects_cache
        
class ExpandedTaskSerializer(TaskSerializer):

    inputs = ExpandedTaskInputSerializer(many=True)
    outputs = ExpandedTaskOutputSerializer(many=True)
    all_task_attempts = ExpandedTaskAttemptSerializer(many=True)
    task_attempt = ExpandedTaskAttemptSerializer(required=False)


class URLTaskSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Task
        fields = _task_serializer_fields

    # readable
    uuid = serializers.CharField(required=False)
    url = serializers.HyperlinkedIdentityField(
        view_name='task-detail',
        lookup_field='uuid')
    datetime_finished = serializers.DateTimeField(format='iso-8601')
    datetime_created = serializers.DateTimeField(format='iso-8601')
    status = serializers.CharField(read_only=True)

    # write-only
    all_task_attempts = TaskAttemptSerializer(many=True, write_only=True)
    task_attempt = TaskAttemptSerializer(required=False, write_only=True)
    resources = serializers.JSONField(required=False, write_only=True)
    environment = serializers.JSONField(required=False, write_only=True)
    inputs = TaskInputSerializer(many=True, write_only=True)
    outputs = TaskOutputSerializer(many=True, write_only=True)
    raw_command = serializers.CharField(required=False, write_only=True)
    command = serializers.CharField(required=False, write_only=True)
    interpreter = serializers.CharField(required=False, write_only=True)
    status_is_finished = serializers.BooleanField(required=False, write_only=True)
    status_is_failed = serializers.BooleanField(required=False, write_only=True)
    status_is_killed = serializers.BooleanField(required=False, write_only=True)
    status_is_running = serializers.BooleanField(required=False, write_only=True)
    status_is_waiting = serializers.BooleanField(required=False, write_only=True)
    analysis_failure_count = serializers.IntegerField(required=False, write_only=True)
    system_failure_count = serializers.IntegerField(required=False, write_only=True)
    events = TaskEventSerializer(
        many=True, allow_null=True, required=False, write_only=True)
    data_path = serializers.JSONField(required=True, write_only=True)
