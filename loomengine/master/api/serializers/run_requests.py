import json
from rest_framework import serializers

from .base import SuperclassModelSerializer, CreateWithParentModelSerializer
from api.models.data_objects import DataObject
from api.models.runs import Run
from api.models.run_requests import RunRequest, RunRequestInput
from api.models.signals import post_save_children
from api.serializers.input_output_nodes import InputOutputNodeSerializer
from api.serializers.templates import TemplateSerializer, ExpandableTemplateSerializer
from api import tasks


class RunRequestInputSerializer(InputOutputNodeSerializer):

    type = serializers.CharField(required=False)

    class Meta:
        model = RunRequestInput
        fields = ('type', 'channel', 'data',)


class RunRequestSerializer(serializers.ModelSerializer):

    inputs = RunRequestInputSerializer(many=True, required=False)
    template = ExpandableTemplateSerializer()
    uuid = serializers.UUIDField(required=False)

    class Meta:
        model = RunRequest
        fields = ('uuid',
                  'template',
                  'inputs',
                  'datetime_created')

    def create(self, validated_data):
        inputs = self.initial_data.get('inputs', None)
        validated_data.pop('inputs', None)

        # Look up workflow or step 'template' using identifier string
        s = TemplateSerializer(data=validated_data.pop('template'))
        s.is_valid()
        template = s.save()
        
        validated_data['template'] = template

        run_request = RunRequest.objects.create(**validated_data)
        
        if inputs is not None:
            for input_data in inputs:
                # We need to know the data type to find or create the
                # data object from the value given. Get that from the
                # corresponding workflow input.
                type = template.get_input(input_data['channel']).get('type')
                input_data.update({'type': type})
                s = RunRequestInputSerializer(
                    data=input_data,
                    context={'parent_field': 'run_request',
                             'parent_instance': run_request
                         })
                s.is_valid(raise_exception=True)
                s.save()

        run_request.initialize_run()
        
        return run_request
