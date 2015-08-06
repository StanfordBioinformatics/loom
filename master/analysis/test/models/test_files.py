import copy
from django.conf import settings
from django.test import TestCase
import os

from analysis.models import *
from analysis.test.fixtures import *

from .common import ImmutableModelsTestCase


class TestFile(ImmutableModelsTestCase):

    def testFile(self):
        file = File.create(file_obj)
        self.assertEqual(file.hash_value, file_obj['hash_value'])
        self.roundTripJson(file)
        self.roundTripObj(file)

    def testIsAvailable(self):
        file = File.create(file_obj)
        self.assertFalse(file.is_available())
        file_location = FileLocation.create(file_server_location_obj)
        self.assertTrue(file.is_available())

class TestFileLocation(ImmutableModelsTestCase):

    def testFileLocation(self):
        file_location = FileLocation.create(file_server_location_obj)
        self.assertEqual(file_location.file_path, file_server_location_obj['file_path'])
        self.roundTripJson(file_location)
        self.roundTripObj(file_location)

    def testGetByFile(self):
        file = File.create(file_server_location_obj['file'])
        file_location = FileLocation.create(file_server_location_obj)
        retrieved_file_location = FileLocation.get_by_file(file).first()
        self.assertEqual(file_location._id, retrieved_file_location._id)

    def testHasFile(self):
        file_location = FileLocation.create(file_server_location_obj)
        self.assertTrue(file_location.has_file())

    def testHasFileFalse(self):
        l_obj = copy.deepcopy(file_server_location_obj)
        l_obj.pop('file')
        file_location = FileLocation.create(l_obj)
        self.assertFalse(file_location.has_file())

class TestFileServerLocation(ImmutableModelsTestCase):

    def testFileServerLocation(self):
        file_server_location = FileServerLocation.create(file_server_location_obj)
        self.assertEqual(file_server_location.file_path, file_server_location_obj['file_path'])
        self.roundTripJson(file_server_location)
        self.roundTripObj(file_server_location)

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
        r_obj['file_location'].pop('file')
        file_import_request = FileImportRequest.create(r_obj)
        self.assertFalse(file_import_request.is_file_available())

    def testGetFile(self):
        file_import_request = FileImportRequest.create(file_import_request_obj)
        file = file_import_request.get_file()
        self.assertEqual(file.hash_value, file_import_request_obj['file_location']['file']['hash_value'])
                             
