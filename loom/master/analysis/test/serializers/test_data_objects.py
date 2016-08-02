import copy
from django.db import IntegrityError
from django.test import TestCase
import json
from rest_framework import serializers

from analysis.serializers.data_objects import *
from analysis.serializers.exceptions import *
from analysis.test import fixtures


class TestStringContentSerializer(TestCase):

    def testCreate(self):
        s = StringContentSerializer(data=fixtures.data_objects.string_content)
        s.is_valid()
        m = s.save()

        self.assertEqual(m.string_value,
                         fixtures.data_objects.string_content['string_value'])

    def testNegCreateMissingData(self):
        s = StringContentSerializer(data={})
        self.assertFalse(s.is_valid())

    def testNegUpdate(self):
        # Create model
        s = StringContentSerializer(data=fixtures.data_objects.string_content)
        s.is_valid()
        m = s.save()

        # Update model
        new_value = 'xx'
        string_content = copy.deepcopy(fixtures.data_objects.string_content)
        string_content.update({'string_value': new_value})
        s = StringContentSerializer(m, data=string_content)
        s.is_valid()
        with self.assertRaises(UpdateNotAllowedError):
            m = s.save()

    def testNegInvalidCreate(self):
        baddata = {'bad': 'data'}
        s = StringContentSerializer(data=baddata)
        self.assertFalse(s.is_valid())

class TestStringDataObjectSerializer(TestCase):

    def testCreate(self):
        s = StringDataObjectSerializer(
            data=fixtures.data_objects.string_data_object)
        s.is_valid()
        m = s.save()

        self.assertEqual(
            m.string_content.string_value,
            fixtures.data_objects.string_data_object['string_content'][
                'string_value'])

    def testNegCreateWithNoContent(self):
        s = StringDataObjectSerializer(data={})
        self.assertFalse(s.is_valid())
        
    def testNegCreateWithDuplicateID(self):
        data = copy.deepcopy(fixtures.data_objects.string_data_object)
        
        s1 = StringDataObjectSerializer(data=data)
        s1.is_valid()
        m1 = s1.save()

        data.update({'id': m1.id})
        s2 = StringDataObjectSerializer(data=data)
        s2.is_valid()
        with self.assertRaises(IntegrityError):
            m2 = s2.save()
        
    def testNegUpdateChild(self):
        # Create model
        s = StringDataObjectSerializer(
            data=fixtures.data_objects.string_data_object)
        s.is_valid()
        m = s.save()

        # Update child model
        new_value = 'xx'
        string_data_object = copy.deepcopy(
            fixtures.data_objects.string_data_object)
        string_data_object['string_content'].update(
            {'string_value': new_value})
        s = StringDataObjectSerializer(m, data=string_data_object)
        s.is_valid()
        with self.assertRaises(UpdateNotAllowedError):
            m = s.save()

    def testNegInvalidChildCreate(self):
        badchilddata = {'string_content': {'bad': 'data'}}
        s = StringDataObjectSerializer(data=badchilddata)
        self.assertFalse(s.is_valid())


class TestBooleanContentSerializer(TestCase):
    
    def testCreate(self):
        s = BooleanContentSerializer(
            data=fixtures.data_objects.boolean_content)
        s.is_valid()
        m = s.save()

        self.assertEqual(
            m.boolean_value,
            fixtures.data_objects.boolean_content['boolean_value'])

class TestBooleanDataObjectSerializer(TestCase):
    
    def testCreate(self):
        s = BooleanDataObjectSerializer(
            data=fixtures.data_objects.boolean_data_object)
        s.is_valid()
        m = s.save()

        self.assertEqual(
            m.boolean_content.boolean_value,
            fixtures.data_objects.boolean_data_object['boolean_content'][
                'boolean_value'])

class TestIntegerContentSerializer(TestCase):

    def testCreate(self):
        s = IntegerContentSerializer(
            data=fixtures.data_objects.integer_content)
        s.is_valid()
        m = s.save()

        self.assertEqual(
            m.integer_value,
            fixtures.data_objects.integer_content['integer_value'])


