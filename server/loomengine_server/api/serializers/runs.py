from rest_framework import serializers
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import prefetch_related_objects
from mptt.utils import get_cached_trees
from . import CreateWithParentModelSerializer, RecursiveField, \
    strip_empty_values, ProxyWriteSerializer
from api.models.runs import Run, UserInput, RunInput, RunOutput, RunEvent
from api.serializers.templates import TemplateSerializer, URLTemplateSerializer
from api.serializers.tasks import SummaryTaskSerializer, TaskSerializer, \
    URLTaskSerializer, ExpandedTaskSerializer
from api.serializers.data_channels import DataChannelSerializer
from api import async


class UserInputSerializer(DataChannelSerializer):

    # type not required because it is inferred from template
    type = serializers.CharField(required=False)

    class Meta:
        model = UserInput
        fields = ('type', 'channel', 'data')

        
class RunInputSerializer(DataChannelSerializer):

    class Meta:
        model = RunInput
        fields = ('type', 'channel', 'as_channel', 'data', 'mode', 'group')

    mode = serializers.CharField()
    group = serializers.IntegerField()
    as_channel = serializers.CharField(required=False)

    def to_representation(self, instance):
        return strip_empty_values(
            super(RunInputSerializer, self).to_representation(instance))


class RunOutputSerializer(DataChannelSerializer):

    class Meta:
        model = RunOutput
        fields = ('type', 'channel', 'as_channel', 'data', 'mode', 'source', 'parser')

    mode = serializers.CharField()
    source = serializers.JSONField(required=False)
    parser = serializers.JSONField(required=False)
    as_channel = serializers.CharField(required=False)

    def to_representation(self, instance):
        return strip_empty_values(
            super(RunOutputSerializer, self).to_representation(instance))


class RunEventSerializer(CreateWithParentModelSerializer):

    class Meta:
        model = RunEvent
        fields = ('event', 'detail', 'timestamp', 'is_error')


_run_serializer_fields = [
    'uuid',
    'url',
    'name',
    'status',
    'datetime_created',
    'datetime_finished',
    'template',
    'postprocessing_status',
    'status_is_finished',
    'status_is_failed',
    'status_is_killed',
    'status_is_running',
    'status_is_waiting',
    'is_leaf',
    'command',
    'interpreter',
    'environment',
    'resources',
    'notification_addresses',
    'notification_context',
    'user_inputs',
    'inputs',
    'outputs',
    'events',
    'steps',
    'tasks',]


class URLRunSerializer(ProxyWriteSerializer):

    class Meta:
        model = Run
        fields = _run_serializer_fields

    # readable fields
    uuid = serializers.UUIDField(required=False)
    url = serializers.HyperlinkedIdentityField(
        view_name='run-detail',
        lookup_field='uuid')
    name = serializers.CharField(required=False)
    datetime_created = serializers.DateTimeField(
        required=False, format='iso-8601')
    datetime_finished = serializers.DateTimeField(
        required=False, format='iso-8601')
    status = serializers.CharField(read_only=True)
    is_leaf = serializers.BooleanField(required=False)

    # write-only fields
    template = TemplateSerializer(required=False, write_only=True)
    postprocessing_status = serializers.CharField(required=False, write_only=True)
    status_is_finished = serializers.BooleanField(required=False, write_only=True)
    status_is_failed = serializers.BooleanField(required=False, write_only=True)
    status_is_killed = serializers.BooleanField(required=False, write_only=True)
    status_is_running = serializers.BooleanField(required=False, write_only=True)
    status_is_waiting = serializers.BooleanField(required=False, write_only=True)
    command = serializers.CharField(required=False, write_only=True)
    interpreter = serializers.CharField(required=False, write_only=True)
    environment = serializers.JSONField(required=False, write_only=True)
    resources = serializers.JSONField(required=False, write_only=True)
    notification_addresses = serializers.JSONField(
        required=False, write_only=True, allow_null=True)
    notification_context = serializers.JSONField(
        required=False, write_only=True, allow_null=True)
    user_inputs = UserInputSerializer(
        many=True, required=False, write_only=True)
    inputs = RunInputSerializer(many=True, required=False, write_only=True)
    outputs = RunOutputSerializer(many=True, required=False, write_only=True)
    events = RunEventSerializer(many=True, required=False, write_only=True)
    steps = RecursiveField(many=True, required=False, write_only=True)
    tasks = URLTaskSerializer(many=True, required=False, write_only=True)

    @classmethod
    def apply_prefetch(cls, queryset):
        return queryset


class RunSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Run
	fields = _run_serializer_fields

    uuid = serializers.UUIDField(required=False)
    url = serializers.HyperlinkedIdentityField(
        view_name='run-detail',
        lookup_field='uuid')
    name = serializers.CharField(required=False)
    datetime_created = serializers.DateTimeField(required=False, format='iso-8601')
    datetime_finished = serializers.DateTimeField(required=False, format='iso-8601')
    template = URLTemplateSerializer(required=False)
    postprocessing_status = serializers.CharField(required=False)
    status = serializers.CharField(read_only=True)
    status_is_finished = serializers.BooleanField(required=False)
    status_is_failed = serializers.BooleanField(required=False)
    status_is_killed = serializers.BooleanField(required=False)
    status_is_running = serializers.BooleanField(required=False)
    status_is_waiting = serializers.BooleanField(required=False)
    is_leaf = serializers.BooleanField(required=False)
    command = serializers.CharField(required=False)
    interpreter = serializers.CharField(required=False)
    environment = serializers.JSONField(required=False)
    resources = serializers.JSONField(required=False)
    notification_addresses = serializers.JSONField(required=False, allow_null=True)
    notification_context = serializers.JSONField(required=False, allow_null=True)
    user_inputs = UserInputSerializer(many=True, required=False)
    inputs = RunInputSerializer(many=True, required=False)
    outputs = RunOutputSerializer(many=True, required=False)
    events = RunEventSerializer(many=True, required=False)
    steps = URLRunSerializer(many=True, required=False)
    tasks = URLTaskSerializer(many=True, required=False)

    def to_representation(self, instance):
        return strip_empty_values(
            super(RunSerializer, self).to_representation(instance))

    def create(self, validated_data):
        user_inputs = self.initial_data.get('user_inputs', None)
        validated_data.pop('user_inputs', None)
        validated_data.pop('template')
        s = TemplateSerializer(data=self.initial_data.get('template'))
        s.is_valid()
        template = s.save()

        run = Run.create_from_template(
            template,
            name=validated_data.get('name'),
            notification_addresses=validated_data.get('notification_addresses'),
            notification_context=Run.get_notification_context(
                self.context.get('request')))
        if user_inputs is not None:
            for input_data in user_inputs:
                # The user_input usually won't have data type specified.
                # We need to know the data type to find or create the
                # data object from the value given. We get the type from the
                # corresponding template input.
                if not input_data.get('channel'):
                    raise serializers.ValidationError(
                        'Missing required "channel" field on input: "%s"' % input_data)
                try:
                    input = template.get_input(input_data.get('channel'))
                except ObjectDoesNotExist:
                    raise serializers.ValidationError(
                        'Input channel "%s" does not match any channel '\
                        'on the template.' % input_data.get('channel'))
                if input_data.get('type') and input_data.get('type') != input.type:
                    raise serializers.ValidationError(
                        'Type mismatch: Data with type "%s" does not match '
                        'input channel "%s" with type "%s".' % (
                            input_data.get('type'), input_data.get('channel'), type))
                input_data.update({'type': input.type})
                s = UserInputSerializer(
                    data=input_data,
                    context={'parent_field': 'run',
                             'parent_instance': run
                         })
                s.is_valid(raise_exception=True)
                s.save()
        run.initialize_inputs()
        run.initialize_outputs()
        run.initialize()
        return run

    @classmethod
    def apply_prefetch(cls, queryset):
        return queryset\
            .select_related('template')\
            .prefetch_related('events')\
            .prefetch_related('inputs')\
            .prefetch_related('inputs__data_node')\
            .prefetch_related('outputs')\
            .prefetch_related('outputs__data_node')\
            .prefetch_related('user_inputs')\
            .prefetch_related('user_inputs__data_node')\
            .prefetch_related('steps')\
            .prefetch_related('tasks')


