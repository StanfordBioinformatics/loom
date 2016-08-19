from django.test import TestCase

from analysis.models import *
from . import fixtures

class TestDataObject(TestCase):

    def testCreate(self):
        file_data_object = FileDataObject(fixtures.data_objects.file)
        try:
            hash_value = file_data_object.file_content.unnamed_file_content.hash_value
        except AttributeError:
            hash_value = None
        self.assertEqual(hash_value,
                         fixtures.data_objects.file['file_content']['unnamed_file_content']['hash_value']
        )


"""
class TestFile(TestCase, ModelTestMixin):

    def testFile(self):
        file = FileDataObject.create(fixtures.file)
        self.assertEqual(file.file_content.unnamed_file_content.hash_value, fixtures.file['file_content']['unnamed_file_content']['hash_value'])
        self.roundTrip(file)


class TestFileLocation(TestCase, ModelTestMixin):

    def testFileStorageLocation(self):
        file_location = FileLocation.create(fixtures.file_location)
        self.assertEqual(file_location.url, fixtures.file_location['url'])
        self.roundTrip(file_location)


class TestFileImport(TestCase, ModelTestMixin):

    def testFileImportWithNestedDirectories(self):
        root_dir = 'root_dir'
        # These settings cause a nested directory structure where files are organized as
        # {ROOTDIR}/[{workflow}]/[{nested_workflow}/...]{step}/{task},{execution}, [work|logs]
        # {ROOTDIR}/'imported'
        with self.settings(
                FILE_SERVER_TYPE='LOCAL',
                FILE_ROOT=root_dir,
                FORCE_KEEP_DUPLICATES=True,
                FORCE_RERUN=True,
        ):
            # Temp location is automatically generated
            file_import = FileImport.create(fixtures.file_import)
            self.assertTrue(file_import.temp_file_location.url.startswith(os.path.join('file:///', root_dir)))
            self.assertIsNone(file_import.file_location)

            # Final location is automatically generated when FileDataObject is added
            file = deepcopy(fixtures.file)
            file.update({'file_import': file_import})
            FileDataObject.create(file)
            file_import.refresh_from_db()
            self.assertTrue(file_import.file_location.url.startswith(os.path.join('file:///', root_dir)))
            self.roundTrip(file_import)

    def testFileImportWithHashInFilename(self):
        root_dir = 'root_dir'
        # These settings cause a flat directory structure for all files (imports, results, and logs)
        # where files are named by hash
        with self.settings(
                FILE_SERVER_TYPE='LOCAL',
                FILE_ROOT=root_dir,
                FORCE_KEEP_DUPLICATES=False,
        ):
            # Temp location is automatically generated
            file_import = FileImport.create(fixtures.file_import)
            self.assertTrue(file_import.temp_file_location.url.startswith(os.path.join('file:///', root_dir)))
            self.assertIsNone(file_import.file_location)

            # Final location is automatically generated when FileDataObject is added
            file = deepcopy(fixtures.file)
            file.update({'file_import': file_import})
            FileDataObject.create(file)
            file_import.refresh_from_db()
            self.assertTrue(file_import.file_location.url.startswith(os.path.join('file:///', root_dir)))
            self.roundTrip(file_import)

    def testFileImportWithIdInFilename(self):
        # These settings cause a flat directory structure for all files (imports, results, and logs)
        # where files are named by {timestamp}-{file_data_object_id}-{filename}
        root_dir = 'root_dir'
        with self.settings(
                FILE_SERVER_TYPE='LOCAL',
                FILE_ROOT=root_dir,
                FORCE_KEEP_DUPLICATES=True,
                FORCE_RERUN=False,
        ):
            # Temp location is automatically generated
            file_import = FileImport.create(fixtures.file_import)
            self.assertTrue(file_import.temp_file_location.url.startswith(os.path.join('file:///', root_dir)))
            self.assertIsNone(file_import.file_location)

            # Final location is automatically generated when FileDataObject is added
            file = deepcopy(fixtures.file)
            file.update({'file_import': file_import})
            FileDataObject.create(file)
            file_import.refresh_from_db()
            self.assertTrue(file_import.file_location.url.startswith(os.path.join('file:///', root_dir)))
            self.roundTrip(file_import)


class TestDataObjects(TestCase, ModelTestMixin):

    def testIntegerDataObject(self):
        do = DataObject.create(fixtures.integer_data_object)
        self.assertEqual(do.integer_content.integer_value, fixtures.integer_data_object['integer_content']['integer_value'])
        self.roundTrip(do)

    def testBooleanDataObject(self):
        do = DataObject.create(fixtures.boolean_data_object)
        self.assertEqual(do.boolean_content.boolean_value, fixtures.boolean_data_object['boolean_content']['boolean_value'])
        self.roundTrip(do)

    def testStringDataObject(self):
        do = DataObject.create(fixtures.string_data_object)
        self.assertEqual(do.string_content.string_value, fixtures.string_data_object['string_content']['string_value'])
        self.roundTrip(do)

    def testJSONDataObject(self):
        do = DataObject.create(fixtures.json_data_object)
        self.assertEqual(do.json_content.json_value['data'], fixtures.json_data_object['json_content']['json_value']['data'])
        self.roundTrip(do)
"""
