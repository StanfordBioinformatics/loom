from rest_framework import serializers
from django.core.exceptions import ObjectDoesNotExist

from .base import SuperclassModelSerializer, CreateWithParentModelSerializer, \
    NameAndUuidSerializer
from api.models.runs import Run, StepRun, \
    StepRunInput, StepRunOutput, WorkflowRunInput, \
    WorkflowRunOutput, WorkflowRun, RunTimepoint
from api.serializers.templates import TemplateNameAndUuidSerializer
from api.serializers.tasks import TaskUuidSerializer
from api.serializers.input_output_nodes import InputOutputNodeSerializer
from api.serializers.run_requests import RunRequestSerializer, \
    RunRequestUuidSerializer
from api import tasks


class RunSerializer(SuperclassModelSerializer):

    class Meta:
        model = Run
        fields = ()

    def _get_subclass_serializer_class(self, type):
        if type=='workflow':
            return WorkflowRunSerializer
        if type=='step':
            return StepRunSerializer
        else:
            # No valid type. Serializer with the base class
            return RunSerializer

    def _get_subclass_field(self, type):
        if type == 'step':
            return 'steprun'
        elif type == 'workflow':
            return 'workflowrun'
        else:
            return None

    def _get_type(self, data=None, instance=None):
        if instance:
            type = instance.type
        else:
            assert data, 'must provide either data or instance'
            type = data.get('type')
        if not type:
            return None
        return type


class RunNameAndUuidSerializer(NameAndUuidSerializer, RunSerializer):
    pass


class RunTimepointSerializer(CreateWithParentModelSerializer):

    class Meta:
        model = RunTimepoint
        fields = ('message', 'detail', 'timestamp', 'is_error')


class StepRunInputSerializer(InputOutputNodeSerializer):

    mode = serializers.CharField()
    group = serializers.IntegerField()

    class Meta:
        model = StepRunInput
        fields = ('type', 'channel', 'data', 'mode', 'group')


class StepRunOutputSerializer(InputOutputNodeSerializer):

    mode = serializers.CharField()
    source = serializers.JSONField(required=False)

    class Meta:
        model = StepRunOutput
        fields = ('type', 'channel', 'data', 'mode', 'source')


class StepRunSerializer(CreateWithParentModelSerializer):
    
    uuid = serializers.CharField(required=False)
    template = TemplateNameAndUuidSerializer()
    inputs = StepRunInputSerializer(many=True,
                                    required=False,
                                    allow_null=True)
    outputs = StepRunOutputSerializer(many=True)
    command = serializers.CharField()
    interpreter = serializers.CharField()
    interpreter_options = serializers.CharField()
    type = serializers.CharField()
    tasks = TaskUuidSerializer(many=True)
    run_request = RunRequestUuidSerializer(required=False)
    datetime_created = serializers.CharField(read_only=True)
    timepoints = RunTimepointSerializer(
        many=True, allow_null=True, required=False)
    status = serializers.CharField(read_only=True)
    
    class Meta:
        model = StepRun
        fields = ('uuid', 'template', 'inputs', 'outputs',
                  'command', 'interpreter', 'interpreter_options', 'tasks',
                  'run_request', 'postprocessing_status', 'type', 'datetime_created',
                  'status_is_finished', 'status_is_failed', 'status_is_killed',
                  'status_is_running', 'timepoints', 'status')


class WorkflowRunInputSerializer(InputOutputNodeSerializer):

    class Meta:
        model = WorkflowRunInput
        fields = ('type', 'channel', 'data',)


class WorkflowRunOutputSerializer(InputOutputNodeSerializer):

    class Meta:
        model = WorkflowRunOutput
        fields = ('type', 'channel', 'data',)


class WorkflowRunSerializer(CreateWithParentModelSerializer):

    uuid = serializers.CharField(required=False)
    type = serializers.CharField(required=False)
    template = TemplateNameAndUuidSerializer()
    steps = RunNameAndUuidSerializer(many=True)
    inputs = WorkflowRunInputSerializer(many=True,
                                        required=False,
                                        allow_null=True)
    outputs = WorkflowRunOutputSerializer(many=True)
    run_request = RunRequestUuidSerializer(required=False)
    datetime_created = serializers.CharField(read_only=True)
    timepoints = RunTimepointSerializer(
        many=True, allow_null=True, required=False)
    status = serializers.CharField(read_only=True)

    class Meta:
        model = WorkflowRun
        fields = ('uuid', 'template', 'steps', 'inputs', 'outputs',
                  'run_request', 'postprocessing_status', 'type', 'datetime_created',
                  'status_is_finished', 'status_is_failed', 'status_is_killed',
                  'status_is_running', 'timepoints', 'status')
