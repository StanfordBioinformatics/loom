from django.test import TestCase
from analyses.models import *


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

    analysis_request_obj = {
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

    step_run_obj = {
        'step': step_obj,
        # Exclude step_run_record, to be added on update
        }

    step_run_record_obj = {
        'step': step_obj,
        'file': file_obj,
        }

    analysis_run_obj = {
        'analysis_request': analysis_request_obj,
        # Exclude analysis_run_record, to be added on update
        }

    analysis_run_record_obj = {
        'analysis_request': analysis_request_obj,
        'step_run_records': [step_run_record_obj],
        }

    file_import_record_obj = {
        'import_comments': 'Notes about the source of this file...',
        'file': file_obj,
        }

    file_import_run_obj = {
        'import_comments': 'Notes about the source of this file...',
        'destination': file_path_location_obj,
        # Exclude file_import_record, to be added on update
        }
    
    def testFile(self):
        file = File.create(self.file_obj)
        self.assertEqual(file.hash_value, self.file_obj['hash_value'])

        self.roundTripJson(file)
        self.roundTripObj(file)

    def testDockerImage(self):
        docker_image = DockerImage.create(self.docker_image_obj)
        self.assertEqual(docker_image.docker_image, self.docker_image_obj['docker_image'])

        self.roundTripJson(docker_image)
        self.roundTripObj(docker_image)

    def testEnvironment(self):
        environment = Environment.create(self.docker_image_obj)
        self.assertEqual(environment.docker_image, self.docker_image_obj['docker_image'])
        self.assertTrue(isinstance(environment, DockerImage))

        self.roundTripJson(environment)
        self.roundTripObj(environment)

    def testInputPort(self):
        input_port = InputPort.create(self.input_port_obj)
        self.assertEqual(input_port.file_path, self.input_port_obj['file_path'])

        self.roundTripJson(input_port)
        self.roundTripObj(input_port)

    def testOutputPort(self):
        output_port = OutputPort.create(self.output_port_obj)
        self.assertEqual(output_port.file_path, self.output_port_obj['file_path'])

        self.roundTripJson(output_port)
        self.roundTripObj(output_port)

    def testInputBinding(self):
        input_binding = InputBinding.create(self.input_binding_obj)
        self.assertEqual(input_binding.input_port.file_path, self.input_binding_obj['input_port']['file_path'])

        self.roundTripJson(input_binding)
        self.roundTripObj(input_binding)

    def testStepTemplate(self):
        step_template = StepTemplate.create(self.step_template_obj)
        self.assertEqual(step_template.command, self.step_template_obj['command'])

        self.roundTripJson(step_template)
        self.roundTripObj(step_template)
        
    def testStep(self):
        step = Step.create(self.step_obj)
        self.assertEqual(step.step_template.command, self.step_obj['step_template']['command'])

        self.roundTripJson(step)
        self.roundTripObj(step)

    def testFileRecipe(self):
        file_recipe = FileRecipe.create(self.file_recipe_obj)
        self.assertEqual(file_recipe.output_port.file_path, self.file_recipe_obj['output_port']['file_path'])

        self.roundTripJson(file_recipe)
        self.roundTripObj(file_recipe)

    def testDataObjectAsFileRecipe(self):
        data_object = DataObject.create(self.file_recipe_obj)
        self.assertEqual(data_object.output_port.file_path, self.file_recipe_obj['output_port']['file_path'])
        self.assertTrue(isinstance(data_object, FileRecipe))

        self.roundTripJson(data_object)
        self.roundTripObj(data_object)
        
    def testDataObjectAsFile(self):
        data_object = DataObject.create(self.file_obj)
        self.assertEqual(data_object.hash_value, self.file_obj['hash_value'])
        self.assertTrue(isinstance(data_object, File))

        self.roundTripJson(data_object)
        self.roundTripObj(data_object)

    def testDataObjectAsDataObject(self):
        file_object = DataObject.create(self.file_obj)
        data_object = DataObject.objects.get(_id=file_object._id)

        self.roundTripJson(data_object)
        self.roundTripObj(data_object)

    def testResourceSet(self):
        resource_set = ResourceSet.create(self.resource_set_obj)
        self.assertEqual(resource_set.cores, self.resource_set_obj['cores'])

        self.roundTripJson(resource_set)
        self.roundTripObj(resource_set)

    def testAnalysisRequest(self):
        analysis_request = AnalysisRequest.create(self.analysis_request_obj)
        self.assertEqual(analysis_request.resource_sets.first().cores, self.analysis_request_obj['resource_sets'][0]['cores'])

        self.roundTripJson(analysis_request)
        self.roundTripObj(analysis_request)

    def testFileLocation(self):
        # Keep all of these in one test. If the test framework runs them in
        # parallel they may SegFault with sqlite database.

        azure_blob_location = AzureBlobLocation.create(self.azure_blob_location_obj)
        self.assertEqual(azure_blob_location.container, self.azure_blob_location_obj['container'])

        self.roundTripJson(azure_blob_location)
        self.roundTripObj(azure_blob_location)

        url_location = UrlLocation.create(self.url_location_obj)
        self.assertEqual(url_location.url, self.url_location_obj['url'])

        self.roundTripJson(url_location)
        self.roundTripObj(url_location)

        file_path_location = FilePathLocation.create(self.file_path_location_obj)
        self.assertEqual(file_path_location.file_path, self.file_path_location_obj['file_path'])

        self.roundTripJson(file_path_location)
        self.roundTripObj(file_path_location)

        file_location = FileLocation.create(self.azure_blob_location_obj)
        self.assertEqual(file_location.container, self.azure_blob_location_obj['container'])

        self.roundTripJson(file_location)
        self.roundTripObj(file_location)

    def testStepRunRecord(self):
        step_run_record = StepRunRecord.create(self.step_run_record_obj)
        self.assertEqual(step_run_record.file.hash_value, self.step_run_record_obj['file']['hash_value'])

        self.roundTripJson(step_run_record)
        self.roundTripObj(step_run_record)

    def testStepRun(self):
        step_run = StepRun.create(self.step_run_obj)
        step_run.update({'step_run_record': self.step_run_record_obj})
        self.assertEqual(step_run.step_run_record.file.hash_value, self.step_run_record_obj['file']['hash_value'])

        self.roundTripJson(step_run)
        self.roundTripObj(step_run)

    def testAnalysisRunRecord(self):
        analysis_run_record = AnalysisRunRecord.create(self.analysis_run_record_obj)
#        self.assertEqual(analysis_run_record.analysis_request.requester, self.analysis_request_obj['requester'])

        self.roundTripJson(analysis_run_record)
        self.roundTripObj(analysis_run_record)

    def testAnalysisRun(self):
        analysis_run = AnalysisRun.create(self.analysis_run_obj)
        analysis_run.update({'analysis_run_record': self.analysis_run_record_obj})
        self.assertEqual(analysis_run.analysis_run_record.analysis_request.requester, self.analysis_run_record_obj['analysis_request']['requester'])

        self.roundTripJson(analysis_run)
        self.roundTripObj(analysis_run)

    def testFileImportRecord(self):
        file_import_record = FileImportRecord.create(self.file_import_record_obj)
        self.assertEqual(file_import_record.file.hash_value, self.file_import_record_obj['file']['hash_value'])

        self.roundTripJson(file_import_record)
        self.roundTripObj(file_import_record)

    def testFileImportRun(self):
        file_import_run = FileImportRun.create(self.file_import_run_obj)
        file_import_run.update({'file_import_record': self.file_import_record_obj})
        self.assertEqual(file_import_run.file_import_record.file.hash_value, self.file_import_record_obj['file']['hash_value'])

        self.roundTripJson(file_import_run)
        self.roundTripObj(file_import_run)

    def roundTripJson(self, model):
        cls = model.__class__
        id1 = model._id
        model = cls.create(model.to_json())
        self.assertEqual(model._id, id1)

    def roundTripObj(self, model):
        cls = model.__class__
        id1 = model._id
        model = cls.create(model.to_obj())
        self.assertEqual(model._id, id1)
