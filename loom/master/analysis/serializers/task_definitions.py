from rest_framework import serializers

from .base import SuperclassModelSerializer, CreateWithParentModelSerializer, NoUpdateModelSerializer
from .data_objects import DataObjectContentSerializer
from analysis.models.task_definitions import *


class TaskDefinitionInputSerializer(NoUpdateModelSerializer,
                                    CreateWithParentModelSerializer):
                                    

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


class TaskDefinitionOutputSerializer(NoUpdateModelSerializer,
                                     CreateWithParentModelSerializer):

    class Meta:
        model = TaskDefinitionOutput
        fields = ('filename', 'type',)


class TaskDefinitionDockerEnvironmentSerializer(
        CreateWithParentModelSerializer,
        NoUpdateModelSerializer):

    class Meta:
        model = TaskDefinitionDockerEnvironment
        fields = ('docker_image',)


class TaskDefinitionEnvironmentSerializer(NoUpdateModelSerializer,
                                          SuperclassModelSerializer):

    subclass_serializers = {
        'taskdefinitiondockerenvironment':
        TaskDefinitionDockerEnvironmentSerializer,
    }

    class Meta:
        model = TaskDefinitionEnvironment
        fields = ()


class TaskDefinitionSerializer(NoUpdateModelSerializer):

    inputs = TaskDefinitionInputSerializer(many=True, required=False)
    outputs = TaskDefinitionOutputSerializer(many=True, required=False)
    environment = TaskDefinitionEnvironmentSerializer()

    class Meta:
        model = TaskDefinition
        fields = ('inputs', 'outputs', 'environment', 'command',)

    def create(self, validated_data):

        inputs = self.initial_data.get('inputs', None)
        outputs = self.initial_data.get('outputs', None)
        environment = self.initial_data.get('environment', None)
        validated_data.pop('inputs', None)
        validated_data.pop('outputs', None)
        validated_data.pop('environment', None)

        model = super(self.__class__, self).create(validated_data)

        if inputs is not None:
            new_inputs = []
            for input_data in inputs:
                s = TaskDefinitionInputSerializer(
                    data=input_data,
                    context={'parent_field': 'task_definition',
                    'parent_instance': model})
                s.is_valid(raise_exception=True)
                s.save()

        if outputs is not None:
            new_outputs = []
            for output_data in outputs:
                s = TaskDefinitionOutputSerializer(
                    data=output_data,
                    context={'parent_field': 'task_definition',
                             'parent_instance': model})
                s.is_valid(raise_exception=True)
                s.save()


        if environment is not None:
            s = TaskDefinitionEnvironmentSerializer(
                data=environment,
                context={'parent_field': 'task_definition',
                         'parent_instance': model})
            s.is_valid(raise_exception=True)
            s.save()


        return model
