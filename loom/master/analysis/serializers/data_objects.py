import copy
from rest_framework import serializers
from analysis.models.data_objects import *
from .base import MagicSerializer, _POLYMORPHIC_TYPE_FIELD

class DataObjectSerializer(MagicSerializer):

    class Meta:
        model = DataObject
        exclude = (_POLYMORPHIC_TYPE_FIELD,)
        subclass_serializers = {
            'file_data_object': 'analysis.serializers.data_objects.FileDataObjectSerializer',
            'json_data_object': 'analysis.serializers.data_objects.JSONDataObjectSerializer',
            'string_data_object': 'analysis.serializers.data_objects.StringDataObjectSerializer',
            'integer_data_object': 'analysis.serializers.data_objects.IntegerDataObjectSerializer',
        }


class DataObjectContentSerializer(MagicSerializer):

    class Meta:
        model = DataObjectContent
        exclude = (_POLYMORPHIC_TYPE_FIELD,)
        subclass_serializers = {
            'file_data_object_content': 'analysis.serializers.data_objects.FileDataObjectContentSerializer',
            'json_data_object_content': 'analysis.serializers.data_objects.JSONDataObjectContentSerializer',
            'string_data_object_content': 'analysis.serializers.data_objects.StringDataObjectContentSerializer',
            'integer_data_object_content': 'analysis.serializers.data_objects.IntegerDataObjectContentSerializer',
        }

class UnnamedFileContentSerializer(MagicSerializer):

    class Meta:
        model = UnnamedFileContent

class FileContentSerializer(MagicSerializer):
    
    unnamed_file_content = UnnamedFileContentSerializer()

    class Meta:
        model = FileContent
        exclude = (_POLYMORPHIC_TYPE_FIELD,)
        nested_foreign_key_serializers = {'unnamed_file_content': 'analysis.serializers.data_objects.UnnamedFileContentSerializer'}

class FileLocationSerializer(MagicSerializer):

    unnamed_file_content = UnnamedFileContentSerializer()

    class Meta:
        model = FileLocation
        exclude = (_POLYMORPHIC_TYPE_FIELD,)
        nested_foreign_key_serializers = {'unnamed_file_content': 'analysis.serializers.data_objects.UnnamedFileContentSerializer'}

class _AbstractFileImportSerializer(MagicSerializer):
    
    temp_file_location = FileLocationSerializer(allow_null=True, required=False)
    file_location = FileLocationSerializer(allow_null=True, required=False)

    class Meta:
        nested_foreign_key_serializers = {
            'temp_file_location': 'analysis.serializers.data_objects.FileLocationSerializer',
            'file_location': 'analysis.serializers.data_objects.FileLocationSerializer'
        }

class FileImportSerializer(_AbstractFileImportSerializer):

    class Meta:
        model = FileImport
        exclude = (_POLYMORPHIC_TYPE_FIELD,)
        nested_foreign_key_serializers = _AbstractFileImportSerializer.Meta.nested_foreign_key_serializers

class AbstractFileImportSerializer(_AbstractFileImportSerializer):

    class Meta:
        model = AbstractFileImport
        exclude = (_POLYMORPHIC_TYPE_FIELD,)
        subclass_serializers = {'fileimport': 'analysis.serializers.data_objects.FileImportSerializer'}
        nested_foreign_key_serializers = _AbstractFileImportSerializer.Meta.nested_foreign_key_serializers

class FileDataObjectSerializer(MagicSerializer):

    file_content = FileContentSerializer(allow_null=True, required=False)
    file_import = AbstractFileImportSerializer(allow_null=True, required=False)

    class Meta:
        model = FileDataObject
        exclude = (_POLYMORPHIC_TYPE_FIELD,)
        nested_foreign_key_serializers = {
            'file_content': 'analysis.serializers.data_objects.FileContentSerializer',
            'file_import': 'analysis.serializers.data_objects.AbstractFileImportSerializer'
        }

class JSONDataContentSerializer(MagicSerializer):

    class Meta:
        model = UnnamedFileContent
        exclude = (_POLYMORPHIC_TYPE_FIELD,)

class JSONDataObjectSerializer(MagicSerializer):

    class Meta:
        model = JSONDataObject
        exclude = (_POLYMORPHIC_TYPE_FIELD,)
        nested_foreign_key_serializers = {
            'json_data_content': 'analysis.serializers.data_objects.JSONDataContentSerializer',
        }

class StringDataContentSerializer(MagicSerializer):

    class Meta:
        model = StringDataObject
        exclude = (_POLYMORPHIC_TYPE_FIELD,)

        
class StringDataObjectSerializer(MagicSerializer):

    class Meta:
        model = StringDataObject
        exclude = (_POLYMORPHIC_TYPE_FIELD,)
        nested_foreign_key_serializers = {
            'string_data_content': 'analysis.serializers.data_objects.StringDataContentSerializer',
        }

class BooleanDataContentSerializer(MagicSerializer):

    class Meta:
        model = BooleanDataObject
        exclude = (_POLYMORPHIC_TYPE_FIELD,)

        
class BooleanDataObjectSerializer(MagicSerializer):

    class Meta:
        model = BooleanDataObject
        exclude = (_POLYMORPHIC_TYPE_FIELD,)
        nested_foreign_key_serializers = {
            'boolean_data_content': 'analysis.serializers.data_objects.BooleanDataContentSerializer',
        }

class IntegerDataContentSerializer(MagicSerializer):

    class Meta:
        model = IntegerDataObject
        exclude = (_POLYMORPHIC_TYPE_FIELD,)
        
class IntegerDataObjectSerializer(MagicSerializer):

    class Meta:
        model = IntegerDataObject
        exclude = (_POLYMORPHIC_TYPE_FIELD,)
        nested_foreign_key_serializers = {
            'integer_data_content': IntegerDataContentSerializer,
        }

class DataObjectArraySerializer(MagicSerializer):

    class Meta:
        model = DataObjectArray
        nested_many_to_many_serializers = {
            'items': 'analysis.serializers.data_objects.DataObjectSerializer',
        }
