from rest_framework import serializers

from .base import CreateWithParentModelSerializer, ExpandableSerializerMixin
from api.models.data_objects import DataObject
from api.models.tasks import Task, TaskInput, TaskOutput, \
    TaskTimepoint
from api.serializers.data_objects import DataObjectSerializer
from api.serializers.data_channels import DataChannelSerializer
from api.serializers.task_attempts import TaskAttemptSerializer, \
    TaskAttemptURLSerializer, SummaryTaskAttemptSerializer


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


class TaskURLSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Task
        fields = ('url', 'uuid', 'datetime_created', 'datetime_finished', 'status')

    uuid = serializers.UUIDField(required=False)
    url = serializers.HyperlinkedIdentityField(
        view_name='task-detail',
        lookup_field='uuid')
    datetime_created = serializers.DateTimeField(required=False, format='iso-8601')
    datetime_finished = serializers.DateTimeField(required=False, format='iso-8601')
    status = serializers.CharField(read_only=True)


class TaskSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Task
        fields = (
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
            'attempt_number',
            'timepoints',
            'data_path',
            'status',
        )

    uuid = serializers.CharField(required=False, read_only=True)
    url = serializers.HyperlinkedIdentityField(
        view_name='task-detail',
        lookup_field='uuid')
    resources = serializers.JSONField(required=False)
    environment = serializers.JSONField(required=False)
    inputs = TaskInputSerializer(many=True, read_only=True)
    outputs = TaskOutputSerializer(many=True, read_only=True)
    all_task_attempts = TaskAttemptURLSerializer(many=True, read_only=True)
    task_attempt = TaskAttemptURLSerializer(required=False)
    raw_command = serializers.CharField(required=False)
    command = serializers.CharField(required=False)
    interpreter = serializers.CharField(required=False)
    datetime_finished = serializers.DateTimeField(read_only=True, format='iso-8601')
    datetime_created = serializers.DateTimeField(read_only=True, format='iso-8601')
    status_is_finished = serializers.BooleanField(required=False)
    status_is_failed = serializers.BooleanField(required=False)
    status_is_killed = serializers.BooleanField(required=False)
    status_is_running = serializers.BooleanField(required=False)
    status_is_waiting = serializers.BooleanField(required=False)
    attempt_number = serializers.IntegerField(read_only=True)
    timepoints = TaskTimepointSerializer(
        many=True, allow_null=True, required=False)
    data_path = serializers.JSONField(required=True)
    status = serializers.CharField(read_only=True)

    @classmethod
    def _apply_prefetch(cls, queryset):
        for select_string in cls.get_select_related_list():
            queryset = queryset.select_related(select_string)
        for prefetch_string in cls.get_prefetch_related_list():
            queryset = queryset.prefetch_related(prefetch_string)
        return queryset

    @classmethod
    def get_select_related_list(cls):
        return ['task_attempt']

    @classmethod
    def get_prefetch_related_list(cls):
        prefetch_list = [
            'inputs',
            'inputs__data_node__data_object',
            'outputs',
            'outputs__data_node__data_object',
            'all_task_attempts',
            'timepoints']
        for suffix in DataObjectSerializer.get_select_related_list():
            prefetch_list.append('inputs__data_node__data_object__'+suffix)
            prefetch_list.append('outputs__data_node__data_object__'+suffix)
        return prefetch_list


class SummaryTaskSerializer(TaskSerializer):

    """SummaryTaskSerializer is an abbreviated alternative to
    TaskSerializer. Most fields are write_only.
    """

    resources = serializers.JSONField(write_only=True, required=False)
    environment = serializers.JSONField(write_only=True, required=False)
    inputs = TaskInputSerializer(write_only=True, many=True)
    outputs = TaskOutputSerializer(write_only=True, many=True)
    all_task_attempts = SummaryTaskAttemptSerializer(many=True)
    task_attempt = SummaryTaskAttemptSerializer(required=False)
    raw_command = serializers.CharField(write_only=True, required=False)
    command = serializers.CharField(write_only=True, required=False)
    interpreter = serializers.CharField(write_only=True, required=False)
    status_is_finished = serializers.BooleanField(write_only=True, required=False)
    status_is_failed = serializers.BooleanField(write_only=True, required=False)
    status_is_killed = serializers.BooleanField(write_only=True, required=False)
    status_is_running = serializers.BooleanField(write_only=True, required=False)
    status_is_waiting = serializers.BooleanField(write_only=True, required=False)
    timepoints = TaskTimepointSerializer(
        write_only=True, many=True, allow_null=True, required=False)
    data_path = serializers.JSONField(write_only=True, required=True)

    @classmethod
    def _apply_prefetch(cls, queryset):
        for select_string in cls.get_select_related_list():
            queryset = queryset.select_related(select_string)
        for prefetch_string in cls.get_prefetch_related_list():
            queryset = queryset.prefetch_related(prefetch_string)
        return queryset

    @classmethod
    def get_select_related_list(cls):
        return ['task_attempt']

    @classmethod
    def get_prefetch_related_list(cls):
        return ['all_task_attempts']


class ExpandedTaskSerializer(TaskSerializer):

    all_task_attempts = TaskAttemptSerializer(many=True, read_only=True)
    task_attempt = TaskAttemptSerializer(read_only=True)
    
    @classmethod
    def _apply_prefetch(cls, queryset):
        for select_string in cls.get_select_related_list():
            queryset = queryset.select_related(select_string)
        for prefetch_string in cls.get_prefetch_related_list():
            queryset = queryset.prefetch_related(prefetch_string)
        return queryset

    @classmethod
    def get_select_related_list(cls):
        return ['task_attempt']

    @classmethod
    def get_prefetch_related_list(cls):
        prefetch_list = [
            'inputs',
            'inputs__data_node__data_object',
            'outputs',
            'outputs__data_node__data_object',
            'all_task_attempts',
            'timepoints']
        for suffix in DataObjectSerializer.get_select_related_list():
            prefetch_list.append('inputs__data_node__data_object__'+suffix)
            prefetch_list.append('outputs__data_node__data_object__'+suffix)
        for suffix in TaskAttemptSerializer.get_prefetch_related_list():
            prefetch_list.append('all_task_attempts__'+suffix)
            prefetch_list.append('task_attempt__'+suffix)
        return prefetch_list


class ExpandableTaskSerializer(ExpandableSerializerMixin, TaskSerializer):

    DEFAULT_SERIALIZER = TaskSerializer
    COLLAPSE_SERIALIZER = TaskSerializer
    EXPAND_SERIALIZER = ExpandedTaskSerializer
    SUMMARY_SERIALIZER = SummaryTaskSerializer
