import copy
import django.core.exceptions
from api.models.labels import RunLabel, DataLabel, TemplateLabel
from api.models.templates import Template
from api.models.data_objects import DataObject
from api.models.runs import Run
from api.serializers.data_objects import DataObjectSerializer
from api.serializers.templates import URLTemplateSerializer
from api.serializers.runs import URLRunSerializer
from rest_framework import serializers


class TemplateLabelSerializer(serializers.ModelSerializer):

    class Meta:
        model = TemplateLabel
        fields = ('id','label')

        label = serializers.CharField(required=True)

    def create(self, validated_data):
        template = self.context.get('template')
        validated_data.update({'template': template})
        label = TemplateLabel(**validated_data)
        try:
            label.full_clean()
            label.save()
        except django.core.exceptions.ValidationError as e:
            raise serializers.ValidationError(e.message_dict)
        return label


class DataLabelSerializer(serializers.ModelSerializer):

    class Meta:
        model = DataLabel
        fields = ('id','label')

        label = serializers.CharField(required=True)

    def create(self, validated_data):
        data_object = self.context.get('data_object')
        validated_data.update({'data_object': data_object})
        label = DataLabel(**validated_data)
        try:
            label.full_clean()
            label.save()
        except django.core.exceptions.ValidationError as e:
            raise serializers.ValidationError(e.message_dict)
        return label


class RunLabelSerializer(serializers.ModelSerializer):

    class Meta:
        model = RunLabel
        fields = ('id','label')

        label = serializers.CharField(required=True)

    def create(self, validated_data):
        run = self.context.get('run')
        validated_data.update({'run': run})
        label = RunLabel(**validated_data)
        try:
            label.full_clean()
            label.save()
        except django.core.exceptions.ValidationError as e:
            raise serializers.ValidationError(e.message_dict)
        return label
