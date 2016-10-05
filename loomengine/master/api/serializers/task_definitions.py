from rest_framework import serializers

from .base import SuperclassModelSerializer, CreateWithParentModelSerializer
from .data_objects import DataObjectContentSerializer
from api.models.task_definitions import TaskDefinition, TaskDefinitionInput, \
    TaskDefinitionOutput, TaskDefinitionOutputSource, TaskDefinitionOutputParser, \
    TaskDefinitionDockerEnvironment, TaskDefinitionEnvironment


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


class TaskDefinitionOutputSourceSerializer(CreateWithParentModelSerializer):

    class Meta:
        model = TaskDefinitionOutputSource
        fields = ('filename', 'stream')


class TaskDefinitionOutputParserSerializer(CreateWithParentModelSerializer):

    class Meta:
        model = TaskDefinitionOutputParser
        fields = ('type', 'delimiter')


class TaskDefinitionOutputSerializer(CreateWithParentModelSerializer):

    source = TaskDefinitionOutputSourceSerializer(read_only=True)
    parser = TaskDefinitionOutputParserSerializer(read_only=True)
    
    class Meta:
        model = TaskDefinitionOutput
        fields = ('source', 'type', 'parser',)


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
