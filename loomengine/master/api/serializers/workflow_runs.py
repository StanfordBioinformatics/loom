from rest_framework import serializers

from .base import SuperclassModelSerializer, CreateWithParentModelSerializer
from api.models.workflow_runs import AbstractWorkflowRun, StepRun, \
    StepRunInput, FixedStepRunInput, StepRunOutput, WorkflowRunInput, \
    FixedWorkflowRunInput, WorkflowRunOutput, WorkflowRun
from api.serializers.workflows import AbstractWorkflowIdSerializer, \
    RequestedEnvironmentSerializer, RequestedResourceSetSerializer
from api.serializers.tasks import TaskIdSerializer, TaskAttemptErrorSerializer


class AbstractWorkflowRunSerializer(SuperclassModelSerializer):

    subclass_serializers = {
        'workflowrun': 'api.serializers.WorkflowRunSerializer',
        'steprun': 'api.serializers.StepRunSerializer'
    }

    class Meta:
        model = AbstractWorkflowRun
        fields = '__all__'


class StepRunInputSerializer(CreateWithParentModelSerializer):

    data = serializers.CharField()
    mode = serializers.CharField()
    group = serializers.IntegerField()

    class Meta:
        model = StepRunInput
        fields = ('type', 'channel', 'data', 'mode', 'group')


class FixedStepRunInputSerializer(CreateWithParentModelSerializer):

    data = serializers.CharField()
    mode = serializers.CharField()
    group = serializers.IntegerField()
        
    class Meta:
        model = FixedStepRunInput
        fields = ('type', 'channel', 'data', 'mode', 'group')

        
class StepRunOutputSerializer(CreateWithParentModelSerializer):

    data = serializers.CharField()
    mode = serializers.CharField()

    class Meta:
        model = StepRunOutput
        fields = ('type', 'channel', 'data', 'mode')


class StepRunSerializer(CreateWithParentModelSerializer):

    id = serializers.UUIDField(format='hex', required=False)
    template = AbstractWorkflowIdSerializer()
    inputs = StepRunInputSerializer(many=True,
                                    required=False,
                                    allow_null=True)
    fixed_inputs = FixedStepRunInputSerializer(many=True,
                                               required=False,
                                               allow_null=True)
    outputs = StepRunOutputSerializer(many=True)
    command = serializers.CharField()
    interpreter = serializers.CharField()
    resources = RequestedResourceSetSerializer()
    environment = RequestedEnvironmentSerializer()
    name = serializers.CharField()
    tasks = TaskIdSerializer(many=True)
    errors = TaskAttemptErrorSerializer(many=True, read_only=True)
    
    class Meta:
        model = StepRun
        fields = ('id', 'template', 'inputs', 'fixed_inputs', 'outputs',
                  'command', 'interpreter', 'environment', 'resources', 'name',
                  'tasks', 'status', 'errors')


class WorkflowRunInputSerializer(CreateWithParentModelSerializer):

    data = serializers.CharField()
        
    class Meta:
        model = WorkflowRunInput
        fields = ('type', 'channel', 'data',)


class FixedWorkflowRunInputSerializer(CreateWithParentModelSerializer):

    data = serializers.CharField()
        
    class Meta:
        model = FixedWorkflowRunInput
        fields = ('type', 'channel', 'data',)


class WorkflowRunOutputSerializer(CreateWithParentModelSerializer):

    data = serializers.CharField()
    
    class Meta:
        model = WorkflowRunOutput
        fields = ('type', 'channel', 'data',)


class WorkflowRunSerializer(CreateWithParentModelSerializer):

    id = serializers.UUIDField(format='hex', required=False)
    template = AbstractWorkflowIdSerializer()
    step_runs = AbstractWorkflowRunSerializer(many=True)
    inputs = WorkflowRunInputSerializer(many=True,
                                        required=False,
                                        allow_null=True)
    fixed_inputs = FixedWorkflowRunInputSerializer(many=True,
                                                   required=False,
                                                   allow_null=True)
    outputs = WorkflowRunOutputSerializer(many=True)
    name = serializers.CharField()
    
    class Meta:
        model = WorkflowRun
        fields = ('id', 'template', 'step_runs', 'inputs', 'fixed_inputs',
                  'outputs', 'name', 'status')
