from django.test import TestCase
from apps.analyses.models import *

class TestModels(TestCase):
    step_obj = {'docker_image': "abcdefg123", 'command': "echo hello"}
    urlLocation_obj = {'url': "https://file.example.com"}
    filePathLocation_obj = {'file_path': "/data/my/file.dat"}
    session_obj = {
        'steps': [step_obj],
    }
    inputPort_obj = {
        'into_session': session_obj,
        'file_path': '/data/my/file.dat',
    }
    hash_obj = {
        'hash_function': 'sha-256',
        'hash_value': 'rstxy123',
    }
    file_obj = {
        'location': filePathLocation_obj,
        'hash': hash_obj,
    }
    inputBinding_obj = {
        'ingredient': file_obj,
        'input_port': inputPort_obj,
    }
    runRecipe_obj = {
        'sessions': [session_obj],
        'input_bindings': [inputBinding_obj]       
    }
    outputPort_obj = {
        'from_session': session_obj,
        'file_path': "/data/my/file.dat"
    }

    fileRecipe_obj = {
        'from_run_recipe': runRecipe_obj,
        'from_port': outputPort_obj
    }

    request_obj = {
        'file_recipes': [fileRecipe_obj],
        'requester': 'somebody@example.net',
    }

    def testUrlLocation(self):
        urlLocation = UrlLocation.create(self.urlLocation_obj)
        self.assertEqual(urlLocation.url, "https://file.example.com")

    def testFilePathLocation(self):
        filePathLocation = FilePathLocation.create(self.filePathLocation_obj)
        self.assertEqual(filePathLocation.file_path, "/data/my/file.dat")

    def testLocation(self):
        location = Location.create(self.filePathLocation_obj)
        self.assertEqual(location.file_path, "/data/my/file.dat")

        location = Location.create(self.urlLocation_obj)
        self.assertEqual(location.url, "https://file.example.com")

    def testStep(self):
        step = Step.create(self.step_obj)
        self.assertEqual(step.docker_image, "abcdefg123")

    def testSession(self):
        session = Session.create(self.session_obj)
        self.assertEqual(session.steps.first().docker_image, "abcdefg123")

    def testInputPort(self):
        inputPort = InputPort.create(self.inputPort_obj)
        self.assertEqual(inputPort.into_session.steps.first().docker_image, "abcdefg123")
 
    def testHash(self):
        hash = Hash.create(self.hash_obj)
        self.assertEqual(hash.hash_value, 'rstxy123')

    def testFile(self):
        file = File.create(self.file_obj)
        self.assertEqual(file.hash.hash_value, 'rstxy123')
       
    def testBinding(self):
        binding = InputBinding.create(self.inputBinding_obj)
        self.assertEqual(binding.ingredient.hash.hash_value, 'rstxy123')

    def testSessionRecipe(self):
        runRecipe = SessionRecipe.create(self.sessionRecipe_obj)
        self.assertEqual(sessionRecipe.sessions.first()._id, sessionRecipe.input_bindings.first().input_port.into_session._id)
    
    def testFileRecipe(self):
        fileRecipe = FileRecipe.create(self.fileRecipe_obj)
        self.assertEqual(fileRecipe.from_run_recipe.sessions.first().steps.first().docker_image, "abcdefg123")

    def testRequest(self):
        request = Request.create(self.request_obj)
        self.assertEqual(request.file_recipes.first().from_run_recipe.sessions.first().steps.first().docker_image, "abcdefg123")
    
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
