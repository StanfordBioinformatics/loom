import copy
from django.db import IntegrityError
from django.test import TestCase
from rest_framework import serializers

from api.serializers.data_objects import *
from . import fixtures


class TestStringDataObjectSerializer(TestCase):

    def testCreate(self):
        s = StringDataObjectSerializer(
            data=fixtures.data_objects.string_data_object)
        s.is_valid()
        m = s.save()

        self.assertEqual(
            m.value,
            fixtures.data_objects.string_data_object['value'])

    def testUpdate(self):
        s = StringDataObjectSerializer(
            data=fixtures.data_objects.string_data_object)
        s.is_valid()
        m = s.save()

        new_value = 'new value'
        s2 = StringDataObjectSerializer(m, data={'value': new_value}, partial=True)
        s2.is_valid()
        with self.assertRaises(UpdateNotAllowedError):
            m2 = s2.save()

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

    def testCreateArray(self):
        s = StringDataObjectSerializer(
            data=fixtures.data_objects.string_data_object_array)
        s.is_valid()
        m = s.save()

        self.assertEqual(
            m.array_members.count(),
            len(fixtures.data_objects.string_data_object_array['array_members'])
        )

class TestBooleanDataObjectSerializer(TestCase):

    def testCreate(self):
        s = BooleanDataObjectSerializer(
            data=fixtures.data_objects.boolean_data_object)
        s.is_valid()
        m = s.save()

        self.assertEqual(
            m.value,
            fixtures.data_objects.boolean_data_object['value'])


class TestIntegerDataObjectSerializer(TestCase):

    def testCreate(self):
        s = IntegerDataObjectSerializer(
            data=fixtures.data_objects.integer_data_object)
        s.is_valid()
        m = s.save()

        self.assertEqual(
            m.value,
            fixtures.data_objects.integer_data_object['value'])


class TestFloatDataObjectSerializer(TestCase):

    def testCreate(self):
        s = FloatDataObjectSerializer(
            data=fixtures.data_objects.float_data_object)
        s.is_valid()
        m = s.save()

        self.assertEqual(
            m.value,
            fixtures.data_objects.float_data_object['value'])

class TestDataObjectSerializer(TestCase):

    def testCreateStringDataObject(self):
        s = StringDataObjectSerializer(
            data=fixtures.data_objects.string_data_object)
        s.is_valid()
        m = s.save()

        self.assertEqual(
            m.value,
            fixtures.data_objects.string_data_object['value'])

    def testCreateArray(self):
        s = DataObjectSerializer(
            data=fixtures.data_objects.string_data_object_array)
        s.is_valid()
        m = s.save()

        self.assertEqual(
            m.array_members.count(),
            len(fixtures.data_objects.string_data_object_array['array_members'])
        )

    def testNegInvalidCreate(self):
        baddata={'bad': 'data'}
        s = DataObjectSerializer(data=baddata)
        with self.assertRaises(serializers.ValidationError):
            s.is_valid(raise_exception=True)

    def testGetDataFromModel(self):
        s1 = FileDataObjectSerializer(
            data=fixtures.data_objects.file_data_object)
        s1.is_valid(raise_exception=True)
        m = s1.save()

        s2 = DataObjectSerializer(m)
        d = s2.data
        self.assertEqual(
            d['md5'],
            fixtures.data_objects.file_data_object['md5'])

    def testGetDataFromData(self):
        s = FileDataObjectSerializer(data=fixtures.data_objects.file_data_object)
        s.is_valid()
        d = s.data
        self.assertEqual(
            d['md5'],
            fixtures.data_objects.file_data_object['md5'])

        
    
class TestFileResourceSerializer(TestCase):

    def testCreate(self):
        s = FileResourceSerializer(data=fixtures.data_objects.file_resource)
        s.is_valid()
        m = s.save()

        self.assertEqual(m.file_url,
                         fixtures.data_objects.file_resource['file_url'])


class TestFileDataObjectSerializer(TestCase):
    
    def testCreate(self):
        s = FileDataObjectSerializer(
            data=fixtures.data_objects.file_data_object)
        s.is_valid()
        m = s.save()

        self.assertEqual(
            m.filename,
            fixtures.data_objects.file_data_object['filename'])
