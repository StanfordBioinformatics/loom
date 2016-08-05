from rest_framework import serializers

from .base import SuperclassModelSerializer, CreateWithParentModelSerializer, NoUpdateModelSerializer
from analysis.models.run_requests import *
from analysis.models.workflows import AbstractWorkflow
from analysis.serializers.workflows import AbstractWorkflowIdSerializer
# from analysis.serializers.workflow_runs import AbstractWorkflowRunSerializer


class RunRequestInputSerializer(CreateWithParentModelSerializer):

    value = serializers.CharField() #converted from DataObject

    class Meta:
        model = RunRequestInput
        fields = ('channel', 'value',)

    def create(self, validated_data):
        # Convert 'value' into its corresponding data object
        value = validated_data.pop('value')
        validated_data['data_object'] = DataObject.get_by_value(
            value,
            self.context['data_type'])
        return super(RunRequestInputSerializer, self).create(validated_data)


class RunRequestOutputSerializer(CreateWithParentModelSerializer):

    class Meta:
        model = RunRequestOutput
        fields = ('channel')


class CancelRequestSerializer(CreateWithParentModelSerializer):

    class Meta:
        model = CancelRequest


class RestartRequestSerializer(CreateWithParentModelSerializer):

    class Meta:
        model = RestartRequest


class FailureNoticeSerializer(CreateWithParentModelSerializer):

    class Meta:
        model = FailureNotice


class RunRequestSerializer(serializers.ModelSerializer):

    id = serializers.UUIDField(format='hex', required=False)
    inputs = RunRequestInputSerializer(many=True, required=False)
    outputs = RunRequestInputSerializer(many=True, required=False)
    template = AbstractWorkflowIdSerializer()
    # run = AbstractWorkflowRunSerialzier(required=False)

    class Meta:
        model = RunRequest
        fields = ('id', 'template', 'inputs', 'outputs')

    def create(self, validated_data):
        inputs = self.initial_data.get('inputs', None)
        outputs = self.initial_data.get('outputs', None)
        validated_data.pop('inputs', None)
        validated_data.pop('outputs', None)

        # convert 'template' name@id into its corresponding object
        s = AbstractWorkflowIdSerializer(data=validated_data.pop('template'))
        s.is_valid()
        workflow = s.save()
        validated_data['template'] = workflow

        #run_serializer = AbstractWorkflowRunSerializer(
        #    data=self.initial_data.get('run', None))
        #run_serializer.is_valid()
        #validated_data['run'] = run_serializer.save()

        run_request = RunRequest.objects.create(**validated_data)

        if inputs is not None:
            for input_data in inputs:
                # We need to know the data type to find or create the data object from the
                # value given. Get that from the corresponding workflow input.
                data_type = workflow.get_input(input_data['channel']).type
                s = RunRequestInputSerializer(
                    data=input_data,
                    context={'parent_field': 'run_request',
                             'parent_instance': run_request,
                             'data_type': data_type,
                    })
                s.is_valid(raise_exception=True)
                s.save()

        if outputs is not None:
            for output_data in outputs:
                s = RunRequestOutputSerializer(
                    data=output_data,
                    context={'parent_field': 'run_request',
                             'parent_instance': run_request})
                s.is_valid(raise_exception=True)
                s.save()

        return run_request
