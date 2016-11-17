from django.db import models
from rest_framework import serializers

from .base import SuperclassModelSerializer, CreateWithParentModelSerializer, \
    IdSerializer
from api.models.data_objects import StringDataObject, BooleanDataObject, \
    IntegerDataObject, FloatDataObject, FileDataObject, DataObject, \
    FileResource, DataObjectArray


class UpdateNotAllowedError(Exception):

    pass


class BooleanDataObjectSerializer(serializers.ModelSerializer):

    id = serializers.UUIDField(format='hex', required=False)

    class Meta:
        model = BooleanDataObject
        fields = ('__all__')


class IntegerDataObjectSerializer(serializers.ModelSerializer):

    id = serializers.UUIDField(format='hex', required=False)

    class Meta:
        model = IntegerDataObject
        fields = ('__all__')


class FloatDataObjectSerializer(serializers.ModelSerializer):

    id = serializers.UUIDField(format='hex', required=False)

    class Meta:
        model = FloatDataObject
        fields = ('__all__')


class StringDataObjectSerializer(serializers.ModelSerializer):

    id = serializers.UUIDField(format='hex', required=False)

    class Meta:
        model = StringDataObject
        fields = ('__all__')


class FileResourceSerializer(serializers.ModelSerializer):

    id = serializers.UUIDField(format='hex', required=False)

    class Meta:
        model = FileResource
        fields = ('__all__')


class FileDataObjectSerializer(serializers.ModelSerializer):

    id = serializers.UUIDField(format='hex', required=False)
    file_resource = FileResourceSerializer(allow_null=True, required=False)

    class Meta:
        model = FileDataObject
        fields = ('__all__')

    def create(self, validated_data):
        validated_data['file_resource'] = self._create_file_resource(
            self.initial_data.get('file_resource', None))
        return self.Meta.model.objects.create(**validated_data)

    def _create_file_resource(self, resource_data):
        if not resource_data:
            return None
        s = FileResourceSerializer(data=resource_data)
        s.is_valid()
        return s.save()


class DataObjectSerializer(SuperclassModelSerializer):

    id = serializers.UUIDField(format='hex', required=False)

    class Meta:
        model = DataObject
        fields = '__all__'

    subclass_serializers = {
        # array type excluded to avoid circular dependency
        #'array': DataObjectArraySerializer,
        'string': StringDataObjectSerializer,
        'integer': IntegerDataObjectSerializer,
        'boolean': BooleanDataObjectSerializer,
        'float': FloatDataObjectSerializer,
        'file': FileDataObjectSerializer,
        }

    # These fields go from the base DataObject model to
    # its subclasses, to transform a base class instance
    # into the derived class
    subclass_fields = {
        'array': 'dataobjectarray',
        'string': 'stringdataobject',
        'integer': 'integerdataobject',
        'boolean': 'booleandataobject',
        'float': 'floatdataobject',
        'file': 'filedataobject',
        }

    def _get_subclass_serializer_class(self, type):
        # This has to be defined in a function due to circular dependency
        # DataObjectArraySerializer.members uses DataObjectSerializer.
        if type == 'array':
            return DataObjectArraySerializer
        else:
            return self.subclass_serializers[type]

    def _get_subclass_field(self, type):
        return self.subclass_fields[type]

    def _get_type(self, data=None, instance=None):
        if instance:
            if instance.is_array:
                return 'array'
            else:
                return instance.type
        else:
            assert data, 'either instance or data is required'
            if data.get('is_array'):
                return 'array'
            else:
                return data.get('type')


class DataObjectIdSerializer(IdSerializer, DataObjectSerializer):

    pass


class DataObjectArraySerializer(serializers.ModelSerializer):

    id = serializers.UUIDField(format='hex', required=False)
    members = DataObjectSerializer(many=True, required=False)

    class Meta:
        model = DataObjectArray
        fields = ('__all__')

    def create(self, validated_data):
        member_instances = self._create_member_instances()
        validated_data.pop('members', None)
        instance = self.Meta.model.objects.create(**validated_data)
        if member_instances:
            instance.add_members(member_instances)
        return instance

    def _create_member_instances(self):
        member_instances = []
        for member in self.initial_data.get('members', []):
            s = DataObjectSerializer(data=member)
            s.is_valid()
            member_instances.append(s.save())
        return member_instances

    def validate_is_array(self, value):
        if value == False:
            raise serializers.ValidationError(
                'DataObjectArraySerializer cannot be used if is_array=False')
        return value

    def validate(self, data):
        members = self.initial_data.get('members', [])
        for member in members:
            serializer = DataObjectSerializer(
                data=member,
                context=self.context)
            serializer.is_valid(raise_exception=True)
        return data

#    def update(self, instance, validated_data):
#        raise UpdateNotAllowedError('Update of DataObjects is not allowed')

'''
class DataObjectArraySerializer(serializers.ModelSerializer):
    """This class handles the nested 'array_members' that may be present on
    any DataObject type when is_array=True.

    When is_array=True and array_member data is present,
    array members will be created. Otherwise, the serializer will create a
    non-array instance.
    """



'''
