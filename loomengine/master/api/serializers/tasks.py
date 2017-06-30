from rest_framework import serializers

from . import CreateWithParentModelSerializer
from api.models.data_objects import DataObject
from api.models.tasks import Task, TaskInput, TaskOutput, \
    TaskTimepoint
from api.serializers.data_objects import DataObjectSerializer
from api.serializers.data_channels import DataChannelSerializer
from api.serializers.task_attempts import TaskAttemptSerializer, \
    URLTaskAttemptSerializer, SummaryTaskAttemptSerializer


class TaskTimepointSerializer(CreateWithParentModelSerializer):

    class Meta:
        model = TaskTimepoint
        fields = ('message', 'detail', 'timestamp', 'is_error')


class TaskInputSerializer(DataChannelSerializer):

    class Meta:
        model = TaskInput
        fields = ('data', 'type', 'channel', 'mode')

    mode = serializers.CharField(read_only=True)


class TaskOutputSerializer(DataChannelSerializer):

    class Meta:
        model = TaskOutput
        fields = ('type', 'channel', 'data', 'mode', 'source', 'parser')

    mode = serializers.CharField(read_only=True)
    source = serializers.JSONField(required=False)
    parser = serializers.JSONField(required=False)


class TaskSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Task
        _read_only_fields = ['status']
        _writable_fields = [
            'uuid',
            'url',
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
            'timepoints',
            'data_path',
        ]
        fields = _writable_fields + _read_only_fields

    uuid = serializers.CharField(required=False)
    url = serializers.HyperlinkedIdentityField(
        view_name='task-detail',
        lookup_field='uuid')
    resources = serializers.JSONField(required=False)
    environment = serializers.JSONField(required=False)
    inputs = TaskInputSerializer(many=True)
    outputs = TaskOutputSerializer(many=True)
    all_task_attempts = URLTaskAttemptSerializer(many=True)
    task_attempt = URLTaskAttemptSerializer(required=False)
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
    timepoints = TaskTimepointSerializer(
        many=True, allow_null=True, required=False)
    data_path = serializers.JSONField(required=True)

    # read-only
    status = serializers.CharField(read_only=True)

    @classmethod
    def apply_prefetch(cls, queryset):
        return queryset\
            .prefetch_related('timepoints')\
            .prefetch_related('inputs')\
            .prefetch_related('inputs__data_node')\
            .prefetch_related('outputs')\
            .prefetch_related('outputs__data_node')\
            .prefetch_related('task_attempt')\
            .prefetch_related('all_task_attempts')


class SummaryTaskSerializer(TaskSerializer):

    """SummaryTaskSerializer is an abbreviated alternative to
    TaskSerializer. Most fields are write_only.
    """

    # readable
    uuid = serializers.CharField(required=False, read_only=True)
    url = serializers.HyperlinkedIdentityField(
        view_name='task-detail',
        lookup_field='uuid')
    all_task_attempts = SummaryTaskAttemptSerializer(many=True, read_only=True)
    task_attempt = SummaryTaskAttemptSerializer(required=False)
    datetime_finished = serializers.DateTimeField(read_only=True, format='iso-8601')
    datetime_created = serializers.DateTimeField(read_only=True, format='iso-8601')
    status = serializers.CharField(read_only=True)

    # write-only
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
    timepoints = TaskTimepointSerializer(
        many=True, allow_null=True, required=False, write_only=True)
    data_path = serializers.JSONField(required=True, write_only=True)

    @classmethod
    def apply_prefetch(cls, queryset):
        return queryset\
            .prefetch_related('task_attempt')\
            .prefetch_related('all_task_attempts')


class URLTaskSerializer(TaskSerializer):

    class Meta:
        model = Task
        # Exclude read_only fields because we can't set both
        # read_only and write_only
        fields = TaskSerializer.Meta._writable_fields

    # readable
    uuid = serializers.CharField(required=False)
    url = serializers.HyperlinkedIdentityField(
        view_name='task-detail',
        lookup_field='uuid')

    # write-only
    all_task_attempts = TaskAttemptSerializer(many=True, write_only=True)
    task_attempt = TaskAttemptSerializer(required=False, write_only=True)
    datetime_finished = serializers.DateTimeField(format='iso-8601', write_only=True)
    datetime_created = serializers.DateTimeField(format='iso-8601', write_only=True)
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
    timepoints = TaskTimepointSerializer(
        many=True, allow_null=True, required=False, write_only=True)
    data_path = serializers.JSONField(required=True, write_only=True)

    @classmethod
    def apply_prefetch(cls, queryset):
        return queryset


class ExpandedTaskSerializer(TaskSerializer):

#    all_task_attempts = TaskAttemptSerializer(many=True)
    task_attempt = TaskAttemptSerializer()
