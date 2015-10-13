import copy
from django.conf import settings
from django.test import TestCase
import os
import sys

from analysis.models import *
sys.path.append(os.path.join(settings.BASE_DIR, '../../..'))
from xppf.common.fixtures import *

from .common import ImmutableModelsTestCase


class TestFile(ImmutableModelsTestCase):

    def testFile(self):
        file = File.create(file_obj)
        self.assertEqual(file.file_contents.hash_value, file_obj['file_contents']['hash_value'])
        self.roundTripJson(file)
        self.roundTripObj(file)

    def testIsAvailable(self):
        file = File.create(file_obj)
        self.assertFalse(file.is_available())
        file_storage_location = FileStorageLocation.create(server_file_storage_location_obj)
        self.assertTrue(file.is_available())

class TestFileArray(ImmutableModelsTestCase):

    def testFileArray(self):
        file_array = FileArray.create(file_array_obj)
        self.assertEqual(file_array.files.count(), len(file_array_obj['files']))
        self.roundTripJson(file_array)
        self.roundTripObj(file_array)

    def testIsAvailable(self):
        file1 = File.create(file_obj)
        file2 = File.create(file_obj_2)
        file_array = FileArray.create({'files': [file_obj, file_obj_2]})
        self.assertFalse(file_array.is_available())
        file_storage_location = FileStorageLocation.create(server_file_storage_location_obj)
        self.assertFalse(file_array.is_available())
        file_storage_location_2 = FileStorageLocation.create(server_file_storage_location_obj_2)
        self.assertTrue(file_array.is_available())

class TestFileStorageLocation(ImmutableModelsTestCase):

    def testFileStorageLocation(self):
        file_storage_location = FileStorageLocation.create(server_file_storage_location_obj)
        self.assertEqual(file_storage_location.file_path, server_file_storage_location_obj['file_path'])
        self.roundTripJson(file_storage_location)
        self.roundTripObj(file_storage_location)

    def testGetByFile(self):
        file_storage_location = FileStorageLocation.create(server_file_storage_location_obj)
        file = File.create(file_obj)
        retrieved_file_storage_location = FileStorageLocation.get_by_file(file).first()
        self.assertEqual(file_storage_location._id, retrieved_file_storage_location._id)

class TestServerFileStorageLocation(ImmutableModelsTestCase):

    def testServerFileStorageLocation(self):
        server_file_storage_location = ServerFileStorageLocation.create(server_file_storage_location_obj)
        self.assertEqual(server_file_storage_location.file_path, server_file_storage_location_obj['file_path'])
        self.roundTripJson(server_file_storage_location)
        self.roundTripObj(server_file_storage_location)

"""
class TestFileImportRequest(ImmutableModelsTestCase):

    def testFileImportRequest(self):
        file_import_request = FileImportRequest.create(file_import_request_obj)
        self.assertEqual(file_import_request.requester, file_import_request_obj.get('requester'))
        self.roundTripJson(file_import_request)
        self.roundTripObj(file_import_request)

    def testIsAvailable(self):
        file_import_request = FileImportRequest.create(file_import_request_obj)
        self.assertTrue(file_import_request.is_file_available())

    def testIsAvailableNeg(self):
        r_obj = copy.deepcopy(file_import_request_obj)
        r_obj['file_storage_location'].pop('file')
        file_import_request = FileImportRequest.create(r_obj)
        self.assertFalse(file_import_request.is_file_available())

    def testGetFile(self):
        file_import_request = FileImportRequest.create(file_import_request_obj)
        file = file_import_request.get_file()
        self.assertEqual(file.hash_value, file_import_request_obj['file_storage_location']['file']['hash_value'])
                             
"""
