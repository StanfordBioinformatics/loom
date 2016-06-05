from django.test import TestCase
import uuid

from analysis.models import *
from . import fixtures
from .common import UniversalModelTestMixin


class TestFile(TestCase, UniversalModelTestMixin):

    def testFile(self):
        file = FileDataObject.create(fixtures.file)
        self.assertEqual(file.file_content.unnamed_file_content.hash_value, fixtures.file['file_content']['unnamed_file_content']['hash_value'])
        self.roundTripJson(file)
        self.roundTripStruct(file)

class TestFileLocation(TestCase, UniversalModelTestMixin):

    def testFileStorageLocation(self):
        file_location = FileLocation.create(fixtures.file_location)
        self.assertEqual(file_location.url, fixtures.file_location['url'])
        self.roundTripJson(file_location)
        self.roundTripStruct(file_location)

    def testGetByFile(self):
        file_location = FileLocation.create(fixtures.file_location)
        file = FileDataObject.create(fixtures.file)
        retrieved_file_location = FileLocation.get_by_file(file).first()
        self.assertEqual(uuid.UUID(str(file_location._id)), uuid.UUID(str(retrieved_file_location._id)))


class TestFileImport(TestCase, UniversalModelTestMixin):

    def testFileImport(self):
        root_dir = 'root_dir'
        import_dir = 'import_dir'
        with self.settings(
                FILE_SERVER_TYPE='LOCAL',
                FILE_ROOT=root_dir,
                IMPORT_DIR=import_dir
        ):
            # Temp location is automatically generated
            file_import = FileImport.create(fixtures.file_import)
            self.assertTrue(file_import.temp_file_location.url.startswith(os.path.join('file:///', root_dir, import_dir)))
            self.assertIsNone(file_import.file_location)

            # Final location is automatically generated when FileDataObject is added
            file_import.update({'file_data_object': fixtures.file})
            self.assertTrue(file_import.file_location.url.startswith(os.path.join('file:///', root_dir, import_dir)))
            
            self.roundTripJson(file_import)
            self.roundTripStruct(file_import)

class TestDataObjects(TestCase, UniversalModelTestMixin):

    def testIntegerDataObject(self):
        do = DataObject.create(fixtures.integer_data_object)
        self.assertEqual(do.integer_content.integer_value, fixtures.integer_data_object['integer_content']['integer_value'])
        self.roundTripJson(do)
        self.roundTripStruct(do)

    def testBooleanDataObject(self):
        do = DataObject.create(fixtures.boolean_data_object)
        self.assertEqual(do.boolean_content.boolean_value, fixtures.boolean_data_object['boolean_content']['boolean_value'])
        self.roundTripJson(do)
        self.roundTripStruct(do)

    def testStringDataObject(self):
        do = DataObject.create(fixtures.string_data_object)
        self.assertEqual(do.string_content.string_value, fixtures.string_data_object['string_content']['string_value'])
        self.roundTripJson(do)
        self.roundTripStruct(do)

    def testJSONDataObject(self):
        do = DataObject.create(fixtures.json_data_object)
        self.assertEqual(do.json_content.json_value['data'], fixtures.json_data_object['json_content']['json_value']['data'])
        self.roundTripJson(do)
        self.roundTripStruct(do)
