import json
from rest_framework import serializers

from .base import SuperclassModelSerializer, CreateWithParentModelSerializer
from api.models.data_objects import DataObject
from api.models.run_requests import RunRequest, RunRequestInput
from api.models.signals import post_save_children
from api.models.workflows import AbstractWorkflow
from api.serializers.workflows import AbstractWorkflowIdSerializer
from api.serializers.workflow_runs import AbstractWorkflowRunSerializer


class RunRequestInputSerializer(CreateWithParentModelSerializer):

    data = serializers.CharField() #converted from tree of DataNodes at input.data_root

    class Meta:
        model = RunRequestInput
        fields = ('channel', 'data',)

    def create(self, validated_data):
        # Convert 'data' into its corresponding data object
        data_value = validated_data.pop('data')
        run_request_input = super(RunRequestInputSerializer, self).create(validated_data)
        run_request_input.add_data_objects(data_value, self.context['data_type'])
        return run_request_input

class RunRequestSerializer(serializers.ModelSerializer):

    id = serializers.UUIDField(format='hex', required=False)
    name = serializers.CharField(required=False, read_only=True)
    inputs = RunRequestInputSerializer(many=True, required=False)
    template = AbstractWorkflowIdSerializer()
    run = AbstractWorkflowRunSerializer(required=False)

    class Meta:
        model = RunRequest
        fields = ('id',
                  'name',
                  'template',
                  'inputs',
                  'datetime_created',
                  'run',
                  'status')

    def create(self, validated_data):
        inputs = self.initial_data.get('inputs', None)
        validated_data.pop('inputs', None)

        # Look up workflow or step 'template' using identifier string
        s = AbstractWorkflowIdSerializer(data=validated_data.pop('template'))
        s.is_valid()
        workflow = s.save()
        validated_data['template'] = workflow

        run_request = RunRequest.objects.create(**validated_data)

        
        if inputs is not None:
            for input_data in inputs:
                # We need to know the data type to find or create the
                # data object from the value given. Get that from the
                # corresponding workflow input.
                data_type = workflow.get_input(input_data['channel']).type
                s = RunRequestInputSerializer(
                    data=input_data,
                    context={'parent_field': 'run_request',
                             'parent_instance': run_request,
                             'data_type': data_type,
                    })
                s.is_valid(raise_exception=True)
                s.save()

        run_request.initialize()
        run_request.create_ready_tasks()

        return run_request
