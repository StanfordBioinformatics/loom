from django.test import TestCase
import json
import os
from api.serializers import FileDataObjectSerializer, \
    RunRequestSerializer, WorkflowSerializer

from loomengine.utils import md5calc


class AbstractRunTest(object):

    def run_workflow(self, workflow_path, **kwargs):
        run_request = {}
        
        with open(workflow_path) as f:
            workflow_data = json.load(f)
        s = WorkflowSerializer(data=workflow_data)
        s.is_valid(raise_exception=True)
        wf = s.save()

        run_request['template'] = wf.id.hex
        run_request['inputs'] = []
        
        for (channel, value) in kwargs.iteritems():
            input = wf.get_input(channel)
            if input.type == 'file':
                file_path = value
                hash_value = md5calc.calculate_md5sum(file_path)
                file_data = {
                    'file_content': {
                        'filename': os.path.basename(file_path),
                        'unnamed_file_content': {
                            'hash_value': hash_value,
                            'hash_function': 'md5'
                        }
                    },
                    'file_location':{
                        'status': 'complete',
                        'url': 'file://' + os.path.abspath(file_path)
                    }
                }
                s = FileDataObjectSerializer(data=file_data)
                s.is_valid(raise_exception=True)
                fdo = s.save()
                value = fdo.id.hex
            run_request['inputs'].append({
                'channel': channel,
                'value': value
            })

        s = RunRequestSerializer(data=run_request)
        s.is_valid(raise_exception=True)
        with self.settings(WORKER_TYPE='MOCK'):
            return s.save()
            

class TestHelloWorld(TestCase, AbstractRunTest):

    def setUp(self):
        workflow_dir = os.path.join(
            os.path.dirname(__file__),'..','fixtures','runs','hello_world')
        workflow_file = os.path.join(workflow_dir, 'hello_world.json')
        hello_file = os.path.join(workflow_dir, 'hello.txt')
        world_file = os.path.join(workflow_dir, 'world.txt')

        self.run_request = self.run_workflow(workflow_file,
                                             hello=hello_file,
                                             world=world_file)

    def testRun(self):
        # Verify that output data objects have been created
        self.assertIsNotNone(self.run_request.run.step_runs.first().task_runs\
                             .first().task_run_attempts.first()\
                             .outputs.first().data_object)
        self.assertIsNotNone(
            self.run_request.outputs.first()\
            .indexed_data_objects.first().data_object)
