from rest_framework import serializers
from django.db import models

from . import CreateWithParentModelSerializer
from api.models.data_channels import DataChannel
from api.serializers.data_nodes import DataNodeSerializer

class DataChannelSerializer(CreateWithParentModelSerializer):

    data = serializers.JSONField()
    type = serializers.CharField()
    channel = serializers.CharField()

    def create(self, validated_data):
        data = validated_data.pop('data', None)
        data_channel = super(DataChannelSerializer, self).create(validated_data)
        if data is not None:
            type = validated_data.get('type')
            if not type:
                raise Exception('data type is required')
            data_node_serializer = DataNodeSerializer(
                data=data,
                context = {'type': type})
            data_node_serializer.is_valid(raise_exception=True)
            data_node = data_node_serializer.save()
            data_channel.setattrs_and_save_with_retries({
                'data_node': data_node})
        return data_channel

    def update(self, instance, validated_data):
        # This is used to add data to an existing node
        data = validated_data.pop('data', None)
        if data is not None:
            if instance.data_node:
                raise serializers.ValidationError('Update to existing data not allowed')
            data_node_serializer = DataNodeSerializer(
                data=data,
                context = {'type': instance.type,
                           'task_attempt': instance.task_attempt})
            data_node_serializer.is_valid(raise_exception=True)
            data_node = data_node_serializer.save()
            instance.setattrs_and_save_with_retries({
                'data_node': data_node})
        return instance

    def to_representation(self, instance):
        if not isinstance(instance, models.Model):
            # If the Serializer was instantiated with data instead of a model,
            # "instance" is an OrderedDict.
            return super(DataChannelSerializer, self).to_representation(
                instance)
        else:
            assert isinstance(instance, DataChannel)
            instance.prefetch()
            representation = super(DataChannelSerializer, self)\
                             .to_representation(instance)
            if instance.data_node is not None:
                data_node_serializer = DataNodeSerializer(
                    instance.data_node,
                    context=self.context)
                representation['data'] = data_node_serializer.data
            return representation
