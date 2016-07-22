from rest_framework import serializers

from .base import NestedPolymorphicModelSerializer, POLYMORPHIC_TYPE_FIELD
from analysis.models.workflows import *


class RequestedEnvironmentSerializer(NestedPolymorphicModelSerializer):

    class Meta:
        model = RequestedEnvironment
        exclude = (POLYMORPHIC_TYPE_FIELD, 'step', 'id')
        subclass_serializers = {
            'requesteddockerenvironment': 'analysis.serializers.workflows.RequestedDockerEnvironmentSerializer',
        }

class RequestedDockerEnvironmentSerializer(RequestedEnvironmentSerializer):

    class Meta:
        model = RequestedDockerEnvironment
        exclude = RequestedEnvironmentSerializer.Meta.exclude


class RequestedResourceSetSerializer(NestedPolymorphicModelSerializer):

    class Meta:
        model = RequestedResourceSet
        exclude = ('step', 'id')


class WorkflowInputSerializer(NestedPolymorphicModelSerializer):

    class Meta:
        model = WorkflowInput
        exclude = (POLYMORPHIC_TYPE_FIELD, 'workflow', 'id')


class StepInputSerializer(NestedPolymorphicModelSerializer):

    class Meta:
        model = StepInput
        exclude = (POLYMORPHIC_TYPE_FIELD, 'step', 'id')


class FixedWorkflowInputSerializer(NestedPolymorphicModelSerializer):

    class Meta:
        model = FixedWorkflowInput
        exclude = (POLYMORPHIC_TYPE_FIELD, 'workflow', 'id')


class FixedStepInputSerializer(NestedPolymorphicModelSerializer):

    class Meta:
        model = FixedStepInput
        exclude = (POLYMORPHIC_TYPE_FIELD, 'step', 'id')


class WorkflowOutputSerializer(NestedPolymorphicModelSerializer):

    class Meta:
        model = WorkflowOutput
        exclude = (POLYMORPHIC_TYPE_FIELD, 'workflow', 'id')


class StepOutputSerializer(NestedPolymorphicModelSerializer):

    class Meta:
        model = StepOutput
        exclude = (POLYMORPHIC_TYPE_FIELD, 'step', 'id')


class AbstractWorkflowSerializer(NestedPolymorphicModelSerializer):

    loom_id = serializers.UUIDField(format='hex', required=False)
    
    class Meta:
        model = AbstractWorkflow
        exclude = (POLYMORPHIC_TYPE_FIELD,)
        subclass_serializers = {
            'workflow': 'analysis.serializers.workflows.WorkflowSerializer',
            'step': 'analysis.serializers.workflows.StepSerializer',
        }


class WorkflowSerializer(AbstractWorkflowSerializer):

    inputs = WorkflowInputSerializer(many=True, required=False, allow_null=True)
    fixed_inputs = FixedWorkflowInputSerializer(many=True, required=False, allow_null=True)
    outputs = WorkflowOutputSerializer(many=True)
    steps = AbstractWorkflowSerializer(many=True)
    
    class Meta:
        model = Workflow
        exclude = (POLYMORPHIC_TYPE_FIELD,)
        nested_x_to_many_serializers = {
            'inputs': 'analysis.serializers.workflows.WorkflowInputSerializer',
            'fixed_inputs': 'analysis.serializers.workflows.FixedWorkflowInputSerializer',
            'outputs': 'analysis.serializers.workflows.WorkflowOutputSerializer',
            'steps': 'analysis.serializers.workflows.AbstractWorkflowSerializer',
        }


class StepSerializer(AbstractWorkflowSerializer):

    environment = RequestedEnvironmentSerializer()
    resources = RequestedResourceSetSerializer()
    inputs = StepInputSerializer(many=True, required=False)
    fixed_inputs = FixedStepInputSerializer(many=True, required=False)
    outputs = StepOutputSerializer(many=True)
    
    class Meta:
        model = Step
        exclude = (POLYMORPHIC_TYPE_FIELD,)
        nested_reverse_x_to_one_serializers = {
            'environment': 'analysis.serializers.workflows.RequestedEnvironmentSerializer',
            'resources': 'analysis.serializers.workflows.RequestedResourceSetSerializer',
        }
        nested_x_to_many_serializers = {
            'inputs': 'analysis.serializers.workflows.StepInputSerializer',
            'fixed_inputs': 'analysis.serializers.workflows.FixedStepInputSerializer',
            'outputs': 'analysis.serializers.workflows.StepOutputSerializer',
        }
