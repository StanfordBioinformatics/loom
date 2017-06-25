from rest_framework import serializers
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import prefetch_related_objects
from mptt.utils import get_cached_trees
from .base import CreateWithParentModelSerializer, RecursiveField, strip_empty_values, \
    ExpandableSerializerMixin
from api.models.runs import Run, RequestedInput, RunInput, RunOutput, RunTimepoint
from api.serializers.templates import TemplateSerializer, TemplateURLSerializer
from api.serializers.tasks import SummaryTaskSerializer, TaskSerializer, TaskURLSerializer, ExpandedTaskSerializer
from api.serializers.input_output_nodes import InputOutputNodeSerializer
from api import async


class RequestedInputSerializer(InputOutputNodeSerializer):

    # Type is inferred from template
    type = serializers.CharField(required=False)
    
    class Meta:
        model = RequestedInput
        fields = ('type', 'channel', 'data')


class RunInputSerializer(InputOutputNodeSerializer):

    class Meta:
        model = RunInput
        fields = ('type', 'channel', 'data', 'mode', 'group')

    mode = serializers.CharField()
    group = serializers.IntegerField()

    def to_representation(self, instance):
        return strip_empty_values(
            super(RunInputSerializer, self).to_representation(instance))


class RunOutputSerializer(InputOutputNodeSerializer):

    class Meta:
        model = RunOutput
        fields = ('type', 'channel', 'data', 'mode', 'source', 'parser')

    mode = serializers.CharField()
    source = serializers.JSONField(required=False)
    parser = serializers.JSONField(required=False)

    def to_representation(self, instance):
        return strip_empty_values(
            super(RunOutputSerializer, self).to_representation(instance))


class RunTimepointSerializer(CreateWithParentModelSerializer):

    class Meta:
        model = RunTimepoint
        fields = ('message', 'detail', 'timestamp', 'is_error')


class RunURLSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Run
        fields = ('url',
                  'uuid',
                  'name',
                  'datetime_created',
                  'datetime_finished',
                  'status')

    uuid = serializers.UUIDField(required=False)
    url = serializers.HyperlinkedIdentityField(
        view_name='run-detail',
        lookup_field='uuid')
    name = serializers.CharField(required=False)
    datetime_created = serializers.DateTimeField(read_only=True, format='iso-8601')
    datetime_finished = serializers.DateTimeField(read_only=True, format='iso-8601')
    status = serializers.CharField(read_only=True)

class RunSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Run
	fields = ('uuid',
                  'url',
                  'name',
                  'datetime_created',
                  'datetime_finished',
                  'template',
                  'postprocessing_status',
                  'status',
                  'status_is_finished',
                  'status_is_failed',
                  'status_is_killed',
                  'status_is_running',
                  'status_is_waiting',
                  'command',
                  'interpreter',
                  'requested_inputs',
                  'inputs',
                  'outputs',
                  'timepoints',
                  'steps',
                  'tasks',
        )

    uuid = serializers.UUIDField(required=False)
    url = serializers.HyperlinkedIdentityField(
        view_name='run-detail',
        lookup_field='uuid')
    name = serializers.CharField(required=False)
    datetime_created = serializers.DateTimeField(read_only=True, format='iso-8601')
    datetime_finished = serializers.DateTimeField(read_only=True, format='iso-8601')
    template = TemplateURLSerializer()
    postprocessing_status = serializers.CharField(required=False)
    status = serializers.CharField(read_only=True)
    status_is_finished = serializers.BooleanField(required=False)
    status_is_failed = serializers.BooleanField(required=False)
    status_is_killed = serializers.BooleanField(required=False)
    status_is_running = serializers.BooleanField(required=False)
    status_is_waiting = serializers.BooleanField(required=False)
    command = serializers.CharField(required=False)
    interpreter = serializers.CharField(required=False)
    requested_inputs = RequestedInputSerializer(many=True, required=False)
    inputs = RunInputSerializer(many=True,
                                required=False)
    outputs = RunOutputSerializer(many=True, required=False)
    timepoints = RunTimepointSerializer(many=True, required=False)
    steps = RunURLSerializer(many=True, read_only=True, required=False)
    tasks = TaskURLSerializer(many=True, required=False)

    def to_representation(self, instance):
        return strip_empty_values(
            super(RunSerializer, self).to_representation(instance))

    def create(self, validated_data):
        requested_inputs = self.initial_data.get('requested_inputs', None)
        validated_data.pop('requested_inputs', None)

        s = TemplateSerializer(data=validated_data.pop('template'))
        s.is_valid()
        template = s.save()

        run = Run.create_from_template(template)
        if requested_inputs is not None:
            for input_data in requested_inputs:
                # The requested_input usually won't have data type specified.
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
                s = RequestedInputSerializer(
                    data=input_data,
                    context={'parent_field': 'run',
                             'parent_instance': run
                         })
                s.is_valid(raise_exception=True)
                s.save()
        async.postprocess_run(run.uuid)
        return run
        
    @classmethod
    def _apply_prefetch(cls, queryset):
        for select_string in cls.get_select_related_list():
            queryset = queryset.select_related(select_string)
        for prefetch_string in cls.get_prefetch_related_list():
            queryset = queryset.prefetch_related(prefetch_string)
        return queryset

    @classmethod
    def get_prefetch_related_list(cls):
        return [
            'requested_inputs',
            'inputs',
            'outputs',
            'requested_inputs__data_tree',
            'inputs__data_tree',
            'inputs__data_tree__data_object',
            'inputs__data_tree__data_object__file_resource',
            'outputs__data_tree',
            'outputs__data_tree__data_object',
            'outputs__data_tree__data_object__file_resource',
            'timepoints',
            'steps',
            'tasks']

    @classmethod
    def get_select_related_list(cls):
        return ['template']


