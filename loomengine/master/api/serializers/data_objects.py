from django.db import IntegrityError
from rest_framework import serializers

from .base import SuperclassModelSerializer, CreateWithParentModelSerializer, \
    RecursiveField
from api.models.data_objects import StringDataObject, BooleanDataObject, \
    IntegerDataObject, FloatDataObject, FileDataObject, DataObject, \
    FileResource


class UpdateNotAllowedError(Exception):
    pass


class AbstractDataObjectArraySerializer(serializers.ModelSerializer):
    """This class handles the nested 'array_members' that may be present on
    any DataObject type when is_array=True.

    When is_array=True and array_member data is present,
    array members will be created. Otherwise, the serializer will create a
    non-array instance.
    """

    id = serializers.UUIDField(format='hex', required=False)
    array_members = RecursiveField(many=True, required=False)

    def create(self, validated_data):
        member_instances = self._create_member_instances()
        validated_data.pop('array_members', None)
        instance = self.Meta.model.objects.create(**validated_data)
        if member_instances:
            instance.add_members(member_instances)
        return instance

    def update(self, instance, validated_data):
        raise UpdateNotAllowedError('Update of DataObjects is not allowed')

    def _create_member_instances(self):
        member_instances = []
        for array_member in self.initial_data.get('array_members', []):
            s = self.__class__(data=array_member)
            s.is_valid()
            member_instances.append(s.save())
        return member_instances

        
    def validate_type(self, value):
        if value != self.type:
            raise serializers.ValidationError(
                'Invalid "type" value:" %s". '\
                'Field "type" must have value "%s" for %s.' % (
                    value, self.type, self.__class__.__name__))
        return value

    def validate(self, data):
        is_array = data.get('is_array', True)
        array_members = data.get('array_members', None)
        if not is_array and array_members is not None:
            raise serializers.ValidationError(
                'Incompatible values is_array="%s" and array_members="%s"' % (
                    is_array, array_members))
        return data


class BooleanDataObjectSerializer(AbstractDataObjectArraySerializer):
    type='boolean'
    class Meta:
        model = BooleanDataObject
        fields = ('__all__')


class IntegerDataObjectSerializer(AbstractDataObjectArraySerializer):
    type='integer'
    class Meta:
        model = IntegerDataObject
        fields = ('__all__')


class FloatDataObjectSerializer(AbstractDataObjectArraySerializer):
    type='float'
    class Meta:
        model = FloatDataObject
        fields = ('__all__')


class StringDataObjectSerializer(AbstractDataObjectArraySerializer):
    type='string'
    class Meta:
        model = StringDataObject
        fields = ('__all__')


class FileResourceSerializer(serializers.ModelSerializer):

    id = serializers.UUIDField(format='hex', required=False)

    class Meta:
        model = FileResource
        fields = ('__all__')


class FileDataObjectSerializer(AbstractDataObjectArraySerializer):

    type = 'file'

    file_resource = FileResourceSerializer(allow_null=True, required=False)
    source_type = serializers.CharField(required=False)

    class Meta:
        model = FileDataObject
        fields = ('__all__')

    def create(self, validated_data):
        member_instances = self._create_member_instances()
        validated_data.pop('array_members', None)

        validated_data['file_resource'] = self._create_file_resource(
            self.initial_data.get('file_resource', None))

        instance = self.Meta.model.objects.create(**validated_data)
        if member_instances:
            instance.add_members(member_instances)
        return instance

    def _create_file_resource(self, resource_data):
        if not resource_data:
            return None
        s = FileResourceSerializer(data=resource_data)
        s.is_valid()
        return s.save()


class DataObjectSerializer(SuperclassModelSerializer):

    subclass_serializers = {
        'string': StringDataObjectSerializer,
        'integer': IntegerDataObjectSerializer,
        'boolean': BooleanDataObjectSerializer,
        'float': FloatDataObjectSerializer,
        'file': FileDataObjectSerializer,
    }

    class Meta:
        model = DataObject
        fields = '__all__'
