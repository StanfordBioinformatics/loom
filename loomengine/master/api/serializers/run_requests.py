import json
from rest_framework import serializers

from .base import SuperclassModelSerializer, CreateWithParentModelSerializer
from api.models.data_objects import DataObject
from api.models.run_requests import RunRequest, RunRequestInput
from api.models.signals import post_save_children
from api.serializers.input_output_nodes import InputOutputNodeSerializer
from api.serializers.templates import TemplateIdSerializer
from api.serializers.runs import RunIdSerializer


class RunRequestInputSerializer(InputOutputNodeSerializer):

    class Meta:
        model = RunRequestInput
        fields = ('type', 'channel', 'data',)

class RunRequestSerializer(serializers.ModelSerializer):

    uuid = serializers.UUIDField(format='hex', required=False)
    name = serializers.CharField(required=False, read_only=True)
    inputs = RunRequestInputSerializer(many=True, required=False)
    template = TemplateIdSerializer()
    run = RunIdSerializer(required=False)

    class Meta:
        model = RunRequest
        fields = ('id',
                  'uuid',
                  'name',
                  'template',
                  'inputs',
                  'datetime_created',
                  'run')

    def create(self, validated_data):
        inputs = self.initial_data.get('inputs', None)
        validated_data.pop('inputs', None)

        # Look up workflow or step 'template' using identifier string
        s = TemplateIdSerializer(data=validated_data.pop('template'))
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
