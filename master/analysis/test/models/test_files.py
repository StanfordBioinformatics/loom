from django.conf import settings
from django.test import TestCase
import os

from analysis.models import *
from analysis.test.fixtures import *

from .common import ImmutableModelsTestCase


class TestFileModels(ImmutableModelsTestCase):

    def testFile(self):
        file = File.create(file_obj)
        self.assertEqual(file.hash_value, file_obj['hash_value'])
        self.roundTripJson(file)
        self.roundTripObj(file)

    def testFileLocation(self):
        # Keep all of these in one test. If the test framework runs them in
        # parallel they may SegFault with sqlite database.

        file_server_location = FileServerLocation.create(file_server_location_obj)
        self.assertEqual(file_server_location.file_path, file_server_location_obj['file_path'])

        self.roundTripJson(file_server_location)
        self.roundTripObj(file_server_location)

        file_location = FileLocation.create(file_server_location_obj)
        self.assertEqual(file_location.file_path, file_server_location_obj['file_path'])

        self.roundTripJson(file_location)
        self.roundTripObj(file_location)


class TestFile(TestCase):
    def testIsAvailable(self):
        file = File.create(file_obj)
        self.assertFalse(file.is_available())
        file_location = FileLocation.create(file_server_location_obj)
        self.assertTrue(file.is_available())
        
    
