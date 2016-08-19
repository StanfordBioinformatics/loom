from rest_framework import serializers

from .base import SuperclassModelSerializer, CreateWithParentModelSerializer, NoUpdateModelSerializer
from analysis.models.workflow_runs import *
from analysis.serializers.workflows import AbstractWorkflowIdSerializer, RequestedEnvironmentSerializer, RequestedResourceSetSerializer

class StepRunInputSerializer(CreateWithParentModelSerializer):

    value = serializers.CharField()
    
    class Meta:
        model = StepRunInput
        fields = ('type', 'channel', 'value',)


class FixedStepRunInputSerializer(CreateWithParentModelSerializer):

    value = serializers.CharField()
        
    class Meta:
        model = FixedStepRunInput
        fields = ('type', 'channel', 'value',)


class StepRunOutputSerializer(CreateWithParentModelSerializer):

    value = serializers.CharField()
        
    class Meta:
        model = StepRunOutput
        fields = ('type', 'channel', 'value',)


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
    resources = RequestedResourceSetSerializer()
    environment = RequestedEnvironmentSerializer()
    name = serializers.CharField()
    
    class Meta:
        model = StepRun
        fields = ('id', 'template', 'inputs', 'fixed_inputs', 'outputs', 'command', 'environment', 'resources', 'name',)


class WorkflowRunInputSerializer(CreateWithParentModelSerializer):

    value = serializers.CharField()
        
    class Meta:
        model = WorkflowRunInput
        fields = ('type', 'channel', 'value',)

class FixedWorkflowRunInputSerializer(CreateWithParentModelSerializer):

    value = serializers.CharField()
        
    class Meta:
        model = FixedWorkflowRunInput
        fields = ('type', 'channel', 'value',)


class WorkflowRunOutputSerializer(CreateWithParentModelSerializer):

    value = serializers.CharField()
    
    class Meta:
        model = WorkflowRunOutput
        fields = ('type', 'channel', 'value',)


class WorkflowRunSerializer(CreateWithParentModelSerializer):

    id = serializers.UUIDField(format='hex', required=False)
    template = AbstractWorkflowIdSerializer()
    step_runs = StepRunSerializer(many=True)
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
        fields = ('id', 'template', 'step_runs', 'inputs', 'fixed_inputs', 'outputs', 'name',)


class AbstractWorkflowRunSerializer(SuperclassModelSerializer):

    subclass_serializers = {
        'workflowrun': WorkflowRunSerializer,
        'steprun': StepRunSerializer
    }

    class Meta:
        model = AbstractWorkflowRun
