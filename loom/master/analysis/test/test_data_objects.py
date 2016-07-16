from django.test import TestCase
import json

from analysis.serializers.data_objects import *
from . import fixtures

class TestDataObjectSerializers(TestCase):
        
    def testDataObjectSerializer(self):
        s = DataObjectSerializer(data=fixtures.data_objects.file_data_object)
        s.is_valid()
        m = s.save()

        self.assertEqual(m.file_content.filename,
                         fixtures.data_objects.file_data_object['file_content']['filename'])

    def testDataObjectContentSerializer(self):
        s = DataObjectContentSerializer(data=fixtures.data_objects.file_content)
        s.is_valid()
        m = s.save()

        self.assertEqual(m.filename,
                         fixtures.data_objects.file_content['filename'])

    def testUnnamedFileContentSerializer(self):
        s = UnnamedFileContentSerializer(data=fixtures.data_objects.unnamed_file_content)
        s.is_valid()
        m = s.save()

        self.assertEqual(m.hash_value,
                         fixtures.data_objects.unnamed_file_content['hash_value'])

    def testFileContentSerializer(self):
        s = FileContentSerializer(data=fixtures.data_objects.file_content)
        s.is_valid()
        m = s.save()

        self.assertEqual(m.filename,
                         fixtures.data_objects.file_content['filename'])

    def testFileLocationSerializer(self):
        s = FileLocationSerializer(data=fixtures.data_objects.file_location)
        s.is_valid()
        m = s.save()

        self.assertEqual(m.url,
                         fixtures.data_objects.file_location['url'])

    def testAbstractFileImportSerializer(self):
        s = AbstractFileImportSerializer(data=fixtures.data_objects.file_import)
        s.is_valid()
        m = s.save()

        self.assertEqual(m.source_url,
                         fixtures.data_objects.file_import['source_url'])

    def FileImportSerializer(self):
        s = FileImportSerializer(data=fixtures.data_objects.file_import)
        s.is_valid()
        m = s.save()

        self.assertEqual(m.source_url,
                         fixtures.data_objects.file_import['source_url'])

    def testFileDataObjectSerializer(self):
        s = FileDataObjectSerializer(data=fixtures.data_objects.file_data_object)
        s.is_valid()
        m = s.save()

        self.assertEqual(m.file_content.filename,
                         fixtures.data_objects.file_data_object['file_content']['filename'])

    def testStringContentSerializer(self):
        s = StringContentSerializer(data=fixtures.data_objects.string_content)
        s.is_valid()
        m = s.save()

        self.assertEqual(m.string_value,
                         fixtures.data_objects.string_content['string_value'])

    def testStringDataObjectSerializer(self):
        s = StringDataObjectSerializer(data=fixtures.data_objects.string_data_object)
        s.is_valid()
        m = s.save()

        self.assertEqual(m.string_content.string_value,
                         fixtures.data_objects.string_data_object['string_content']['string_value'])

    def testBooleanContentSerializer(self):
        s = BooleanContentSerializer(data=fixtures.data_objects.boolean_content)
        s.is_valid()
        m = s.save()

        self.assertEqual(m.boolean_value,
                         fixtures.data_objects.boolean_content['boolean_value'])

    def testBooleanDataObjectSerializer(self):
        s = BooleanDataObjectSerializer(data=fixtures.data_objects.boolean_data_object)
        s.is_valid()
        m = s.save()

        self.assertEqual(m.boolean_content.boolean_value,
                         fixtures.data_objects.boolean_data_object['boolean_content']['boolean_value'])

    def testIntegerContentSerializer(self):
        s = IntegerContentSerializer(data=fixtures.data_objects.integer_content)
        s.is_valid()
        m = s.save()

        self.assertEqual(m.integer_value,
                         fixtures.data_objects.integer_content['integer_value'])

    def testIntegerDataObjectSerializer(self):
        s = IntegerDataObjectSerializer(data=fixtures.data_objects.integer_data_object)
        s.is_valid()
        m = s.save()

        self.assertEqual(m.integer_content.integer_value,
                         fixtures.data_objects.integer_data_object['integer_content']['integer_value'])

    """
    def testDataObjectArraySerializer(self):
        pass
    """
