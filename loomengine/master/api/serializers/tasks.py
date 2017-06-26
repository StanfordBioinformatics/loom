from rest_framework import serializers

from api.exceptions import *
from .base import CreateWithParentModelSerializer, SuperclassModelSerializer, ExpandableSerializerMixin
from api.models.data_objects import DataObject
from api.models.tasks import Task, TaskInput, TaskOutput, \
    TaskAttempt, TaskAttemptOutput, TaskAttemptInput, \
    TaskAttemptLogFile, TaskAttemptTimepoint, TaskTimepoint
from api.serializers.data_objects import DataObjectSerializer
from api.serializers.input_output_nodes import InputOutputNodeSerializer


class TaskTimepointSerializer(CreateWithParentModelSerializer):

    class Meta:
        model = TaskTimepoint
        fields = ('message', 'detail', 'timestamp', 'is_error')


class TaskAttemptInputSerializer(InputOutputNodeSerializer):

    class Meta:
        model = TaskAttemptInput
        fields = ('type', 'channel', 'data', 'mode')

    mode = serializers.CharField()


class TaskAttemptOutputSerializer(InputOutputNodeSerializer):

    class Meta:
        model = TaskAttemptOutput
        fields = ('uuid', 'type', 'channel', 'data', 'mode', 'source', 'parser')

    source = serializers.JSONField(required=False)
    parser = serializers.JSONField(required=False)
    mode = serializers.CharField()


class TaskAttemptOutputUpdateSerializer(TaskAttemptOutputSerializer):

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
                                         'task_attempt_log_file': instance}
                                     )
            s.is_valid(raise_exception=True)
            s.save()
        return instance


class TaskAttemptTimepointSerializer(CreateWithParentModelSerializer):

    class Meta:
        model = TaskAttemptTimepoint
        fields = ('message', 'detail', 'timestamp', 'is_error')


class TaskAttemptURLSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = TaskAttempt
        fields = ('url', 'uuid', 'datetime_created', 'datetime_finished', 'status')

    uuid = serializers.UUIDField(required=False)
    url = serializers.HyperlinkedIdentityField(
        view_name='task-attempt-detail',
        lookup_field='uuid')
    datetime_created = serializers.DateTimeField(required=False, format='iso-8601')
    datetime_finished = serializers.DateTimeField(required=False, format='iso-8601')
    status = serializers.CharField(read_only=True)

        
class TaskAttemptSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = TaskAttempt
        fields = ('uuid',
                  'url',
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
                  'resources',
                  'timepoints',
                  'status')

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
    timepoints = TaskAttemptTimepointSerializer(
        many=True, allow_null=True, required=False)
    resources = serializers.JSONField(required=False)
    environment = serializers.JSONField(required=False)
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

        attributes = {}
        if status_is_finished is not None:
            attributes['status_is_finished'] = status_is_finished
        if status_is_failed is not None:
            attributes['status_is_failed'] = status_is_failed
        if status_is_running is not None:
            attributes['status_is_running'] = status_is_running
        instance = instance.setattrs_and_save_with_retries(attributes)
        return instance

    @classmethod
    def _apply_prefetch(cls, queryset):
        for prefetch_string in cls.get_prefetch_related_list():
            queryset = queryset.prefetch_related(prefetch_string)
        return queryset

    @classmethod
    def get_prefetch_related_list(cls):
        prefetch_list = ['inputs',
                'inputs__data_node__data_object',
                'outputs',
                'outputs__data_node__data_object',
                'log_files',
                'log_files__data_object',
                'log_files__data_object__file_resource',
                'timepoints']
        for suffix in DataObjectSerializer.get_select_related_list():
            prefetch_list.append('inputs__data_node__data_object__'+suffix)
            prefetch_list.append('outputs__data_node__data_object__'+suffix)
        return prefetch_list


class SummaryTaskAttemptSerializer(TaskAttemptSerializer):

    """SummaryTaskAttemptSerializer is an abbreviated alternative to
    TaskAttemptSerializer. Most fields are write_only.
    """

    command = serializers.CharField(write_only=True, required=False)
    interpreter = serializers.CharField(write_only=True, required=False)
    log_files = TaskAttemptLogFileSerializer(
        write_only=True, many=True, allow_null=True, required=False)
    inputs = TaskAttemptInputSerializer(
        write_only=True, many=True, allow_null=True, required=False)
    outputs = TaskAttemptOutputSerializer(
        write_only=True, many=True, allow_null=True, required=False)
    timepoints = TaskAttemptTimepointSerializer(
        write_only=True, many=True, allow_null=True, required=False)
    resources = serializers.JSONField(write_only=True, required=False)
    environment = serializers.JSONField(write_only=True, required=False)
    last_heartbeat = serializers.DateTimeField(write_only=True, format='iso-8601')
    status_is_finished = serializers.BooleanField(write_only=True, required=False)
    status_is_failed = serializers.BooleanField(write_only=True, required=False)
    status_is_killed = serializers.BooleanField(write_only=True, required=False)
    status_is_running = serializers.BooleanField(write_only=True, required=False)
    status_is_cleaned_up = serializers.BooleanField(write_only=True, required=False)


    def to_representation(self, instance):
        return super(SummaryTaskAttemptSerializer, self).to_representation(
	    instance)

    @classmethod
    def _apply_prefetch(cls, queryset):
        """Required by ExpandableSerializerMixin
        """
        # no-op
        return queryset

    
class ExpandableTaskAttemptSerializer(ExpandableSerializerMixin, TaskAttemptSerializer):

    DEFAULT_SERIALIZER = TaskAttemptSerializer
    COLLAPSE_SERIALIZER = TaskAttemptSerializer
    EXPAND_SERIALIZER = TaskAttemptSerializer
    SUMMARY_SERIALIZER = SummaryTaskAttemptSerializer


class TaskInputSerializer(InputOutputNodeSerializer):

    class Meta:
        model = TaskInput
        fields = ('data', 'type', 'channel', 'mode')

    mode = serializers.CharField(read_only=True)


class TaskOutputSerializer(InputOutputNodeSerializer):

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