class SummaryRunSerializer(RunSerializer):

    """SummaryRunSerializer differs from RunSerializer in that
    1. Most fields are write_only
    2. It displays the full tree of nested runs (in summary form)
    """

    # readable fields
    uuid = serializers.UUIDField(required=False)
    url = serializers.HyperlinkedIdentityField(
        view_name='run-detail',
        lookup_field='uuid')
    name = serializers.CharField(required=False)
    datetime_created = serializers.DateTimeField(
        required=False, format='iso-8601')
    datetime_finished = serializers.DateTimeField(
        required=False, format='iso-8601')
    status = serializers.CharField(read_only=True)
    steps = RecursiveField(many=True, required=False,
                           source='_cached_children')
    tasks = SummaryTaskSerializer(many=True, required=False)
    is_leaf = serializers.BooleanField(required=False)

    # write-only fields
    template = TemplateSerializer(required=False, write_only=True)
    postprocessing_status = serializers.CharField(required=False, write_only=True)
    status_is_finished = serializers.BooleanField(required=False, write_only=True)
    status_is_failed = serializers.BooleanField(required=False, write_only=True)
    status_is_killed = serializers.BooleanField(required=False, write_only=True)
    status_is_running = serializers.BooleanField(required=False, write_only=True)
    status_is_waiting = serializers.BooleanField(required=False, write_only=True)
    command = serializers.CharField(required=False, write_only=True)
    interpreter = serializers.CharField(required=False, write_only=True)
    environment = serializers.JSONField(required=False, write_only=True)
    resources = serializers.JSONField(required=False, write_only=True)
    notification_addresses = serializers.JSONField(
        required=False, write_only=True, allow_null=True)
    notification_context = serializers.JSONField(
        required=False, write_only=True, allow_null=True)
    user_inputs = UserInputSerializer(
        required=False, many=True, write_only=True)
    inputs = RunInputSerializer(many=True, required=False, write_only=True)
    outputs = RunOutputSerializer(many=True, required=False, write_only=True)
    events = RunEventSerializer(many=True, required=False, write_only=True)

    def to_representation(self, instance):
        instance = self._apply_prefetch_to_instance(instance)
        return super(SummaryRunSerializer, self).to_representation(instance)

    @classmethod
    def apply_prefetch(cls, queryset):
        return queryset

    def _apply_prefetch_to_instance(self, instance):
        if not hasattr(instance, '_cached_children'):
            descendants = instance.get_descendants(include_self=True)
            descendants = self._prefetch_on_tree_nodes(descendants)
            instance = get_cached_trees(descendants)[0]
        return instance

    @classmethod
    def _prefetch_on_tree_nodes(cls, queryset):
        return queryset\
            .prefetch_related('tasks')\
            .prefetch_related('tasks__task_attempt')\
            .prefetch_related('tasks__all_task_attempts')


class ExpandedRunSerializer(RunSerializer):

    steps = RecursiveField(many=True, source='_cached_children', required=False)
    tasks = ExpandedTaskSerializer(required=False, many=True)

    def to_representation(self, instance):
        instance = self._apply_prefetch_to_instance(instance)
        return  super(
            ExpandedRunSerializer, self).to_representation(
                instance)

    @classmethod
    def apply_prefetch(cls, queryset):
        return queryset
    
    def _apply_prefetch_to_instance(self, instance):
        if not hasattr(instance, '_cached_children'):
            descendants = instance.get_descendants(include_self=True)
            descendants = self._prefetch_on_tree_nodes(descendants)
            instance = get_cached_trees(descendants)[0]
        return instance

    @classmethod
    def _prefetch_on_tree_nodes(cls, queryset):
        return queryset\
            .select_related('template')\
            .prefetch_related('events')\
            .prefetch_related('inputs')\
            .prefetch_related('inputs__data_node')\
            .prefetch_related('outputs')\
            .prefetch_related('outputs__data_node')\
            .prefetch_related('user_inputs')\
            .prefetch_related('user_inputs__data_node')\
            .prefetch_related('tasks')\
            .prefetch_related('tasks__events')\
            .prefetch_related('tasks__inputs')\
            .prefetch_related('tasks__inputs__data_node')\
            .prefetch_related('tasks__outputs')\
            .prefetch_related('tasks__outputs__data_node')\
            .prefetch_related('tasks__task_attempt')\
            .prefetch_related('tasks__task_attempt__events')\
            .prefetch_related('tasks__task_attempt__inputs')\
            .prefetch_related('tasks__task_attempt__inputs__data_node')\
            .prefetch_related('tasks__task_attempt__outputs')\
            .prefetch_related('tasks__task_attempt__outputs__data_node')\
            .prefetch_related(
                'tasks__task_attempt__log_files')\
            .prefetch_related(
                'tasks__task_attempt__log_files__data_object')\
            .prefetch_related(
                'tasks__task_attempt__log_files__data_object__file_resource')\
            .prefetch_related('tasks__all_task_attempts')
