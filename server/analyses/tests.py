from django.test import TestCase
from analyses.models import *

r'''{"file_recipes": [{"output_port": "output1", "session": {"input_bindings": [{"input_port": "input1", "data_object": {"output_port": "output1", "session": {"input_bindings": [{"input_port": "input1", "data_object": {"hash_function": "md5", "hash_value": "b1946ac92492d2347c6235b4d2611184"}}], "session_template": {"input_ports": [{"file_path": "hello.txt", "name": "input1"}], "steps": [{"environment": {"docker_image": "ubuntu"}, "command": "echo world > world.txt", "name": "hello"}, {"environment": {"docker_image": "ubuntu"}, "after": ["hello"], "command": "cat hello.txt world.txt > hello_world.txt"}], "output_ports": [{"name": "output1", "file_path": "hello_world.txt"}]}}}}], "session_template": {"input_ports": [{"name": "input1", "file_path": "partialresult.txt"}], "steps": [{"environment": {"docker_image": "ubuntu"}, "command": "echo \"`cat partialresult.txt`\"\\! > hello_worldfinal.txt"}], "output_ports": [{"name": "output1", "file_path": "hello_worldfinal.txt"}]}}}], "requester": "somebody@example.net"}'''


class TestModels(TestCase):

    file_obj = {
        'hash_value': '1234asfd',
        'hash_function': 'md5',
        }
    
    docker_image_obj = {
        'docker_image': '1234567asdf',
        }

    input_port_obj = {
        'file_path':'copy/my/file/here.txt',
        }

    output_port_obj = {
        'file_path':'look/for/my/file/here.txt',
        }

    input_binding_obj = {
        'data_object': file_obj,
        'input_port': input_port_obj,
        }

    step_template_obj = {
        'input_ports': [input_port_obj],
        'output_ports': [output_port_obj],
        'command': 'echo test',
        'environment': docker_image_obj,
        }

    step_obj = {
        'step_template': step_template_obj,
        'input_bindings': [input_binding_obj],
        }

    file_recipe_obj = {
        'step': step_obj,
        'output_port': output_port_obj,
        }

    resource_set_obj = {
        'step': step_obj,
        'memory_bytes': 1024**3,
        'cores': 2,
    }

    request_obj = {
        'file_recipes': [file_recipe_obj],
        'resource_sets': [resource_set_obj],
        'requester': 'someone@example.net',
        }

    azure_blob_location_obj = {
        'file': file_obj,
        'storage_account': 'my_account',
        'container': 'my_container',
        'blob': 'my_blob',
        }

    url_location_obj = {
        'file': file_obj,
        'url': 'https://example.com/myfile.txt',
        }

    file_path_location_obj = {
        'file': file_obj,
        'file_path': '/absolute/path/to/my/file.txt',
        }
    
    def testFile(self):
        file = File.create(self.file_obj)
        self.assertEqual(file.hash_value, self.file_obj['hash_value'])

    def testDockerImage(self):
        docker_image = DockerImage.create(self.docker_image_obj)
        self.assertEqual(docker_image.docker_image, self.docker_image_obj['docker_image'])

    def testInputPort(self):
        input_port = InputPort.create(self.input_port_obj)
        self.assertEqual(input_port.file_path, self.input_port_obj['file_path'])

    def testOutputPort(self):
        output_port = OutputPort.create(self.output_port_obj)
        self.assertEqual(output_port.file_path, self.output_port_obj['file_path'])

    def testInputBinding(self):
        input_binding = InputBinding.create(self.input_binding_obj)
        self.assertEqual(input_binding.input_port.file_path, self.input_binding_obj['input_port']['file_path'])

    def testEnvironment(self):
        environment = Environment.create(self.docker_image_obj)
        self.assertEqual(environment.docker_image, self.docker_image_obj['docker_image'])
        self.assertTrue(isinstance(environment, DockerImage))

    def testStepTemplate(self):
        step_template = StepTemplate.create(self.step_template_obj)
        self.assertEqual(step_template.command, self.step_template_obj['command'])
        
    def testStep(self):
        step = Step.create(self.step_obj)
        self.assertEqual(step.step_template.command, self.step_obj['step_template']['command'])

    def testFileRecipe(self):
        file_recipe = FileRecipe.create(self.file_recipe_obj)
        self.assertEqual(file_recipe.output_port.file_path, self.file_recipe_obj['output_port']['file_path'])

    def testDataObjectAsFileRecipe(self):
        data_object = DataObject.create(self.file_recipe_obj)
        self.assertEqual(data_object.output_port.file_path, self.file_recipe_obj['output_port']['file_path'])
        self.assertTrue(isinstance(data_object, FileRecipe))
        
    def testDataObjectAsFile(self):
        data_object = DataObject.create(self.file_obj)
        self.assertEqual(data_object.hash_value, self.file_obj['hash_value'])
        self.assertTrue(isinstance(data_object, File))

    def testResourceSet(self):
        resource_set = ResourceSet.create(self.resource_set_obj)
        self.assertEqual(resource_set.cores, self.resource_set_obj['cores'])

    def testRequest(self):
        request = Request.create(self.request_obj)
        self.assertEqual(request.resource_sets.first().cores, self.request_obj['resource_sets'][0]['cores'])

    def testFileLocation(self):
        # Keep all of these in one test. If the test framework runs them in
        # parallel they may SegFault with sqlite database.

        azure_blob_location = AzureBlobLocation.create(self.azure_blob_location_obj)
        self.assertEqual(azure_blob_location.container, self.azure_blob_location_obj['container'])

        url_location = UrlLocation.create(self.url_location_obj)
        self.assertEqual(url_location.url, self.url_location_obj['url'])

        file_path_location = FilePathLocation.create(self.file_path_location_obj)
        self.assertEqual(file_path_location.file_path, self.file_path_location_obj['file_path'])

        file_location = FileLocation.create(self.azure_blob_location_obj)
        self.assertEqual(file_location.container, self.azure_blob_location_obj['container'])


"""
    def testHelloWorld(self):
        hello_world_request_obj = r'''{"file_recipes": [{"output_port": "output1", "session": {"input_bindings": [{"input_port": "input1", "data_object": {"output_port": "output1", "session": {"input_bindings": [{"input_port": "input1", "data_object": {"hash_function": "md5", "hash_value": "b1946ac92492d2347c6235b4d2611184"}}], "session_template": {"input_ports": [{"file_path": "hello.txt", "name": "input1"}], "steps": [{"environment": {"docker_image": "ubuntu"}, "command": "echo world > world.txt", "name": "hello"}, {"environment": {"docker_image": "ubuntu"}, "after": ["hello"], "command": "cat hello.txt world.txt > hello_world.txt"}], "output_ports": [{"name": "output1", "file_path": "hello_world.txt"}]}}}}], "session_template": {"input_ports": [{"name": "input1", "file_path": "partialresult.txt"}], "steps": [{"environment": {"docker_image": "ubuntu"}, "command": "echo \"`cat partialresult.txt`\"\\! > hello_worldfinal.txt"}], "output_ports": [{"name": "output1", "file_path": "hello_worldfinal.txt"}]}}}], "requester": "somebody@example.net"}'''

        request = Request.create(hello_world_request_obj)
        self.assertEqual(request.file_recipes.first().session.session_template.steps.first().docker_image, "abcdefg123")
"""
