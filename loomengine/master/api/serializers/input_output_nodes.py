from rest_framework import serializers
from django.db import models

from .base import CreateWithParentModelSerializer
from api.models.input_output_nodes import InputOutputNode
from api.serializers.data_nodes import DataNodeSerializer

class InputOutputNodeSerializer(CreateWithParentModelSerializer):

    data = serializers.JSONField()
    type = serializers.CharField()
    channel = serializers.CharField()

    def create(self, validated_data):
        data = validated_data.pop('data', None)

        io_node = super(InputOutputNodeSerializer, self).create(validated_data)
        if data is not None:
            type = validated_data.get('type')
            if not type:
                raise Exception('data type is required')
            data_node_serializer = DataNodeSerializer(
                data=data,
                context = {'type': type})
            data_node_serializer.is_valid(raise_exception=True)
            data_tree = data_node_serializer.save()
            io_node.data_tree = data_tree
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
            if instance.data_tree is not None:
                data_node_serializer = DataNodeSerializer(
                    instance.data_tree,
                    context=self.context)
                representation['data'] = data_node_serializer.data
            return representation
