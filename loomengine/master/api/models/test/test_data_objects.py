import os
from django.test import TestCase
from api.models.data_objects import *


class TestFileDataObject(TestCase):

    def setUp(self):
        self.filename = 'myfile.dat'
        self.filename_copy = 'myfile.dat_copy'
        self.filename2 = 'myfile2.dat'
        
        self.file = FileDataObject.objects.create(
            type='file',
            filename=self.filename,
            source_type='imported',
            note='Test data',
            source_url='file:///data/'+self.filename
        )
        self.file_copy = FileDataObject.objects.create(
            type='file',
            filename=self.filename_copy,
            source_type='imported',
            note='Test data',
            source_url='file:///data/'+self.filename
        )
        self.file2 = FileDataObject.objects.create(
            type='file',
            filename=self.filename2,
            source_type='imported',
            note='Test data',
            source_url='file:///data/'+self.filename2
        )

        self.hash = FileHash.objects.create(
            file_data_object=self.file,
            value='abcdefg',
            function='md5'
        )
        self.hash_copy = FileHash.objects.create(
            file_data_object=self.file_copy,
            value='abcdefg',
            function='md5'
        )
        self.hash_crc32 = FileHash.objects.create(
            file_data_object=self.file,
            value='1234567',
            function='crc32'
        )
        
        self.hash2 = FileHash.objects.create(
            file_data_object=self.file2,
            value='hijklmno',
            function='md5'
        )

        self.hash2_crc32 = FileHash.objects.create(
            file_data_object=self.file2,
            value='891011',
            function='crc32'
        )

    def testGetByValue_Name(self):
        matches = FileDataObject.filter_by_name_or_id_or_hash(self.filename)
        self.assertEqual(len(matches),1) 
        self.assertTrue(matches[0].filename, self.filename)

    def testGetByValue_ID(self):
        matches = FileDataObject.filter_by_name_or_id_or_hash(
            "@%s" % self.file.id.hex)
        self.assertEqual(len(matches),1) 
        self.assertTrue(matches[0].filename, self.filename)

    def testGetByValue_Hash(self):
        matches = FileDataObject.filter_by_name_or_id_or_hash(
            "$%s" % self.hash.value)
        self.assertEqual(len(matches),2) 
        self.assertTrue(matches[0].filename, self.filename)

    def testGetByValue_NameHash(self):
        matches = FileDataObject.filter_by_name_or_id_or_hash(
            "%s$%s" % (self.filename, self.hash.value))
        self.assertEqual(len(matches),1) 
        self.assertTrue(matches[0].filename, self.filename)

    def testGetByValue_NameId(self):
        matches = FileDataObject.filter_by_name_or_id_or_hash(
            "%s@%s" % (self.filename, self.file.id.hex))
        self.assertEqual(len(matches),1) 
        self.assertTrue(matches[0].filename, self.filename)

    def testGetByValue_HashId(self):
        matches = FileDataObject.filter_by_name_or_id_or_hash(
            "@%s$%s" % (self.file.id.hex, self.hash.value))
        self.assertEqual(len(matches),1) 
        self.assertTrue(matches[0].filename, self.filename)

    def testGetByValue_NameHashId(self):
        query = "%s$%s@%s" % (self.filename, self.hash.value, self.file.id.hex)
        matches = FileDataObject.filter_by_name_or_id_or_hash(
            "%s$%s@%s" % (self.filename, self.hash.value, self.file.id.hex))
        self.assertEqual(len(matches),1) 
        self.assertTrue(matches[0].filename, self.filename)

    def testSubstitutionValue(self):
        self.assertEqual(self.file.substitution_value,
                         self.filename)

    def testCreateLocationForImportKeepDuplicateTrue(self):
        with self.settings(
                KEEP_DUPLICATE_FILES=True):
            self.file.create_location_for_import()
            self.file_copy.create_location_for_import()

        # Files should have separate locations, even if contents match
        self.assertNotEqual(self.file.file_location.id,
                            self.file_copy.file_location.id)

    def testCreateLocationForImportKeepDuplicateFalseUploadIncomplete(self):
        with self.settings(
                KEEP_DUPLICATE_FILES=False):
            self.file.create_location_for_import()
            self.file_copy.create_location_for_import()

        # Files with matching content should not share a location
        # unless upload is complete
        self.assertNotEqual(self.file.file_location.id,
                            self.file_copy.file_location.id)

    def testCreateLocationForImportKeepDuplicateFalseUploadComplete(self):
        with self.settings(
                KEEP_DUPLICATE_FILES=False):
            self.file.create_location_for_import()
            self.file.file_location.upload_status = 'complete'
            self.file.file_location.save()
            self.file_copy.create_location_for_import()

        # Files with matching content should share a location
        # provided upload on first location was complete
        self.assertEqual(self.file.file_location.id,
                         self.file_copy.file_location.id)

    def testGetHash(self):
        with self.settings(
                HASH_FUNCTION='md5'):
            self.assertEqual(self.file.get_hash().value,
                             self.hash.value)
        with self.settings(
                HASH_FUNCTION='crc32'):
            self.assertEqual(self.file.get_hash().value,
                             self.hash_crc32.value)

    def testGetHashFileHashNotFoundError(self):
        with self.settings(
                HASH_FUNCTION='crc32'):
            with self.assertRaises(HashNotFoundError):
                self.file_copy.get_hash()
        
        
    def testAddUrlPrefixLocal(self):
        path = '/my/path'
        with self.settings(
                FILE_SERVER_TYPE='LOCAL'):
            url = FileLocation._add_url_prefix(path)
        self.assertEqual(url, 'file://'+path)

    def testAddUrlPrefixGoogleStorage(self):
        path = '/my/path'
        bucket_id = 'mybucket'
        with self.settings(
                FILE_SERVER_TYPE='GOOGLE_CLOUD',
                BUCKET_ID=bucket_id):
            url = FileLocation._add_url_prefix(path)
        self.assertEqual(url, 'gs://'+bucket_id+path)

    def testAddUrlPrefixRelativePathError(self):
        path = 'relative/path'
        with self.settings(
                FILE_SERVER_TYPE='LOCAL'):
            with self.assertRaises(RelativePathError):
                FileLocation._add_url_prefix(path)

    def testAddUrlPrefixInvalidServerTypeError(self):
        path = '/my/path'
        with self.settings(
                FILE_SERVER_TYPE='WRONG_VALUE'):
            with self.assertRaises(InvalidFileServerTypeError):
                FileLocation._add_url_prefix(path)

    def testGetBrowseablePathForImportedFile(self):
        self.assertEqual(
            FileLocation._get_browsable_path(self.file),
            'imported')

    def testGetFileRoot(self):
        file_root = '/mydata'
        with self.settings(
                FILE_ROOT=file_root):
            self.assertEqual(FileLocation._get_file_root(),
                             file_root)

    def testGetFileRootExpandUser(self):
        file_root = '~/mydata'
        with self.settings(
                FILE_ROOT=file_root,
                FILE_SERVER_TYPE='LOCAL'):
            self.assertEqual(FileLocation._get_file_root(),
                             os.path.expanduser(file_root))

    def testGetFileRootRelativeFileRootError(self):
        file_root = 'mydata'
        with self.settings(
                FILE_ROOT=file_root):
            with self.assertRaises(RelativeFileRootError):
                FileLocation._get_file_root()

    def testGetPathForImportDuplicatesAndReruns(self):
        file_root = '/mydata'
        with self.settings(
                KEEP_DUPLICATE_FILES=True,
                FORCE_RERUN=True,
                FILE_ROOT = file_root
        ):
            
            path = FileLocation._get_path_for_import(self.file)
            self.assertTrue(
                path.startswith(os.path.join(file_root, 'imported')))
            self.assertTrue(
                path.endswith('-%s-%s' % (self.file.id.hex,
                                          self.file.filename)))

    def testGetPathForImportDuplicatesNoReruns(self):
        file_root = '/mydata'
        with self.settings(
                KEEP_DUPLICATE_FILES=True,
                FORCE_RERUN=False,
                FILE_ROOT = file_root
        ):
            
            path = FileLocation._get_path_for_import(self.file)
            self.assertTrue(
                path.startswith(os.path.join(file_root, 'imported')))
            self.assertTrue(
                path.endswith('-%s-%s' % (self.file.id.hex,
                                          self.file.filename)))

    def testGetPathForImportNoDuplicates(self):
        file_root = '/mydata'
        with self.settings(
                KEEP_DUPLICATE_FILES=False,
                FILE_ROOT = file_root,
                HASH_FUNCTION = 'md5'
        ):
            path = FileLocation._get_path_for_import(self.file)
            self.assertEqual(
                path,
                os.path.join(file_root,
                             '%s-%s' % (self.hash.function,
                                        self.hash.value)))


