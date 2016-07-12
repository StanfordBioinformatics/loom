import copy
from rest_framework import serializers
from analysis.models.data_objects import *
from .base import MagicSerializer


class UnnamedFileContentSerializer(MagicSerializer):

    class Meta:
        model = UnnamedFileContent

class FileContentSerializer(MagicSerializer):
    
    unnamed_file_content = UnnamedFileContentSerializer()

    class Meta:
        model = FileContent
        exclude = ('polymorphic_ctype',)
        nested_serializers = {'unnamed_file_content': UnnamedFileContentSerializer}


class FileLocationSerializer(MagicSerializer):

    unnamed_file_content = UnnamedFileContentSerializer()

    class Meta:
        model = FileLocation
        nested_serializers = {'unnamed_file_content': UnnamedFileContentSerializer}

class FileImportSerializer(MagicSerializer):

    temp_file_location = FileLocationSerializer(allow_null=True, required=False)
    file_location = FileLocationSerializer(allow_null=True, required=False)

    class Meta:
        model = FileImport
        nested_serializers = {
            'temp_file_location': FileLocationSerializer,
            'file_location': FileLocationSerializer
        }

class AbstractFileImportSerializer(MagicSerializer):

    temp_file_location = FileLocationSerializer(allow_null=True, required=False)
    file_location = FileLocationSerializer(allow_null=True, required=False)

    class Meta:
        model = AbstractFileImport
        exclude = ('polymorphic_ctype',)
        nested_serializers = {
            'temp_file_location': FileLocationSerializer,
            'file_location': FileLocationSerializer
        }
        subclass_serializers = {'fileimport': FileImportSerializer}

class FileDataObjectSerializer(MagicSerializer):

    file_content = FileContentSerializer(allow_null=True, required=False)
    file_import = AbstractFileImportSerializer(allow_null=True, required=False)

    class Meta:
        model = FileDataObject
        exclude = ('polymorphic_ctype',)
        nested_serializers = {
            'file_content': FileContentSerializer,
            'file_import': AbstractFileImportSerializer
        }

