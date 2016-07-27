from django.db import IntegrityError
from rest_framework import serializers

from analysis.models.data_objects import *
from .base import SuperclassModelSerializer, NoCreateMixin, NoUpdateMixin


class StringContentSerializer(NoUpdateMixin, serializers.ModelSerializer):

    class Meta:
        model = StringContent
        fields = ('string_value',)

    
class StringDataObjectSerializer(serializers.ModelSerializer):

    loom_id = serializers.UUIDField(format='hex', required=False)
    string_content = StringContentSerializer()

    class Meta:
        model = StringDataObject
        fields = ('loom_id', 'string_content',)

    def create(self, validated_data):
        s = StringContentSerializer(data=validated_data['string_content'])
        s.is_valid(raise_exception=True)
        validated_data['string_content'] = s.save()
        return super(StringDataObjectSerializer, self).create(validated_data)

    def update(self, instance, validated_data):
        if validated_data.get('string_content'):
            s = StringContentSerializer(instance.string_content, data=validated_data['string_content'])
            s.is_valid(raise_exception=True)
            validated_data['string_content'] = s.save()
        return super(StringDataObjectSerializer, self).update(instance, validated_data)


class BooleanContentSerializer(NoUpdateMixin, serializers.ModelSerializer):

    class Meta:
        model = BooleanContent
        fields = ('boolean_value',)
        

class BooleanDataObjectSerializer(serializers.ModelSerializer):

    loom_id = serializers.UUIDField(format='hex', required=False)
    boolean_content = BooleanContentSerializer()

    class Meta:
        model = BooleanDataObject
        fields = ('loom_id', 'boolean_content',)

    def create(self, validated_data):
        s = BooleanContentSerializer(data=validated_data['boolean_content'])
        s.is_valid(raise_exception=True)
        validated_data['boolean_content'] = s.save()
        return super(BooleanDataObjectSerializer, self).create(validated_data)

    def update(self, instance, validated_data):
        if validated_data.get('boolean_content'):
            s = BooleanContentSerializer(instance.boolean_content, data=validated_data['boolean_content'])
            s.is_valid(raise_exception=True)
            validated_data['boolean_content'] = s.save()
        return super(BooleanDataObjectSerializer, self).update(instance, validated_data)


class IntegerContentSerializer(NoUpdateMixin, serializers.ModelSerializer):

    class Meta:
        model = IntegerContent
        fields = ('integer_value',)


class IntegerDataObjectSerializer(serializers.ModelSerializer):

    loom_id = serializers.UUIDField(format='hex', required=False)
    integer_content = IntegerContentSerializer()

    class Meta:
        model = IntegerDataObject
        fields = ('loom_id', 'integer_content',)

    def create(self, validated_data):
        s = IntegerContentSerializer(data=validated_data['integer_content'])
        s.is_valid(raise_exception=True)
        validated_data['integer_content'] = s.save()
        return super(IntegerDataObjectSerializer, self).create(validated_data)

    def update(self, instance, validated_data):
        if validated_data.get('integer_content'):
            s = IntegerContentSerializer(instance.integer_content, data=validated_data['integer_content'])
            s.is_valid(raise_exception=True)
            validated_data['integer_content'] = s.save()
        return super(IntegerDataObjectSerializer, self).update(instance, validated_data)


class UnnamedFileContentSerializer(NoUpdateMixin, serializers.ModelSerializer):

    class Meta:
        model = UnnamedFileContent
        fields = ('hash_value', 'hash_function',)
        validators = [] # Remove UniqueTogether validator, since the exception should be handled by the serializer

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
        s = UnnamedFileContentSerializer(data=validated_data['unnamed_file_content'])
        s.is_valid(raise_exception=True)
        validated_data['unnamed_file_content'] = s.save()
        return super(FileContentSerializer, self).create(validated_data)
    
    def update(self, instance, validated_data):
        s = UnnamedFileContentSerializer(instance.unnamed_file_content, data=validated_data['unnamed_file_content'])
        s.is_valid(raise_exception=True)
        validated_data['unnamed_file_content'] = s.save()
        return super(FileContentSerializer, self).update(instance, validated_data)


class FileLocationSerializer(serializers.ModelSerializer):

    class Meta:
        model = FileLocation
        fields = ('url', 'status',)


class FileImportSerializer(NoCreateMixin, NoUpdateMixin, serializers.ModelSerializer):

    class Meta:
        model = FileImport
        fields = ('note', 'source_url',)

    # Serializer is read-only.
    # create is allowed through FileDataObjectSerializer


class FileDataObjectSerializer(serializers.ModelSerializer):

    file_content = FileContentSerializer()
    file_import = FileImportSerializer(allow_null=True, required=False)
    file_location = FileLocationSerializer(allow_null=True, required=False)

    class Meta:
        model = FileDataObject
        fields = ('file_content', 'file_import', 'file_location',)

    def create(self, validated_data):
        
        file_import_data = validated_data.pop('file_import')
        
        if validated_data.get('file_content'):
            s = FileContentSerializer(data=validated_data['file_content'])
            s.is_valid(raise_exception=True)
            validated_data['file_content'] = s.save()
        if validated_data.get('file_location'):
            s = FileLocationSerializer(data=validated_data['file_location'])
            s.is_valid(raise_exception=True)
            validated_data['file_location'] = s.save()

        model = super(FileDataObjectSerializer, self).create(validated_data)
        
        if file_import_data:
            file_import_data.update({'file_data_object': model})
            FileImport(**file_import_data)
            s.save()

        return model

    def update(self, instance, validated_data):
        file_import_data = validated_data.pop('file_import')
        
        if validated_data.get('file_content'):
            s = FileContentSerializer(instance.file_content, data=validated_data['file_content'])
            s.is_valid(raise_exception=True)
            validated_data['file_content'] = s.save()
        if validated_data.get('file_location'):
            s = FileLocationSerializer(instance.file_location, data=validated_data['file_location'])
            s.is_valid(raise_exception=True)
            validated_data['file_location'] = s.save()

        model = super(FileDataObjectSerializer, self).update(validated_data)

        if file_import_data:
            instance.file_import.note = file_import_data.get('note', None)
            instance.file_import.source_url = file_import_data.get('source_url', None)
            instance.file_import.save()
            
        return super(FileContentSerializer, self).update(instance, validated_data)


class DataObjectSerializer(SuperclassModelSerializer):

    subclass_serializers = {
        'stringdataobject': StringDataObjectSerializer,
        'integerdataobject': IntegerDataObjectSerializer,
        'booleandataobject': BooleanDataObjectSerializer,
        'filedataobject': FileDataObjectSerializer,
    }

    class Meta(SuperclassModelSerializer.Meta):
        model = DataObject

class DataObjectContentSerializer(SuperclassModelSerializer):

    subclass_serializers = {
        'filecontent': FileContentSerializer,
        'booleancontent': BooleanContentSerializer,
        'stringcontent': StringContentSerializer,
        'integercontent': IntegerContentSerializer,
    }

    class Meta(SuperclassModelSerializer.Meta):
        model = DataObjectContent
