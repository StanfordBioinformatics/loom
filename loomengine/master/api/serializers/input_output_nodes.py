from rest_framework import serializers
from django.db import models

from .base import CreateWithParentModelSerializer
from api.models.input_output_nodes import InputOutputNode
from api.serializers.data_objects import DataObjectSerializer

class InputOutputNodeSerializer(CreateWithParentModelSerializer):

    data = serializers.JSONField()

    def create(self, validated_data):
        data = validated_data.pop('data', None)

        io_node = super(InputOutputNodeSerializer, self).create(validated_data)
        if data is not None:
            type = validated_data.get('type')
            if not type:
                raise Exception('data type is required')
            data_object_serializer = DataObjectSerializer(
                data=data,
                context = {'type': type})
            data_object_serializer.is_valid(raise_exception=True)
            data_object = data_object_serializer.save()
            io_node.data_object = data_object
            io_node.save()
        return io_node

    def to_representation(self, instance):
        if not isinstance(instance, models.Model):
            # If the Serializer was instantiated with data instead of a model,
            # "instance" is an OrderedDict.
            return super(InputOutputNodeSerializer, self).to_representation(
                instance)
        else:
            assert isinstance(instance, InputOutputNode)
            representation = super(InputOutputNodeSerializer, self)\
                .to_representation(instance)
            if instance.data_object is not None:
                data_object_serializer = DataObjectSerializer(
                    instance.data_object,
                    context=self.context)
                representation['data'] = data_object_serializer.data
            return representation
