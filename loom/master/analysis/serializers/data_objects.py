from django.db import IntegrityError
from rest_framework import serializers

from analysis.models.data_objects import *
from .base import SuperclassModelSerializer, NoCreateMixin, NoUpdateMixin
from .exceptions import *


class StringContentSerializer(NoUpdateMixin, serializers.ModelSerializer):

    class Meta:
        model = StringContent
        fields = ('string_value',)

    
class StringDataObjectSerializer(serializers.ModelSerializer):

    id = serializers.UUIDField(format='hex', required=False)
    string_content = StringContentSerializer()

    class Meta:
        model = StringDataObject
        fields = ('id', 'string_content',)

    def create(self, validated_data):
        s = StringContentSerializer(data=validated_data['string_content'])
        s.is_valid(raise_exception=True)
        validated_data['string_content'] = s.save()
        return super(self.__class__, self).create(validated_data)

    def update(self, instance, validated_data):
        if validated_data.get('string_content'):
            s = StringContentSerializer(instance.string_content,
                                        data=validated_data['string_content'])
            s.is_valid(raise_exception=True)
            validated_data['string_content'] = s.save()
        return super(self.__class__, self).update(
            instance,
            validated_data)


class BooleanContentSerializer(NoUpdateMixin, serializers.ModelSerializer):

    class Meta:
        model = BooleanContent
        fields = ('boolean_value',)
        

class BooleanDataObjectSerializer(serializers.ModelSerializer):

    id = serializers.UUIDField(format='hex', required=False)
    boolean_content = BooleanContentSerializer()

    class Meta:
        model = BooleanDataObject
        fields = ('id', 'boolean_content',)

    def create(self, validated_data):
        s = BooleanContentSerializer(data=validated_data['boolean_content'])
        s.is_valid(raise_exception=True)
        validated_data['boolean_content'] = s.save()
        return super(self.__class__, self).create(validated_data)

    def update(self, instance, validated_data):
        if validated_data.get('boolean_content'):
            s = BooleanContentSerializer(
                instance.boolean_content,
                data=validated_data['boolean_content'])
            s.is_valid(raise_exception=True)
            validated_data['boolean_content'] = s.save()
        return super(self.__class__, self).update(
            instance,
            validated_data)


class IntegerContentSerializer(NoUpdateMixin, serializers.ModelSerializer):

    class Meta:
        model = IntegerContent
        fields = ('integer_value',)


class IntegerDataObjectSerializer(serializers.ModelSerializer):

    id = serializers.UUIDField(format='hex', required=False)
    integer_content = IntegerContentSerializer()

    class Meta:
        model = IntegerDataObject
        fields = ('id', 'integer_content',)

    def create(self, validated_data):
        s = IntegerContentSerializer(data=validated_data['integer_content'])
        s.is_valid(raise_exception=True)
        validated_data['integer_content'] = s.save()
        return super(self.__class__, self).create(validated_data)

    def update(self, instance, validated_data):
        if validated_data.get('integer_content'):
            s = IntegerContentSerializer(
                instance.integer_content,
                data=validated_data['integer_content'])
            s.is_valid(raise_exception=True)
            validated_data['integer_content'] = s.save()
        return super(self.__class__, self).update(
            instance,
            validated_data)


class UnnamedFileContentSerializer(NoUpdateMixin, serializers.ModelSerializer):

    class Meta:
        model = UnnamedFileContent
        fields = ('hash_value', 'hash_function',)
        # Remove UniqueTogether validator, since the exception
        # should be handled by the serializer
        validators = []

    def create(self, validated_data):
        try:
            return self.Meta.model.objects.create(**validated_data)
        except IntegrityError:
            return self.Meta.model.objects.get(**validated_data)


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
        return super(self.__class__, self).create(validated_data)

    def update(self, instance, validated_data):
        # Update not allowed. This method just raises an error if
        # any data was changed.
        s = UnnamedFileContentSerializer(
            instance.unnamed_file_content,
            data=validated_data['unnamed_file_content'])
        s.is_valid(raise_exception=True)
        s.save()
        if validated_data.get('filename'):
            if not validated_data.get('filename') == instance.filename:
                raise UpdateNotAllowedError(instance)
        return instance


class FileLocationSerializer(serializers.ModelSerializer):

    id = serializers.UUIDField(format='hex', required=False)

    class Meta:
        model = FileLocation
        fields = ('id', 'url', 'status',)

    @classmethod
    def no_update(cls, instance, data):
        for key, value in data.iteritems():
            if not getattr(instance, key) == value:
                raise serializers.ValidationError(
                    "You are not allowed to update a File Location as "\
                    "part of a FileDataObject update, because one location "\
                    "may belong to multiple files. This is to prevent "\
                    "accidental data corruption. If you want to make the "\
                    "update, you must update the FileLocation object "
                    "directly in a separate request.")


class FileImportSerializer(NoCreateMixin, NoUpdateMixin,
                           serializers.ModelSerializer):

    class Meta:
        model = FileImport
        fields = ('note', 'source_url',)

    # FileImportSerializer is read-only.
    # create is allowed through FileDataObjectSerializer


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
                  'file_location',)


    def create(self, validated_data):
        # Can't create FileImport until FileDataObject exists
        file_import_data = validated_data.pop('file_import', None)

        if validated_data.get('file_content'):
            s = FileContentSerializer(data=validated_data['file_content'])
            s.is_valid(raise_exception=True)
            validated_data['file_content'] = s.save()

        # Handle file_location and temp_file_location in the same way
        if validated_data.get('file_location'):
                # Since location is OneToMany,
                # we may be connecting to an existing object
                file_location = None
                if validated_data['file_location'].get('id'):
                    try:
                        file_location = FileLocation.objects.get(
                            id=validated_data['file_location']['id'])
                    except FileLocation.DoesNotExist:
                        pass
                if file_location is None:
                    s = FileLocationSerializer(
                        data=validated_data['file_location'])
                    s.is_valid(raise_exception=True)
                    file_location = s.save()

                validated_data['file_location'] = file_location

        model = super(self.__class__, self).create(validated_data)

        if file_import_data is not None:
            file_import_data.update({'file_data_object': model})
            fi = FileImport(**file_import_data)
            fi.save()

        model.send_post_create()
        return model

    def update(self, instance, validated_data):
        # Can't create FileImport until FileDataObject exists
        file_import_data = validated_data.pop('file_import', None)

        if validated_data.get('file_content'):
            s = FileContentSerializer(
                instance.file_content,
                data=validated_data['file_content'])
            s.is_valid(raise_exception=True)
            validated_data['file_content'] = s.save()
        if validated_data.get('file_location'):
            file_location = None
            if validated_data['file_location'].get('id') is not None:
                # This is an update if a model with the specified ID exists.
                try:
                    file_location = FileLocation.objects.get(
                        id=validated_data['file_location'].get('id'))
                    # Verify no changes to FileLocation
                    FileLocationSerializer.no_update(
                        file_location,
                        data=validated_data['file_location'])
                except FileLocation.DoesNotExist:
                    pass

            if file_location is None:
                # This is a create operation, either because
                # no Location with the specified id exists,
                # or because no id was given
                s = FileLocationSerializer(
                    data=validated_data['file_location'])
                s.is_valid(raise_exception=True)
                file_location = s.save()

            validated_data['file_location'] = file_location

        model = super(self.__class__, self).update(
            instance,
            validated_data)

        if file_import_data is not None:
            instance.file_import.note = file_import_data.get('note', None)
            instance.file_import.source_url = file_import_data.get(
                'source_url',
                None)
            instance.file_import.save()

        model.send_post_update()
        return model


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
