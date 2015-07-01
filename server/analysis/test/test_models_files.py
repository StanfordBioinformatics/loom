from analysis.models import *
from .common import ImmutableModelsTestCase

class TestFiles(ImmutableModelsTestCase):

    file_obj = {
        'hash_value': '1234asfd',
        'hash_function': 'md5',
        }

    file_path_location_obj = {
        'file': file_obj,
        'file_path': '/absolute/path/to/my/file.txt',
        }

    def testFile(self):
        file = File.create(self.file_obj)
        self.assertEqual(file.hash_value, self.file_obj['hash_value'])
        self.roundTripJson(file)
        self.roundTripObj(file)

    def testFileLocation(self):
        # Keep all of these in one test. If the test framework runs them in
        # parallel they may SegFault with sqlite database.

        file_path_location = FilePathLocation.create(self.file_path_location_obj)
        self.assertEqual(file_path_location.file_path, self.file_path_location_obj['file_path'])

        self.roundTripJson(file_path_location)
        self.roundTripObj(file_path_location)

        file_location = FileLocation.create(self.file_path_location_obj)
        self.assertEqual(file_location.file_path, self.file_path_location_obj['file_path'])

        self.roundTripJson(file_location)
        self.roundTripObj(file_location)
