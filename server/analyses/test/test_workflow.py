from django.test import TestCase
from analyses.models import *
from analyses.test.test_models import TestModels


class TestWorkFlow(TestCase):

    def test_file_import(self):

        # Client calculates hash of file
        hash_value = 'd8e8fca2dc0f896fd7cb4cb0031ba249'
        hash_function = 'md5'

        # User specifies comments and destination location
        destination_file_path = '/data/local/path/test.txt'
        comments = 'This is thorough description of file source.'


        # FileImportRun object is created
        file_import_run_obj = {
            'import_comments': comments,
            'destination': {
                'file': {
                    'hash_value': hash_value,
                    'hash_function': hash_function,
                    },
                'file_path': destination_file_path,
                },
            }
        
        file_import_run = FileImportRun.create(file_import_run_obj)

        # Upload begins (not in test)
        # Upload finishes (not in test)

        # FileImportRecord object is created and FileImportRun is updated
        file_import_record_obj = {
            'import_comments': file_import_run.import_comments,
            'file': file_import_run.destination.file.to_obj(),
            }

        file_import_record = FileImportRecord.create(file_import_record_obj)
        file_import_run.update({
                'file_import_record':file_import_record.to_obj(),
                })

    def test_analysis_request_submission(self):
        # Create an analysis request
        analysis_request = AnalysisRequest.create(TestModels.analysis_request_obj)
        environment = analysis_request.file_recipes.first().step.step_template.environment.downcast().docker_image
        self.assertEqual(environment, TestModels.analysis_request_obj['file_recipes'][0]['step']['step_template']['environment']['docker_image'])

        # Associate analysis request with analysis run
        analysis_run = AnalysisRun.create({
                'analysis_request': analysis_request.to_obj(),                
                })
        self.assertEqual(analysis_run.analysis_request._id, analysis_request._id)
        
    def test_run_analysis(self):
        # Submit an analysis request and start an analysis_run
        analysis_request = AnalysisRequest.create(TestModels.analysis_request_obj)

        # Associate analysis request with analysis run
        analysis_run = AnalysisRun.create({
                'analysis_request': analysis_request.to_obj(),                
                })
        self.assertEqual(analysis_run.analysis_request._id, analysis_request._id)


        # Request step ready to run, create a StepRun
        import pdb; pdb.set_trace()
        

        # Post StepResult and update StepRun

