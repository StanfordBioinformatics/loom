from django.test import TransactionTestCase, override_settings
import json
import os
from api.models import RunRequest
from api.serializers import FileDataObjectSerializer, \
    RunRequestSerializer, TemplateSerializer

import loomengine.utils.md5calc
import loomengine.utils.helper

class AbstractRunTest(object):

    def run_template(self, template_path, **kwargs):
        run_request = {}

        with open(template_path) as f:
            template_data = json.load(f)
        s = TemplateSerializer(data=template_data)
        s.is_valid(raise_exception=True)
        template = s.save()

        run_request['template'] = '@%s' % str(template.uuid)
        run_request['inputs'] = []

        for (channel, value) in kwargs.iteritems():
            input = template.get_input(channel)
            if input.get('type') == 'file':
                # Files have to be pre-imported.
                # Other data types can be 
                file_path = value
                hash_value = loomengine.utils.md5calc\
                                             .calculate_md5sum(file_path)
                file_data = {
                    'type': 'file',
                    'filename': os.path.basename(file_path),
                    'md5': hash_value,
                    'source_type': 'imported',
                    'file_resourcelocation':{
                        'upload_status': 'complete',
                        'file_url': 'file://' + os.path.abspath(file_path),
                        'md5': hash_value,
                    }
                }
                s = FileDataObjectSerializer(data=file_data)
                s.is_valid(raise_exception=True)
                fdo = s.save()
                value = '@%s' % fdo.uuid
            run_request['inputs'].append({
                'channel': channel,
                'data': {'contents': value,},
            })

        s = RunRequestSerializer(data=run_request)
        s.is_valid(raise_exception=True)
        with self.settings(WORKER_TYPE='MOCK'):
            run_request = s.save()
        loomengine.utils.helper.wait_for_true(
            lambda: RunRequest.objects.get(id=run_request.id).run.postprocessing_status == 'done', timeout_seconds=120, sleep_interval=1)
        loomengine.utils.helper.wait_for_true(
            lambda: all([step.postprocessing_status=='done'
                         for step
                         in RunRequest.objects.get(
                             id=run_request.id).run.workflowrun.steps.all()]),
            timeout_seconds=120,
            sleep_interval=1)

        return run_request


@override_settings(TEST_DISABLE_TASK_DELAY=True)
class TestHelloWorld(TransactionTestCase, AbstractRunTest):

    def setUp(self):
        workflow_dir = os.path.join(
            os.path.dirname(__file__),'..','serializers','fixtures',
            'run_fixtures','hello_world')
        workflow_file = os.path.join(workflow_dir, 'hello_world.json')
        hello_file = os.path.join(workflow_dir, 'hello.txt')
        world_file = os.path.join(workflow_dir, 'world.txt')

        self.run_request = self.run_template(workflow_file,
                                             hello=hello_file,
                                             world=world_file)

    def testRun(self):

        # Verify that all StepRuns have been created
        self.assertIsNotNone(
            self.run_request.run.downcast().steps.filter(name='hello_step'))
        self.assertIsNotNone(
            self.run_request.run.downcast().steps.filter(name='world_step'))

        
        # Verify that output data objects have been created
        #self.assertIsNotNone(self.run_request.run.steps.first().task_runs\
        #                     .first().task_run_attempts.first()\
        #                     .outputs.first().data_object)
        #self.assertIsNotNone(
        #    self.run_request.outputs.first()\
        #    .indexed_data_objects.first().data_object)

@override_settings(TEST_DISABLE_TASK_DELAY=True)
class TestManySteps(TransactionTestCase, AbstractRunTest):

    def setUp(self):
        workflow_dir = os.path.join(
            os.path.dirname(__file__),'..','serializers','fixtures',
            'run_fixtures','many_steps')
        workflow_file = os.path.join(workflow_dir, 'many_steps.json')

        self.run_request = self.run_template(workflow_file)

    def testRun(self):
        pass
