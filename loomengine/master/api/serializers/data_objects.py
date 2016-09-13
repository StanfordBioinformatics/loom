from django.db import IntegrityError
from rest_framework import serializers

from .base import SuperclassModelSerializer, CreateWithParentModelSerializer
from api.models.data_objects import StringContent, StringDataObject, \
    BooleanContent, BooleanDataObject, IntegerContent, IntegerDataObject, \
    UnnamedFileContent, FileContent, FileImport, FileLocation, \
    FileDataObject, DataObject, DataObjectContent


class StringContentSerializer(serializers.ModelSerializer):

    class Meta:
        model = StringContent
        fields = ('string_value',)


class StringDataObjectSerializer(serializers.ModelSerializer):

    id = serializers.UUIDField(format='hex', required=False)
    string_content = StringContentSerializer()

    class Meta:
        model = StringDataObject
        fields = ('id', 'string_content', 'datetime_created', 'type',)

    def create(self, validated_data):
        s = StringContentSerializer(data=validated_data['string_content'])
        s.is_valid(raise_exception=True)
        validated_data['string_content'] = s.save()
        return StringDataObject.objects.create(**validated_data)


class BooleanContentSerializer(serializers.ModelSerializer):

    class Meta:
        model = BooleanContent
        fields = ('boolean_value',)


class BooleanDataObjectSerializer(serializers.ModelSerializer):

    id = serializers.UUIDField(format='hex', required=False)
    boolean_content = BooleanContentSerializer()

    class Meta:
        model = BooleanDataObject
        fields = ('id', 'boolean_content', 'datetime_created', 'type',)

    def create(self, validated_data):
        s = BooleanContentSerializer(data=validated_data['boolean_content'])
        s.is_valid(raise_exception=True)
        validated_data['boolean_content'] = s.save()
        return BooleanDataObject.objects.create(**validated_data)


class IntegerContentSerializer(serializers.ModelSerializer):

    class Meta:
        model = IntegerContent
        fields = ('integer_value',)


class IntegerDataObjectSerializer(serializers.ModelSerializer):

    id = serializers.UUIDField(format='hex', required=False)
    integer_content = IntegerContentSerializer()

    class Meta:
        model = IntegerDataObject
        fields = ('id', 'integer_content', 'datetime_created', 'type',)

    def create(self, validated_data):
        s = IntegerContentSerializer(data=validated_data['integer_content'])
        s.is_valid(raise_exception=True)
        validated_data['integer_content'] = s.save()
        return IntegerDataObject.objects.create(**validated_data)


class UnnamedFileContentSerializer(serializers.ModelSerializer):

    class Meta:
        model = UnnamedFileContent
        fields = ('hash_value', 'hash_function',)
        # Remove UniqueTogether validator, since the exception
        # should be handled by the create method
        validators = []

    def create(self, validated_data):
        # If the object already exists, return return the existing object.
        try:
            return UnnamedFileContent.objects.create(**validated_data)
        except IntegrityError:
            # (hash_function, hash_value) are unique_together.
            # IntegrityError implies object already exists.
            return UnnamedFileContent.objects.get(**validated_data)

class FileContentSerializer(serializers.ModelSerializer):

    unnamed_file_content = UnnamedFileContentSerializer()

    class Meta:
        model = FileContent
        fields = ('unnamed_file_content', 'filename',)

    def create(self, validated_data):
        s = UnnamedFileContentSerializer(
            data=validated_data['unnamed_file_content'])
        s.is_valid(raise_exception=True)
        validated_data['unnamed_file_content'] = s.save()
        # Same pattern as for UnnamedFileContent.
        # Here (filename, unnamed_file_content) are unique_together
        try:
            return FileContent.objects.create(**validated_data)
        except IntegrityError:
            return FileContent.objects.get(**validated_data)

class FileLocationSerializer(serializers.ModelSerializer):

    id = serializers.UUIDField(format='hex', required=False)

    class Meta:
        model = FileLocation
        fields = ('id', 'url', 'status', 'datetime_created')


class FileImportSerializer(CreateWithParentModelSerializer):

    # FileImportSerializer is read-only.
    # create is allowed through FileDataObjectSerializer

    class Meta:
        model = FileImport
        fields = ('note', 'source_url',)


class FileDataObjectSerializer(serializers.ModelSerializer):

    id = serializers.UUIDField(format='hex', required=False)
    file_content = FileContentSerializer(allow_null=True, required=False)
    file_import = FileImportSerializer(allow_null=True, required=False)
    file_location = FileLocationSerializer(allow_null=True, required=False)

    class Meta:
        model = FileDataObject
        fields = ('id',
                  'file_content',
                  'file_import',
                  'file_location',
                  'datetime_created',
                  'source_type',
                  'type',)

    def create(self, validated_data):
        file_import_data = validated_data.pop('file_import', None)
        file_content_data = validated_data.pop('file_content', None)
        file_location_data = validated_data.pop('file_location', None)

        if file_content_data:
            s = FileContentSerializer(data=file_content_data)
            s.is_valid(raise_exception=True)
            validated_data['file_content'] = s.save()

        if file_location_data:
                # Since location is OneToMany,
                # we may be connecting to an existing object
                file_location = None
                if file_location_data.get('id'):
                    try:
                        file_location = FileLocation.objects.get(
                            id=file_location_data['id'])
                    except FileLocation.DoesNotExist:
                        pass
                if file_location is None:
                    s = FileLocationSerializer(
                        data=file_location_data)
                    s.is_valid(raise_exception=True)
                    file_location = s.save()

                validated_data['file_location'] = file_location

        model = FileDataObject.objects.create(**validated_data)

        # FileImport can only be created after FileDataObject exists
        if file_import_data is not None:
            s = FileImportSerializer(
                data=file_import_data,
                context={'parent_field': 'file_data_object',
                         'parent_instance': model,})
            s.is_valid()
            s.save()

        model.after_create()
        return model

    def update(self, instance, validated_data):
        file_content_data = validated_data.pop('file_content', None)
        file_location_data = validated_data.pop('file_location', None)

        if file_content_data and not instance.file_content:
            s = FileContentSerializer(
                data=file_content_data)
            s.is_valid(raise_exception=True)
            instance.file_content = s.save()

        if file_location_data:
            s = FileLocationSerializer(
                data=file_location_data)
            s.is_valid(raise_exception=True)
            instance.file_location = s.save()

        instance.save()
        instance.after_update()
        return instance


class DataObjectSerializer(SuperclassModelSerializer):

    subclass_serializers = {
        'stringdataobject': StringDataObjectSerializer,
        'integerdataobject': IntegerDataObjectSerializer,
        'booleandataobject': BooleanDataObjectSerializer,
        'filedataobject': FileDataObjectSerializer,
    }

    class Meta:
        model = DataObject


class DataObjectContentSerializer(SuperclassModelSerializer):

    subclass_serializers = {
        'filecontent': FileContentSerializer,
        'booleancontent': BooleanContentSerializer,
        'stringcontent': StringContentSerializer,
        'integercontent': IntegerContentSerializer,
    }

    class Meta:
        model = DataObjectContent