class TestIntegerDataObjectSerializer(TestCase):

    def testCreate(self):
        s = IntegerDataObjectSerializer(
            data=fixtures.data_objects.integer_data_object)
        s.is_valid()
        m = s.save()

        self.assertEqual(
            m.integer_content.integer_value,
            fixtures.data_objects.integer_data_object['integer_content'][
                'integer_value'])

        
class TestUnnamedFileContentSerializer(TestCase):

    def testCreate(self):
        s = UnnamedFileContentSerializer(
            data=fixtures.data_objects.unnamed_file_content)
        s.is_valid()
        m = s.save()

        self.assertEqual(
            m.hash_value,
            fixtures.data_objects.unnamed_file_content['hash_value'])

    def testUpdate(self):
        s = UnnamedFileContentSerializer(
            data=fixtures.data_objects.unnamed_file_content)
        s.is_valid()
        m = s.save()

        data = copy.deepcopy(fixtures.data_objects.unnamed_file_content)
        data.update({'hash_value': 'xx'})
        s = UnnamedFileContentSerializer(m, data=data)
        s.is_valid()
        with self.assertRaises(UpdateNotAllowedError):
            m = s.save()


class TestFileContentSerializer(TestCase):

    def testCreate(self):
        s = FileContentSerializer(data=fixtures.data_objects.file_content)
        s.is_valid()
        m = s.save()

        self.assertEqual(m.filename,
                         fixtures.data_objects.file_content['filename'])

class TestFileLocationSerializer(TestCase):
    
    def testCreate(self):
        s = FileLocationSerializer(data=fixtures.data_objects.file_location)
        s.is_valid()
        m = s.save()

        self.assertEqual(m.url,
                         fixtures.data_objects.file_location['url'])

class TestFileImportSerializer(TestCase):

    def testNegCreate(self):
        s = FileImportSerializer(data=fixtures.data_objects.file_import)
        s.is_valid()
        with self.assertRaises(CreateNotAllowedError):
            model = s.save()

class TestFileDataObjectSerializer(TestCase):
    
    def testCreate(self):
        s = FileDataObjectSerializer(
            data=fixtures.data_objects.file_data_object)
        s.is_valid()
        m = s.save()

        self.assertEqual(
            m.file_content.filename,
            fixtures.data_objects.file_data_object['file_content']['filename'])

    def testCreateWithExistingLocation(self):
        data = copy.deepcopy(fixtures.data_objects.file_data_object)
        s1 = FileLocationSerializer(data=data['file_location'])
        s1.is_valid()
        loc = s1.save()

        # Update data with existing file location ID
        data['file_location'] = s1.data

        s2 = FileDataObjectSerializer(data=data)
        s2.is_valid()
        do = s2.save()

        # FileDataObject should use existing location, not create new
        self.assertEqual(FileLocation.objects.count(), 1)
        self.assertEqual(
            do.file_location.url,
            fixtures.data_objects.file_data_object['file_location']['url'])

    def testCreateWithLocationId(self):
        data = copy.deepcopy(fixtures.data_objects.file_data_object)
        new_id = uuid.uuid4().hex
        data['file_location'].update({'id': new_id})

        s = FileDataObjectSerializer(data=data)
        s.is_valid()
        do = s.save()

        # FileLocation should have been created
        self.assertEqual(FileLocation.objects.count(), 1)
        # and it should have the id that was assigned
        self.assertEqual(
            new_id,
            do.file_location.id.hex)

    def testUpdateWithExistingLocation(self):
        data = copy.deepcopy(fixtures.data_objects.file_data_object)
        s = FileDataObjectSerializer(data=data)
        s.is_valid()
        m = s.save()

        loc1_id = m.file_location.pk

        new_url = 'new:///ur/l'
        data['file_location']['url'] = new_url
        
        s = FileDataObjectSerializer(m, data=data)
        s.is_valid()
        m = s.save()

        loc2_id = m.file_location.pk

        self.assertEqual(m.file_location.url, new_url)
        self.assertNotEqual(loc1_id, loc2_id)

    def testUpdateWithNewLocation(self):
        s1 = FileDataObjectSerializer(
            data=fixtures.data_objects.file_data_object)
        s1.is_valid()
        m = s1.save()

        data = s1.data
        data['file_location'] = fixtures.data_objects.file_location_2

        s2 = FileDataObjectSerializer(m, data=data)
        s2.is_valid()
        m = s2.save()

        self.assertEqual(m.file_location.url,
                         fixtures.data_objects.file_location_2['url'])
        self.assertEqual(FileLocation.objects.count(), 2)

    def testNegUpdateLocationViaDataObject(self):
        s1 = FileDataObjectSerializer(
            data=fixtures.data_objects.file_data_object)
        s1.is_valid()
        m = s1.save()

        # Update should work if Location data is unchanged
        data = s1.data
        s2 = FileDataObjectSerializer(m, data=data)
        s2.is_valid()
        s2.save()

        # But if Location data changes we should see an error
        new_url = 'a:///new/url'
        data['file_location']['url'] = new_url

        s3 = FileDataObjectSerializer(m, data=data)
        s3.is_valid()
        with self.assertRaises(serializers.ValidationError):
            s3.save()

    def testNegUpdateContentViaDataObject(self):
        s1 = FileDataObjectSerializer(
            data=fixtures.data_objects.file_data_object)
        s1.is_valid()
        m = s1.save()

        data = s1.data

        new_filename = 're.name'
        data['file_content']['filename'] = new_filename

        s2 = FileDataObjectSerializer(m, data=data)
        s2.is_valid()
        with self.assertRaises(UpdateNotAllowedError):
            m = s2.save()


