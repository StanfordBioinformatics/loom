from analysis.models.channels import *
from .base import MagicSerializer, POLYMORPHIC_TYPE_FIELD
from .data_objects import DataObjectSerializer

class InputOutputNodeSerializer(MagicSerializer):

    class Meta:
        model = InputOutputNode
        exclude = (POLYMORPHIC_TYPE_FIELD,)
        subclass_serializers = {
            'analysisstepruninput': 'analysis.serializers.workflow_runs.AbstractStepRunInputSerializer',
            'steprunoutput': 'analysis.serializers.workflow_runs.StepRunOutputSerializer',
            'workflowruninput': 'analysis.serializers.workflow_runs.WorkflowRunInputSerializer',
            'fixedworkflowruninput': 'analysis.serializers.workflow_runs.FixedWorkflowRunInputSerializer',
            'workflowrunoutput': 'analysis.serializers.workflow_runs.WorkflowRunOutputSerializer',
        }


class ChannelOutputSerializer(MagicSerializer):

    data_objects = DataObjectSerializer(many=True, required=False)
    receiver = InputOutputNodeSerializer(required=False)

    class Meta:
        model = ChannelOutput
        nested_x_to_many_serializers = {
            'data_objects': 'analysis.serializers.data_objects.DataObjectSerializer',
        }
        nested_x_to_one_serializers = {
            'sender': 'analysis.serializers.channels.InputOutputNodeSerializer',
        }


class ChannelSerializer(MagicSerializer):

    data_objects = DataObjectSerializer(many=True, required=False)
    outputs = ChannelOutputSerializer(many=True, required=False)
    sender = InputOutputNodeSerializer(required=False, allow_null=True)

    class Meta:
        model = Channel
        nested_x_to_many_serializers = {
            'data_objects': 'analysis.serializers.data_objects.DataObjectSerializer',
            'outputs': 'analysis.serializers.channels.ChannelOutputSerializer',
        }
        nested_x_to_one_serializers = {
            'sender': 'analysis.serializers.channels.InputOutputNodeSerializer',
        }
