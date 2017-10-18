import copy
from api.models.tags import RunTag, DataTag, TemplateTag
from api.models.templates import Template
from api.models.data_objects import DataObject
from api.models.runs import Run
from api.serializers.data_objects import DataObjectSerializer
from api.serializers.templates import URLTemplateSerializer
from api.serializers.runs import URLRunSerializer
from rest_framework import serializers


class TemplateTagSerializer(serializers.ModelSerializer):

    class Meta:
        model = TemplateTag
        fields = ('id', 'tag')

        tag = serializers.CharField(required=True)

    def create(self, validated_data):
        template = self.context.get('template')
        validated_data.update({'template': template})
        tag = TemplateTag(**validated_data)
        tag.full_clean()
        tag.save()
        return tag


class DataTagSerializer(serializers.ModelSerializer):

    class Meta:
        model = DataTag
        fields = ('id','tag')

        tag = serializers.CharField(required=True)

    def create(self, validated_data):
        data_object = self.context.get('data_object')
        validated_data.update({'data_object': data_object})
        tag = DataTag(**validated_data)
        tag.full_clean()
        tag.save()
        return tag


class RunTagSerializer(serializers.ModelSerializer):

    class Meta:
        model = RunTag
        fields = ('id','tag')

        tag = serializers.CharField(required=True)

    def create(self, validated_data):
        run = self.context.get('run')
        validated_data.update({'run': run})
        tag = RunTag(**validated_data)
        tag.full_clean()
        tag.save()
        return tag
