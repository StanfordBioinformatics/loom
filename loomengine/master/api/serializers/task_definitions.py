from rest_framework import serializers

from .base import SuperclassModelSerializer, CreateWithParentModelSerializer
from .data_objects import DataObjectContentSerializer
from api.models.task_definitions import TaskDefinition, TaskDefinitionInput, \
    TaskDefinitionOutput, TaskDefinitionDockerEnvironment, TaskDefinitionEnvironment


class TaskDefinitionInputSerializer(CreateWithParentModelSerializer):

    data_object_content = DataObjectContentSerializer(required=False)

    class Meta:
        model = TaskDefinitionInput
        fields = ('data_object_content', 'type',)

    def create(self, validated_data):
        s = DataObjectContentSerializer(
            data=self.initial_data['data_object_content'])
        s.is_valid(raise_exception=True)
        validated_data['data_object_content'] = s.save()
        return super(self.__class__, self).create(validated_data)


class TaskDefinitionOutputSerializer(CreateWithParentModelSerializer):

    class Meta:
        model = TaskDefinitionOutput
        fields = ('filename', 'type',)


class TaskDefinitionDockerEnvironmentSerializer(CreateWithParentModelSerializer):

    class Meta:
        model = TaskDefinitionDockerEnvironment
        fields = ('docker_image',)


class TaskDefinitionEnvironmentSerializer(SuperclassModelSerializer):

    subclass_serializers = {
        'taskdefinitiondockerenvironment':
        TaskDefinitionDockerEnvironmentSerializer,
    }

    class Meta:
        model = TaskDefinitionEnvironment
        fields = ()


class TaskDefinitionSerializer(serializers.ModelSerializer):

    inputs = TaskDefinitionInputSerializer(many=True, required=False)
    outputs = TaskDefinitionOutputSerializer(many=True, required=False)
    environment = TaskDefinitionEnvironmentSerializer()

    class Meta:
        model = TaskDefinition
        fields = ('inputs', 'outputs', 'environment', 'command', 'interpreter')
