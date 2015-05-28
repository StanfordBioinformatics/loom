from django.test import TestCase
from analyses.models import *

class TestModels(TestCase):
    step_obj = {'docker_image': "abcdefg123", 'command': "echo hello"}
    url_location_obj = {'url': "https://file.example.com"}
    file_path_location_obj = {'file_path': "/data/my/file.dat"}
    session_obj = {
        'steps': [step_obj],
    }
    input_port_obj = {
        'session': session_obj,
        'file_path': '/data/my/file.dat',
    }
    hash_obj = {
        'hash_function': 'sha-256',
        'hash_value': 'rstxy123',
    }
    file_obj = {
        'location': file_path_location_obj,
        'hash': hash_obj,
    }
    input_binding_obj = {
        'ingredient': file_obj,
        'input_port': input_port_obj,
    }
    session_recipe_obj = {
        'sessions': [session_obj],
        'input_bindings': [input_binding_obj]       
    }
    output_port_obj = {
        'session': session_obj,
        'file_path': "/data/my/file.dat"
    }

    file_recipe_obj = {
        'session_recipe': session_recipe_obj,
        'port': output_port_obj
    }

    request_obj = {
        'file_recipes': [file_recipe_obj],
        'requester': 'somebody@example.net',
    }

    def testUrlLocation(self):
        urlLocation = UrlLocation.create(self.url_location_obj)
        self.assertEqual(urlLocation.url, "https://file.example.com")

    def testFilePathLocation(self):
        filePathLocation = FilePathLocation.create(self.file_path_location_obj)
        self.assertEqual(filePathLocation.file_path, "/data/my/file.dat")

    def testLocation(self):
        location = Location.create(self.file_path_location_obj)
        self.assertEqual(location.file_path, "/data/my/file.dat")

        location = Location.create(self.url_location_obj)
        self.assertEqual(location.url, "https://file.example.com")

    def testStep(self):
        step = Step.create(self.step_obj)
        self.assertEqual(step.docker_image, "abcdefg123")

    def testSession(self):
        session = Session.create(self.session_obj)
        self.assertEqual(session.steps.first().docker_image, "abcdefg123")

    def testInputPort(self):
        inputPort = InputPort.create(self.input_port_obj)
        self.assertEqual(inputPort.session.steps.first().docker_image, "abcdefg123")
 
    def testHash(self):
        hash = Hash.create(self.hash_obj)
        self.assertEqual(hash.hash_value, 'rstxy123')

    def testFile(self):
        file = File.create(self.file_obj)
        self.assertEqual(file.hash.hash_value, 'rstxy123')
       
    def testBinding(self):
        binding = InputBinding.create(self.input_binding_obj)
        self.assertEqual(binding.ingredient.hash.hash_value, 'rstxy123')

    def testSessionRecipe(self):
        sessionRecipe = SessionRecipe.create(self.session_recipe_obj)
        self.assertEqual(sessionRecipe.sessions.first()._id, sessionRecipe.input_bindings.first().input_port.session._id)
    
    def testFileRecipe(self):
        fileRecipe = FileRecipe.create(self.file_recipe_obj)
        self.assertEqual(fileRecipe.session_recipe.sessions.first().steps.first().docker_image, "abcdefg123")

    def testRequest(self):
        request = Request.create(self.request_obj)
        self.assertEqual(request.file_recipes.first().session_recipe.sessions.first().steps.first().docker_image, "abcdefg123")
    
