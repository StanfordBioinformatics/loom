from analysis.models import *
import copy
from django.conf import settings
from django.test import TestCase
import os
import sys

from loom.common.fixtures import *
from .common import ImmutableModelsTestCase


class TestFile(ImmutableModelsTestCase):

    def testFile(self):
        file = File.create(file_struct)
        self.assertEqual(file.file_contents.hash_value, file_struct['file_contents']['hash_value'])
        self.roundTripJson(file)
        self.roundTripStruct(file)

    def testIsAvailable(self):
        file = File.create(file_struct)
        self.assertFalse(file.is_available())
        file_storage_location = FileStorageLocation.create(server_file_storage_location_struct)
        self.assertTrue(file.is_available())

class TestFileArray(ImmutableModelsTestCase):

    def testFileArray(self):
        file_array = FileArray.create(file_array_struct)
        self.assertEqual(file_array.files.count(), len(file_array_struct['files']))
        self.roundTripJson(file_array)
        self.roundTripStruct(file_array)

    def testFileArrayEmptyFiles(self):
        file_array = FileArray.create({'files': []})
        self.roundTripJson(file_array)
        self.roundTripStruct(file_array)

    def testIsAvailable(self):
        file1 = File.create(file_struct)
        file2 = File.create(file_struct_2)
        file_array = FileArray.create({'files': [file_struct, file_struct_2]})
        self.assertFalse(file_array.is_available())
        file_storage_location = FileStorageLocation.create(server_file_storage_location_struct)
        self.assertFalse(file_array.is_available())
        file_storage_location_2 = FileStorageLocation.create(server_file_storage_location_struct_2)
        self.assertTrue(file_array.is_available())

class TestFileStorageLocation(ImmutableModelsTestCase):

    def testFileStorageLocation(self):
        file_storage_location = FileStorageLocation.create(server_file_storage_location_struct)
        self.assertEqual(file_storage_location.file_path, server_file_storage_location_struct['file_path'])
        self.roundTripJson(file_storage_location)
        self.roundTripStruct(file_storage_location)

    def testGetByFile(self):
        file_storage_location = FileStorageLocation.create(server_file_storage_location_struct)
        file = File.create(file_struct)
        retrieved_file_storage_location = FileStorageLocation.get_by_file(file).first()
        self.assertEqual(file_storage_location._id, retrieved_file_storage_location._id)

class TestServerFileStorageLocation(ImmutableModelsTestCase):

    def testServerFileStorageLocation(self):
        server_file_storage_location = ServerFileStorageLocation.create(server_file_storage_location_struct)
        self.assertEqual(server_file_storage_location.file_path, server_file_storage_location_struct['file_path'])
        self.roundTripJson(server_file_storage_location)
        self.roundTripStruct(server_file_storage_location)