class TestBooleanDataObject(TestCase):

    value = True
    
    def testGetByValue(self):
        data_object = DataObject.get_by_value(self.value, 'boolean')
        self.assertEqual(data_object.value, self.value)

    def testSubstitutionValue(self):
        boolean_data_object = BooleanDataObject.objects.create(
            type='boolean', value=self.value)
        data_object = DataObject.objects.get(id=boolean_data_object.id)
        self.assertEqual(data_object.substitution_value, self.value)


class TestFloatDataObject(TestCase):

    value = 9.1

    def testGetByValue(self):
        data_object = DataObject.get_by_value(self.value, 'float')
        self.assertEqual(data_object.value, self.value)

    def testSubstitutionValue(self):
        float_data_object = FloatDataObject.objects.create(
            type='float', value=self.value)
        data_object = DataObject.objects.get(id=float_data_object.id)
        self.assertEqual(data_object.substitution_value, self.value)


class TestIntegerDataObject(TestCase):

    value = 1000

    def testGetByValue(self):
        data_object = DataObject.get_by_value(self.value, 'integer')
        self.assertEqual(data_object.value, self.value)

    def testSubstitutionValue(self):
        integer_data_object = IntegerDataObject.objects.create(
            type='integer', value=self.value)
        data_object = DataObject.objects.get(id=integer_data_object.id)
        self.assertEqual(data_object.substitution_value, self.value)


