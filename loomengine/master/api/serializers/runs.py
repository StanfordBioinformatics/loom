from rest_framework import serializers
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import prefetch_related_objects
from mptt.utils import get_cached_trees
from .base import CreateWithParentModelSerializer, RecursiveField, strip_empty_values
from api.models.runs import Run, RunInput, RunOutput, RunTimepoint
from api.serializers.templates import TemplateURLSerializer
from api.serializers.tasks import ExpandableTaskSerializer
from api.serializers.input_output_nodes import InputOutputNodeSerializer
from api.serializers.run_requests import RunRequestURLSerializer


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
        fields = ('type', 'channel', 'data', 'mode', 'source')

    mode = serializers.CharField()
    source = serializers.JSONField(required=False)

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
	fields = ('url', 'uuid')

    uuid = serializers.UUIDField(required=False)
    url = serializers.HyperlinkedIdentityField(
        view_name='run-detail',
        lookup_field='uuid')


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
                  'inputs',
                  'outputs',
                  'timepoints',
                  'run_request',
                  'steps',
                  'tasks',
        )

    uuid = serializers.UUIDField(required=False)
    url = serializers.HyperlinkedIdentityField(
        view_name='run-detail',
        lookup_field='uuid')
    name = serializers.CharField()
    datetime_created = serializers.DateTimeField(read_only=True, format='iso-8601')
    datetime_finished = serializers.DateTimeField(read_only=True, format='iso-8601')
    template = TemplateURLSerializer()
    postprocessing_status = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    status_is_finished = serializers.BooleanField(required=False)
    status_is_failed = serializers.BooleanField(required=False)
    status_is_killed = serializers.BooleanField(required=False)
    status_is_running = serializers.BooleanField(required=False)
    status_is_waiting = serializers.BooleanField(required=False)
    command = serializers.CharField(required=False, source='steprun.command')
    interpreter = serializers.CharField()
    inputs = RunInputSerializer(many=True,
                                required=False,
                                allow_null=True)
    outputs = RunOutputSerializer(many=True)
    timepoints = RunTimepointSerializer(
        many=True, allow_null=True, required=False)
    run_request = RunRequestURLSerializer(required=False)
    steps = RunURLSerializer(many=True, read_only=True, required=False)
    tasks = ExpandableTaskSerializer(many=True)
    
    def to_representation(self, instance):
        return strip_empty_values(
            super(RunSerializer, self).to_representation(instance))

    @classmethod
    def apply_prefetch(cls, queryset):
        return queryset.select_related('template')\
                       .prefetch_related('inputs')\
                       .prefetch_related('outputs')\
                       .prefetch_related(
                           'inputs__data_root')\
                       .prefetch_related(
                           'outputs__data_root')\
                       .prefetch_related('steps')\
                       .select_related(
                           'run_request')\
                       .prefetch_related('timepoints')\
                       .prefetch_related('tasks')


class NestedRunSerializer(RunSerializer):

    steps = RecursiveField(many=True, source='_cached_children', required=False)
    
    def to_representation(self, instance):
        self.Meta = RunSerializer.Meta
        if not hasattr(instance, '_cached_children'):
            descendants = instance.get_descendants(include_self=True)
            descendants = self.apply_prefetch(descendants)
            instance = get_cached_trees(descendants)[0]
        return super(NestedRunSerializer, self).to_representation(
            instance)


class ExpandableRunSerializer(RunSerializer):

    def to_representation(self, instance):
        if hasattr(instance, '_cached_repr'):
            return instance._cached_repr
        if self.context.get('expand'):
            repr = NestedRunSerializer(
                instance, context=self.context).to_representation(instance)
        else:
            repr = RunSerializer(
                instance, context=self.context).to_representation(instance)
        instance._cached_repr = repr
        return repr
