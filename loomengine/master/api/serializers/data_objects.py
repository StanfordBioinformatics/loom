from django.db import models
from rest_framework import serializers

from .base import SuperclassModelSerializer, CreateWithParentModelSerializer, \
    RecursiveField
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


class DataObjectSerializer(serializers.ModelSerializer):

    id = serializers.UUIDField(format='hex', required=False)

    subclass_serializers = {
        # array type excluded to avoid circular dependency
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

    def _get_subclass_serializer_class(self, type, is_array):
        # This has to be defined in a function due to circular dependency
        # DataObjectArraySerializer.members uses DataObjectSerializer.
        array_serializer = DataObjectArraySerializer

        if is_array:
            return array_serializer
        else:
            return self.subclass_serializers[type]

    def _get_subclass_field(self, type, is_array):
        if is_array:
            return self.subclass_fields['array']
        else:
            return self.subclass_fields[type]

    class Meta:
        model = DataObject
        fields = '__all__'

    def validate(self, data):
        # This is critical to validating data against the SubclassSerializer
        if not hasattr(self, 'initial_data'):
            # No further validation possible if called in a mode without
            # initial data, because required fields may be lost
            return data
        type = data.get('type')
        is_array = data.get('is_array')
        SubclassSerializer \
            = self._get_subclass_serializer_class(type, is_array)
        serializer = SubclassSerializer(
            data=self.initial_data,
            context=self.context)
        serializer.is_valid(raise_exception=True)
        return data

    def create(self, validated_data):
        type = validated_data.get('type')
        is_array = validated_data.get('is_array')
        SubclassSerializer \
            = self._get_subclass_serializer_class(type, is_array)
        serializer = SubclassSerializer(
            data=self.initial_data,
            context=self.context)
        serializer.is_valid(raise_exception=True)
        return serializer.save()

    def update(self, instance, validated_data):
        type = instance.type
        is_array = instance.is_array
        SubclassSerializer \
            = self._get_subclass_serializer_class(type, is_array)
        serializer = SubclassSerializer(
            data=self.initial_data,
            context=self.context)
        serializer.is_valid(raise_exception=True)
        return serializer.save()

    def to_representation(self, instance):
        if not isinstance(instance, models.Model):
            # If the Serializer was instantiated with data instead of a model,
            # "instance" is an OrderedDict. It may be missing data in fields
            # that are on the subclass but not on the superclass, so we go
            # back to initial_data.
            type = instance.get('type')
            is_array = instance.get('is_array')
            SubclassSerializer = self._get_subclass_serializer_class(
                type, is_array)
            serializer = SubclassSerializer(data=self.initial_data)
            return super(serializer.__class__, serializer).to_representation(
                self.initial_data)
        else:
            assert isinstance(instance, self.Meta.model)
            # Execute "to_representation" on the correct subclass serializer
            type = instance.type
            is_array = instance.is_array
            SubclassSerializer = self._get_subclass_serializer_class(
                type, is_array)
            subclass_field = self._get_subclass_field(type, is_array)
            try:
                instance = getattr(instance, subclass_field)
            except ObjectDoesNotExist:
                pass
            serializer = SubclassSerializer(instance, context=self.context)
            return super(serializer.__class__, serializer).to_representation(
                instance)

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
