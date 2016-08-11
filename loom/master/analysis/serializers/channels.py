from rest_framework import serializers

from analysis.models.channels import DataObjectPointer
from .data_objects import DataObjectSerializer
from .base import SuperclassModelSerializer, CreateWithParentModelSerializer, NoUpdateModelSerializer


class DataObjectPointerSerializer(CreateWithParentModelSerializer):

    data_object = DataObjectSerializer()

    class Meta:
        model = DataObjectPointer

    def create(self, validated_data):
        
