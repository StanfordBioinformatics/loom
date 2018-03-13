import os
from django.test import TestCase
from django.core.exceptions import ValidationError

from api.models.data_objects import DataObject, FileResource
from api.models import calculate_contents_fingerprint


md5_1 = 'd8e8fca2dc0f896fd7cb4cb0031ba249'
filename_1 = 'mydata.txt'


class TestDataObject(TestCase):

    VALUE_SETS = [
        # (type, valid_value)
        ('boolean', True),
        ('float', 3.7),
        ('integer', 3),
        ('string', ':D'),
    ]

    INVALID_VALUE_SETS = [
        # (type, invalid_value)
        ('float', 'word'),
        ('integer', 'three'),
    ]

    def testGetByValue(self):
        for (type, value) in self.VALUE_SETS:
            do = DataObject.get_by_value(value, type)
            self.assertEqual(do.value, value)

    def testSubstitutionValue(self):
        for (type, value) in self.VALUE_SETS:
            do = DataObject.get_by_value(value, type)
            self.assertEqual(do.substitution_value, str(value))

    def testIsReady(self):
        for (type, value) in self.VALUE_SETS:
            do = DataObject.get_by_value(value, type)
            self.assertTrue(do.is_ready)

    def testGetByValue_invalidValue(self):
        for (type, invalid_value) in self.INVALID_VALUE_SETS:
            with self.assertRaises(ValidationError):
                if invalid_value is not None:
                    DataObject.get_by_value(invalid_value, type)

    def testGetByValue_invalidType(self):
        with self.assertRaises(ValidationError):
            DataObject.get_by_value('cantelope', 'fruit')

    def testCreateAndInitializeFileResource_import(self):
        imported_from_url = 'file:///data/'+filename_1
        comments = 'Test data'
        do = DataObject.create_and_initialize_file_resource(
            filename=filename_1, md5=md5_1, source_type='result',
            imported_from_url=imported_from_url,
            import_comments=comments)
        self.assertEqual(do.file_resource.md5, md5_1)
        self.assertEqual(do.file_resource.upload_status, 'incomplete')
        self.assertTrue('work' in do.file_resource.file_url)
        self.assertEqual(do.file_resource.import_comments, comments)
        self.assertEqual(
            do.file_resource.imported_from_url, imported_from_url)

    def testValue_file(self):
        do = DataObject.create_and_initialize_file_resource(
            filename=filename_1, md5=md5_1, source_type='result')
        self.assertEqual(do.value, do.file_resource)

    def testSubstitutionValue_file(self):
        do = DataObject.create_and_initialize_file_resource(
            filename=filename_1, md5=md5_1, source_type='result')
        self.assertEqual(do.substitution_value, filename_1)

    def testGetByValue_file(self):
        do = DataObject.create_and_initialize_file_resource(
            filename=filename_1, md5=md5_1, source_type='result')
        file_identifiers = [
            filename_1,
            '$%s' % md5_1,
            '@%s' % do.uuid,
            '%s@%s' % (filename_1, do.uuid),
            '%s$%s' % (filename_1, md5_1),
            '%s$%s@%s' % (filename_1, md5_1, do.uuid),
            '$%s@%s' % (md5_1, do.uuid),
        ]
        for identifier in file_identifiers:
            retrieved_do = DataObject.get_by_value(identifier, 'file')
            self.assertEqual(do.uuid, retrieved_do.uuid)

    def testGetByValue_noMatch(self):
        with self.assertRaises(ValidationError):
            DataObject.get_by_value('noMatch', 'file')

    def testGetByValue_twoMatches(self):
        do = DataObject.create_and_initialize_file_resource(
            filename=filename_1, md5=md5_1, source_type='result')
        retrieved_do = DataObject.get_by_value(filename_1, 'file')
        self.assertEqual(do.uuid, retrieved_do.uuid)
        DataObject.create_and_initialize_file_resource(
            filename=filename_1, md5=md5_1, source_type='result')
        with self.assertRaises(ValidationError):
            DataObject.get_by_value(filename_1, 'file')

    def testCalculateContentsFingerprint_integer(self):
        contents = {'type': 'integer',
                    'value':17}
        do = DataObject.get_by_value(contents['value'], contents['type'])
        self.assertEqual(
            do.calculate_contents_fingerprint(),
            calculate_contents_fingerprint(contents))

    def testCalculateContentsFingerprint_file(self):
        contents = {
            'type': 'file',
            'value': {
                'md5': md5_1,
                'filename': filename_1
            }
        }
        do = DataObject.create_and_initialize_file_resource(
            filename=contents['value']['filename'],
            md5=contents['value']['md5'],
            source_type='result')
        self.assertEqual(do.calculate_contents_fingerprint(),
                         calculate_contents_fingerprint(contents))


class TestFileResource(TestCase):

    def testInitialize(self):
        data_object = DataObject.objects.create(type='file')
        resource = FileResource.initialize(
            data_object=data_object, filename=filename_1,
            md5=md5_1, source_type='result')
        self.assertEqual(resource.md5, md5_1)
        self.assertEqual(resource.filename, filename_1)
        self.assertEqual(resource.data_object.uuid, data_object.uuid)
        self.assertTrue('work' in resource.file_url)
        self.assertEqual(resource.upload_status, 'incomplete')
        self.assertEqual(resource.source_type, 'result')

    def testIsReady(self):
        data_object = DataObject.objects.create(type='file')
        resource = FileResource.initialize(
            data_object=data_object, filename=filename_1,
            md5=md5_1, source_type='result')
        self.assertFalse(data_object.is_ready)
        self.assertFalse(resource.is_ready)
        resource.upload_status='complete'
        self.assertTrue(data_object.is_ready)
        self.assertTrue(resource.is_ready)

    def testGetUuid(self):
        data_object = DataObject.objects.create(type='file')
        resource = FileResource.initialize(
            data_object=data_object, filename=filename_1,
            md5=md5_1, source_type='result')
        self.assertEqual(resource.get_uuid(), data_object.uuid)
