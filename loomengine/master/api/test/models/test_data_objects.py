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
            source_url='file:///data/'+self.filename,
            md5='abcde'
        )
        self.file_copy = FileDataObject.objects.create(
            type='file',
            filename=self.filename_copy,
            source_type='imported',
            note='Test data',
            source_url='file:///data/'+self.filename,
            md5='abcde'
        )
        self.file2 = FileDataObject.objects.create(
            type='file',
            filename=self.filename2,
            source_type='imported',
            note='Test data',
            source_url='file:///data/'+self.filename2,
            md5='fghij'
        )


    def testGetByValue(self):
        file = DataObject.get_by_value(self.filename, 'file')
        self.assertEqual(file.filename, self.filename)

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
            "$%s" % self.file.md5)
        self.assertEqual(len(matches),2) 
        self.assertTrue(matches[0].filename, self.filename)

    def testGetByValue_NameHash(self):
        matches = FileDataObject.filter_by_name_or_id_or_hash(
            "%s$%s" % (self.filename, self.file.md5))
        self.assertEqual(len(matches),1) 
        self.assertTrue(matches[0].filename, self.filename)

    def testGetByValue_NameId(self):
        matches = FileDataObject.filter_by_name_or_id_or_hash(
            "%s@%s" % (self.filename, self.file.id.hex))
        self.assertEqual(len(matches),1) 
        self.assertTrue(matches[0].filename, self.filename)

    def testGetByValue_HashId(self):
        matches = FileDataObject.filter_by_name_or_id_or_hash(
            "@%s$%s" % (self.file.id.hex, self.file.md5))
        self.assertEqual(len(matches),1) 
        self.assertTrue(matches[0].filename, self.filename)

    def testGetByValue_NameHashId(self):
        query = "%s$%s@%s" % (self.filename, self.file.md5, self.file.id.hex)
        matches = FileDataObject.filter_by_name_or_id_or_hash(
            "%s$%s@%s" % (self.filename, self.file.md5, self.file.id.hex))
        self.assertEqual(len(matches),1) 
        self.assertTrue(matches[0].filename, self.filename)

    def testSubstitutionValue(self):
        self.assertEqual(self.file.substitution_value,
                         self.filename)

    def testCreateIncompleteResourceForImportKeepDuplicateTrue(self):
        with self.settings(
                KEEP_DUPLICATE_FILES=True):
            self.file.create_incomplete_resource_for_import()
            self.file_copy.create_incomplete_resource_for_import()

        # Files should have separate resources, even if contents match
        self.assertNotEqual(self.file.file_resource.id,
                            self.file_copy.file_resource.id)

    def testCreateIncompleteResourceForImportKeepDuplicateFalseUploadIncomplete(self):
        with self.settings(
                KEEP_DUPLICATE_FILES=False):
            self.file.create_incomplete_resource_for_import()
            self.file_copy.create_incomplete_resource_for_import()

        # Files with matching content should not share a resource
        # unless upload is complete
        self.assertNotEqual(self.file.file_resource.id,
                            self.file_copy.file_resource.id)

    def testCreateIncompleteResourceForImportKeepDuplicateFalseUploadComplete(self):
        with self.settings(
                KEEP_DUPLICATE_FILES=False):
            self.file.create_incomplete_resource_for_import()
            self.file.file_resource.upload_status = 'complete'
            self.file.file_resource.save()
            self.file_copy.create_incomplete_resource_for_import()

        # Files with matching content should share a resource
        # provided upload on first resource was complete
        self.assertEqual(self.file.file_resource.id,
                         self.file_copy.file_resource.id)

    def testAddUrlPrefixLocal(self):
        path = '/my/path'
        with self.settings(
                FILE_SERVER_TYPE='LOCAL'):
            url = FileResource._add_url_prefix(path)
        self.assertEqual(url, 'file://'+path)

    def testAddUrlPrefixGoogleStorage(self):
        path = '/my/path'
        bucket_id = 'mybucket'
        with self.settings(
                FILE_SERVER_TYPE='GOOGLE_CLOUD',
                BUCKET_ID=bucket_id):
            url = FileResource._add_url_prefix(path)
        self.assertEqual(url, 'gs://'+bucket_id+path)

    def testAddUrlPrefixRelativePathError(self):
        path = 'relative/path'
        with self.settings(
                FILE_SERVER_TYPE='LOCAL'):
            with self.assertRaises(RelativePathError):
                FileResource._add_url_prefix(path)

    def testAddUrlPrefixInvalidServerTypeError(self):
        path = '/my/path'
        with self.settings(
                FILE_SERVER_TYPE='WRONG_VALUE'):
            with self.assertRaises(InvalidFileServerTypeError):
                FileResource._add_url_prefix(path)

    def testGetBrowseablePathForImportedFile(self):
        self.assertEqual(
            FileResource._get_browsable_path(self.file),
            'imported')

    def testGetFileRoot(self):
        file_root = '/mydata'
        with self.settings(
                FILE_ROOT=file_root):
            self.assertEqual(FileResource._get_file_root(),
                             file_root)

    def testGetFileRootExpandUser(self):
        file_root = '~/mydata'
        with self.settings(
                FILE_ROOT=file_root,
                FILE_SERVER_TYPE='LOCAL'):
            self.assertEqual(FileResource._get_file_root(),
                             os.path.expanduser(file_root))

    def testGetFileRootRelativeFileRootError(self):
        file_root = 'mydata'
        with self.settings(
                FILE_ROOT=file_root):
            with self.assertRaises(RelativeFileRootError):
                FileResource._get_file_root()

    def testGetPathForImportDuplicatesAndReruns(self):
        file_root = '/mydata'
        with self.settings(
                KEEP_DUPLICATE_FILES=True,
                FORCE_RERUN=True,
                FILE_ROOT = file_root
        ):
            
            path = FileResource._get_path_for_import(self.file)
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
            
            path = FileResource._get_path_for_import(self.file)
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
        ):
            path = FileResource._get_path_for_import(self.file)
            self.assertEqual(
                path,
                os.path.join(file_root,
                             self.file.md5))


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