class TestStringDataObject(TestCase):

    value = 'sprocket'

    def testGetByValue(self):
        data_object = DataObject.get_by_value(self.value, 'string')
        self.assertEqual(data_object.value, self.value)

    def testSubstitutionValue(self):
        string_data_object = StringDataObject.objects.create(
            type='string', value=self.value)
        data_object = DataObject.objects.get(id=string_data_object.id)
        self.assertEqual(data_object.substitution_value, self.value)


class TestArrayDataObject(TestCase):

    def testSubstitutionValue(self):
        values = [1,2,3]
        data_object_list = [
            DataObject.get_by_value(i, 'integer')
            for i in values
        ]
        data_object_array = DataObjectArray.create_from_list(
            data_object_list, 'integer')

        self.assertEqual(data_object_array.substitution_value, values)

    def testTypeMismatchError(self):
        data_object_list = [
            DataObject.get_by_value(3, 'integer'),
            DataObject.get_by_value(False, 'boolean')
        ]
        with self.assertRaises(TypeMismatchError):
            data_object_array = DataObjectArray.create_from_list(
                data_object_list, 'integer')

    def testNestedArraysError(self):
        list1 = [
            DataObject.get_by_value(3, 'integer'),
            DataObject.get_by_value(5, 'integer')
        ]
        array1 = DataObjectArray.create_from_list(
            list1, 'integer')

        list2=[
            DataObject.get_by_value(7, 'integer'),
            array1
        ]
        with self.assertRaises(NestedArraysError):
            array2 = DataObjectArray.create_from_list(
                list2, 'integer')
