from .base import NestedPolymorphicModelSerializer, POLYMORPHIC_TYPE_FIELD
from analysis.models.workflows import *


class AbstractWorkflowSerializer(NestedPolymorphicModelSerializer):

    class Meta:
        model = AbstractWorkflow
        exclude = (POLYMORPHIC_TYPE_FIELD,)
        subclass_serializers = {
            'workflow': 'analysis.serializers.workflows.WorkflowSerializer',
            'step': 'analysis.serializers.workflows.StepSerializer',
        }


class WorkflowSerializer(AbstractWorkflowSerializer):

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

    class Meta:
        model = Step
        exclude = (POLYMORPHIC_TYPE_FIELD,)
        nested_x_to_one_serializers = {
            'environment': 'analysis.serializers.workflows.RequestedEnvironmentSerializer',
            'resources': 'analysis.serializers.workflows.RequestedResourceSetSerializer',
        }
        nested_x_to_many_serializers = {
            'inputs': 'analysis.serializers.workflows.StepInputSerializer',
            'fixed_inputs': 'analysis.serializers.workflows.FixedStepInputSerializer',
            'outputs': 'analysis.serializers.workflows.StepOutputSerializer',
        }


class RequestedEnvironmentSerializer(NestedPolymorphicModelSerializer):

    class Meta:
        model = RequestedEnvironment
        exclude = (POLYMORPHIC_TYPE_FIELD,)
        subclass_serializers = {
            'requesteddockerenvironment': 'analysis.serializers.workflows.RequestedDockerEnvironment',
        }

class RequestedDockerEnvironmentSerializer(RequestedEnvironmentSerializer):

    class Meta:
        model = RequestedDockerEnvironment
        exclude = (POLYMORPHIC_TYPE_FIELD,)


class RequestedResourceSetSerializer(NestedPolymorphicModelSerializer):

    class Meta:
        model = RequestedResourceSet


class WorkflowInputSerializer(NestedPolymorphicModelSerializer):

    class Meta:
        model = WorkflowInput


class StepInputSerializer(NestedPolymorphicModelSerializer):

    class Meta:
        model = StepInput


class FixedWorkflowInputSerializer(NestedPolymorphicModelSerializer):

    class Meta:
        model = FixedWorkflowInput


class FixedStepInputSerializer(NestedPolymorphicModelSerializer):

    class Meta:
        model = FixedStepInput


class WorkflowOutputSerializer(NestedPolymorphicModelSerializer):

    class Meta:
        model = WorkflowOutput


class StepOutputSerializer(NestedPolymorphicModelSerializer):

    class Meta:
        model = StepOutput
