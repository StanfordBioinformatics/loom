from rest_framework import serializers
from django.db import models

from .base import CreateWithParentModelSerializer
from api.models.input_output_nodes import InputOutputNode
from .data_trees import DataNodeSerializer, DataNodeUuidSerializer


class InputOutputNodeSerializer(CreateWithParentModelSerializer):

    data = serializers.JSONField()

    def create(self, validated_data):
        data = validated_data.pop('data')

        if self.context.get('parent_field') \
           and self.context.get('parent_instance'):
            validated_data.update({
                self.context.get('parent_field'):
                self.context.get('parent_instance')})

        # Class of io_node depends on subclass.Meta.model
        io_node =  self.Meta.model.objects.create(**validated_data)

        if data is not None:
            type = validated_data.get('type')
            if not type:
                raise Exception('data type is required')
            data_node_serializer = DataNodeSerializer(
                data=data,
                context = {'type': type})
            data_node_serializer.is_valid(raise_exception=True)
            data_root = data_node_serializer.save()
            io_node.data_root = data_root
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
            if instance.data_root is not None:
                data_node_serializer = DataNodeUuidSerializer(instance.data_root)
                try:
                    representation['data'] = data_node_serializer.data
                except:
                   # Avoid raising exceptions when deserializing
                    pass
            return representation