class TestDataObjectSerializer(TestCase):

    def testCreate(self):
        s = DataObjectSerializer(data=fixtures.data_objects.string_data_object)
        s.is_valid()
        m = s.save()

        self.assertEqual(
            m.string_content.string_value,
            fixtures.data_objects.string_data_object['string_content']['string_value'])

    def testNegUpdate(self):
        # Create model
        s = DataObjectSerializer(data=fixtures.data_objects.string_data_object)
        s.is_valid()
        m = s.save()

        # Update model
        new_value = 'xx'
        string_data_object = copy.deepcopy(
            fixtures.data_objects.string_data_object)
        string_data_object['string_content'].update(
            {'string_value': new_value})
        s = DataObjectSerializer(m, data=string_data_object)
        s.is_valid()
        with self.assertRaises(UpdateNotAllowedError):
            m = s.save()

    def testNegInvalidCreate(self):
        baddata={'bad': 'data'}
        s = DataObjectSerializer(data=baddata)
        s.is_valid()
        with self.assertRaises(serializers.ValidationError):
            s.save()

    def testGetDataFromModel(self):
        s1 = FileDataObjectSerializer(
            data=fixtures.data_objects.file_data_object)
        s1.is_valid()
        m = s1.save()

        s2 = DataObjectSerializer(m)
        d = s2.data
        self.assertEqual(
            d['file_content']['unnamed_file_content']['hash_value'],
            fixtures.data_objects.file_data_object['file_content']['unnamed_file_content']['hash_value'])

    def testGetDataFromData(self):
        s = DataObjectSerializer(data=fixtures.data_objects.file_data_object)
        s.is_valid()
        d = s.data
        self.assertEqual(
            d['file_content']['unnamed_file_content']['hash_value'],
            fixtures.data_objects.file_data_object['file_content']['unnamed_file_content']['hash_value'])


class TestDataObjectContentSerializer(TestCase):

    def testCreate(self):
        s = DataObjectContentSerializer(
            data=fixtures.data_objects.boolean_content)
        s.is_valid()
        m = s.save()

        self.assertEqual(
            m.boolean_value,
            fixtures.data_objects.boolean_content['boolean_value'])
