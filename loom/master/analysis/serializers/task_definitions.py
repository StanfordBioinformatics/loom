from .base import NestedPolymorphicModelSerializer, POLYMORPHIC_TYPE_FIELD
from .data_objects import DataObjectContentSerializer
from analysis.models.task_definitions import *

class TaskDefinitionInputSerializer(NestedPolymorphicModelSerializer):

    data_object_content = DataObjectContentSerializer(required=False)

    class Meta:
        model = TaskDefinitionInput
        nested_x_to_one_serializers = {
            'data_object_content': 'analysis.serializers.data_objects.DataObjectContentSerializer'
        }


class TaskDefinitionOutputSerializer(NestedPolymorphicModelSerializer):

    class Meta:
        model = TaskDefinitionOutput


class TaskDefinitionEnvironmentSerializer(NestedPolymorphicModelSerializer):

    class Meta:
        model = TaskDefinitionEnvironment
        subclass_serializers = {
            'taskdefinitiondockerenvironment': 'analysis.serializers.task_definitions.TaskDefinitionDockerEnvironmentSerializer'
        }


class TaskDefinitionDockerEnvironmentSerializer(TaskDefinitionEnvironmentSerializer):

    class Meta:
        model = TaskDefinitionDockerEnvironment


class TaskDefinitionSerializer(NestedPolymorphicModelSerializer):

    inputs = TaskDefinitionInputSerializer(many=True, required=False)
    outputs = TaskDefinitionOutputSerializer(many=True, required=False)
    environment = TaskDefinitionEnvironmentSerializer()
    
    class Meta:
        model = TaskDefinition
        nested_x_to_many_serializers = {
            'inputs': 'analysis.serializers.task_definitions.TaskDefinitionInputSerializer',
            'outputs': 'analysis.serializers.task_definitions.TaskDefinitionOutputSerializer',
        }
        nested_x_to_one_serializers = {
            'environment': 'analysis.serializers.task_definitions.TaskDefinitionEnvironmentSerializer',
        }

