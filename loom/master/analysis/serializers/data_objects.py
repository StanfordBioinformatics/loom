from analysis.models.data_objects import *
from .base import NestedPolymorphicModelSerializer, POLYMORPHIC_TYPE_FIELD


class DataObjectSerializer(NestedPolymorphicModelSerializer):

    class Meta:
        model = DataObject
        exclude = (POLYMORPHIC_TYPE_FIELD,)
        subclass_serializers = {
            'filedataobject': 'analysis.serializers.data_objects.FileDataObjectSerializer',
            'stringdataobject': 'analysis.serializers.data_objects.StringDataObjectSerializer',
            'integerdataobject': 'analysis.serializers.data_objects.IntegerDataObjectSerializer',
        }


class DataObjectContentSerializer(NestedPolymorphicModelSerializer):

    class Meta:
        model = DataObjectContent
        exclude = (POLYMORPHIC_TYPE_FIELD,)
        subclass_serializers = {
            'filecontent': 'analysis.serializers.data_objects.FileContentSerializer',
            'stringcontent': 'analysis.serializers.data_objects.StringContentSerializer',
            'integercontent': 'analysis.serializers.data_objects.IntegerContentSerializer',
        }


class UnnamedFileContentSerializer(NestedPolymorphicModelSerializer):

    class Meta:
        model = UnnamedFileContent


class FileContentSerializer(NestedPolymorphicModelSerializer):

    unnamed_file_content = UnnamedFileContentSerializer()

    class Meta:
        model = FileContent
        exclude = (POLYMORPHIC_TYPE_FIELD,)
        nested_x_to_one_serializers = {'unnamed_file_content': 'analysis.serializers.data_objects.UnnamedFileContentSerializer'}


class FileLocationSerializer(NestedPolymorphicModelSerializer):

    unnamed_file_content = UnnamedFileContentSerializer()

    class Meta:
        model = FileLocation
        nested_x_to_one_serializers = {'unnamed_file_content': 'analysis.serializers.data_objects.UnnamedFileContentSerializer'}


class AbstractFileImportSerializer(NestedPolymorphicModelSerializer):

    temp_file_location = FileLocationSerializer(allow_null=True, required=False)
    file_location = FileLocationSerializer(allow_null=True, required=False)

    class Meta:
        model = AbstractFileImport
        exclude = (POLYMORPHIC_TYPE_FIELD,)
        subclass_serializers = {'fileimport': 'analysis.serializers.data_objects.FileImportSerializer'}
        nested_x_to_one_serializers = {
            'temp_file_location': 'analysis.serializers.data_objects.FileLocationSerializer',
            'file_location': 'analysis.serializers.data_objects.FileLocationSerializer'
        }


class FileImportSerializer(AbstractFileImportSerializer):

    class Meta:
        model = FileImport
        exclude = (POLYMORPHIC_TYPE_FIELD,)
        nested_x_to_one_serializers = AbstractFileImportSerializer.Meta.nested_x_to_one_serializers


class FileDataObjectSerializer(NestedPolymorphicModelSerializer):

    file_content = FileContentSerializer(allow_null=True, required=False)
    file_import = AbstractFileImportSerializer(allow_null=True, required=False)

    class Meta:
        model = FileDataObject
        exclude = (POLYMORPHIC_TYPE_FIELD,)
        nested_x_to_one_serializers = {
            'file_content': 'analysis.serializers.data_objects.FileContentSerializer',
            'file_import': 'analysis.serializers.data_objects.AbstractFileImportSerializer'
        }


class StringContentSerializer(NestedPolymorphicModelSerializer):

    class Meta:
        model = StringContent
        exclude = (POLYMORPHIC_TYPE_FIELD,)

        
class StringDataObjectSerializer(NestedPolymorphicModelSerializer):

    string_content = StringContentSerializer()

    class Meta:
        model = StringDataObject
        exclude = (POLYMORPHIC_TYPE_FIELD,)
        nested_x_to_one_serializers = {
            'string_content': 'analysis.serializers.data_objects.StringContentSerializer',
        }


class BooleanContentSerializer(NestedPolymorphicModelSerializer):

    class Meta:
        model = BooleanContent
        exclude = (POLYMORPHIC_TYPE_FIELD,)

        
class BooleanDataObjectSerializer(NestedPolymorphicModelSerializer):

    boolean_content = BooleanContentSerializer()

    class Meta:
        model = BooleanDataObject
        exclude = (POLYMORPHIC_TYPE_FIELD,)
        nested_x_to_one_serializers = {
            'boolean_content': 'analysis.serializers.data_objects.BooleanContentSerializer',
        }


class IntegerContentSerializer(NestedPolymorphicModelSerializer):

    class Meta:
        model = IntegerContent
        exclude = (POLYMORPHIC_TYPE_FIELD,)
        

class IntegerDataObjectSerializer(NestedPolymorphicModelSerializer):

    integer_content = IntegerContentSerializer()

    class Meta:
        model = IntegerDataObject
        exclude = (POLYMORPHIC_TYPE_FIELD,)
        nested_x_to_one_serializers = {
            'integer_content': 'analysis.serializers.data_objects.IntegerContentSerializer',
        }

"""
class DataObjectArraySerializer(NestedPolymorphicModelSerializer):

    class Meta:
        model = DataObjectArray
        nested_x_to_many_serializers = {
            'items': 'analysis.serializers.data_objects.DataObjectSerializer',
        }
"""
