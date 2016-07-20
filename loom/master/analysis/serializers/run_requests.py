from .base import NestedPolymorphicModelSerializer, POLYMORPHIC_TYPE_FIELD
from analysis.models.run_requests import *
from analysis.serializers.workflow_runs import AbstractWorkflowRunSerializer
from analysis.serializers.channels import InputOutputNodeSerializer


class RunRequestSerializer(NestedPolymorphicModelSerializer):

    class Meta:
        model = RunRequest
        exclude = (POLYMORPHIC_TYPE_FIELD,)
        nested_x_to_one_serializers = {
            'template': 'analysis.serializers.workflows.AbstractWorkflowSerializer',
            'run': 'analysis.serializers.workflow_runs.AbstractWorkflowRunSerializer',
        }
        nested_x_to_many_serializers = {
            'inputs': 'analysis.serializers.run_requests.RunRequestInputSerializer',
            'outputs': 'analysis.serializers.run_requests.RunRequestOutputSerializer',
            'cancel_requests': 'analysis.serializers.run_requests.CancelRequestSerializer',
            'restart_requests': 'analysis.serializers.run_requests.RestartRequestSerializer',
            'failure_notices': 'analysis.serializers.run_requests.FailureNoticeSerializer',
        } 

class RunRequestInputSerializer(InputOutputNodeSerializer):
    
    class Meta:
        model = RunRequestInput
        exclude = (POLYMORPHIC_TYPE_FIELD,)

class RunRequestOutputSerializer(InputOutputNodeSerializer):

    class Meta:
        model = RunRequestOutput
        exclude = (POLYMORPHIC_TYPE_FIELD,)

class CancelRequestSerializer(NestedPolymorphicModelSerializer):

    class Meta:
        model = CancelRequest

class RestartRequestSerializer(NestedPolymorphicModelSerializer):

    class Meta:
        model = RestartRequest

class FailureNoticeSerializer(NestedPolymorphicModelSerializer):

    class Meta:
        model = FailureNotice
