"""
from django.test import TestCase
from analyses.models import *
import queue_manager

class TestQueueManager(TestCase):

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
    session_run_obj = {
        'session_recipe': session_recipe_obj
    }

    def setUp(self):
        urlLocation = UrlLocation.create(self.url_location_obj)
        filePathLocation = FilePathLocation.create(self.file_path_location_obj)
        #location = Location.create(self.file_path_location_obj)
        #location = Location.create(self.url_location_obj)
        step = Step.create(self.step_obj)
        session = Session.create(self.session_obj)
        inputPort = InputPort.create(self.input_port_obj)
        myHash = Hash.create(self.hash_obj)
        myFile = File.create(self.file_obj)
        binding = InputBinding.create(self.input_binding_obj)
        sessionRecipe = SessionRecipe.create(self.session_recipe_obj)
        fileRecipe = FileRecipe.create(self.file_recipe_obj)
        request = Request.create(self.request_obj)

        # Run sessionRecipe by creating a SessionRun pointing to it.
        sessionRun = SessionRun.create(self.session_run_obj)
        self.runningSessionRecipe = sessionRecipe
    
    def testRetrieveRunningSessionRecipes(self):
        qm = queue_manager.QueueManager()
        running_session_recipes = qm.get_running_session_recipes()
        self.assertIn(self.runningSessionRecipe, running_session_recipes)
    
    def testRetrieveReadySessionRecipes(self):
        # TODO
        pass
"""