class SummaryRunSerializer(RunSerializer):

    """SummaryRunSerializer differs from RunSerializer in that
    1. Most fields are write_only
    2. It displays the full tree of nested runs (in summary form)
    """

    template = TemplateURLSerializer(write_only=True)
    postprocessing_status = serializers.CharField(write_only=True, required=False)
    status = None
    status_is_finished = serializers.BooleanField(write_only=True, required=False)
    status_is_failed = serializers.BooleanField(write_only=True, required=False)
    status_is_killed = serializers.BooleanField(write_only=True, required=False)
    status_is_running = serializers.BooleanField(write_only=True, required=False)
    status_is_waiting = serializers.BooleanField(write_only=True, required=False)
    command = serializers.CharField(write_only=True, required=False)
    interpreter = serializers.CharField(write_only=True)
    inputs = RunInputSerializer(many=True,
                                required=False,
                                allow_null=True,
                                write_only=True)
    outputs = RunOutputSerializer(many=True, write_only=True)
    timepoints = RunTimepointSerializer(
        many=True, allow_null=True, required=False, write_only=True)
    steps = RecursiveField(many=True, source='_cached_children', required=False)
    tasks = SummaryTaskSerializer(many=True)

    def to_representation(self, instance):
        instance = self._apply_prefetch_to_instance(instance)
        return super(SummaryRunSerializer, self).to_representation(
            instance)

    @classmethod
    def _apply_prefetch(cls, queryset):
        # no-op
        return queryset
              
    def _apply_prefetch_to_instance(self, instance):
        if not hasattr(instance, '_cached_children'):
            descendants = instance.get_descendants(include_self=True)\
                                  .prefetch_related('tasks')\
                                  .prefetch_related('tasks__all_task_attempts')\
                                  .prefetch_related('tasks__task_attempt')
            instance = get_cached_trees(descendants)[0]
        return instance


class ExpandedRunSerializer(RunSerializer):

    steps = RecursiveField(many=True, source='_cached_children', required=False)
    tasks = ExpandedTaskSerializer(many=True)

    def to_representation(self, instance):
        instance = self._apply_prefetch_to_instance(instance)
        return super(ExpandedRunSerializer, self).to_representation(
            instance)

    @classmethod
    def _apply_prefetch(cls, queryset):
        # no-op
        return queryset

    def _apply_prefetch_to_instance(self, instance):
        if not hasattr(instance, '_cached_children'):
            descendants = instance.get_descendants(include_self=True)
            descendants = RunSerializer._apply_prefetch(descendants)
            for select_string in self.get_select_related_list():
                descendants = descendants.select_related(select_string)
            for prefetch_string in self.get_prefetch_related_list():
                descendants = descendants.prefetch_related(prefetch_string)
            instance = get_cached_trees(descendants)[0]
        return instance

    @classmethod
    def get_prefetch_related_list(cls):
        prefetch_list = [
            'inputs',
            'outputs',
            'inputs__data_tree',
            'inputs__data_tree__data_object',
            'inputs__data_tree__data_object__file_resource',
            'outputs__data_tree',
            'outputs__data_tree__data_object',
            'outputs__data_tree__data_object__file_resource',
            'timepoints',
            'tasks']
        for suffix in ExpandedTaskSerializer.get_prefetch_related_list() + \
            ExpandedTaskSerializer.get_select_related_list():
            prefetch_list.append('tasks__'+suffix)
        return prefetch_list

    @classmethod
    def get_select_related_list(cls):
        return ['template']


class ExpandableRunSerializer(ExpandableSerializerMixin, RunSerializer):

    DEFAULT_SERIALIZER = RunSerializer
    COLLAPSE_SERIALIZER = RunSerializer
    EXPAND_SERIALIZER = ExpandedRunSerializer
    SUMMARY_SERIALIZER = SummaryRunSerializer
