from django.test import TestCase
from apps.recipes.models import *

class TestModels(TestCase):
    urlLocation_json = '{"url":"https://file.example.com"}'
    filePathLocation_json = '{"file_path":"/data/my/file.dat"}'


    def testUrlLocation(self):
        urlLocation = UrlLocation.create(self.urlLocation_json)
        self.assertEqual(urlLocation.url, "https://file.example.com")

    def testFilePathLocation(self):
        filePathLocation = FilePathLocation.create(self.filePathLocation_json)
        self.assertEqual(filePathLocation.file_path, "/data/my/file.dat")

    def testLocation(self):
        location = Location.create(self.filePathLocation_json)
        self.assertEqual(location.file_path, "/data/my/file.dat")

        location = Location.create(self.urlLocation_json)
        self.assertEqual(location.url, "https://file.example.com")
    
    
    """
    File
    FileRecipe
    ImportRecipe
    BlobLocation
    UrlLocation
    FilePathLocation
    Binding
    ImportRequest
    ImportResult
    Import
    Port
    Request
    Run
    RunRecipe
    RunResult
    Session
    Step
    """
