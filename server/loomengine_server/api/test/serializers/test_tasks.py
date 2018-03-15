from django.test import TestCase
from rest_framework import serializers

from api.serializers.data_objects import DataObjectSerializer
from api.serializers.tasks import *
from api.models.tasks import *
from api.models.task_attempts import *
from api.models.data_objects import DataObject, FileResource
from api.models.data_nodes import DataNode
from . import fixtures
from . import get_mock_context, create_data_node_from_data_object

def get_task():
    task = Task.objects.create(
        interpreter='/bin/bash',
        raw_command='echo {{input1}}',
        command='echo True',
        resources={'memory': '1', 'disk_size': '1', 'cores': '1'},
        environment={'docker_image': 'ubuntu'},
        data_path=[[0,1],]
    )
    input_data_object = DataObject.objects.create(
        type='boolean',
        data={'value': True}
    )
    input_data_node = create_data_node_from_data_object(input_data_object)
    input = TaskInput.objects.create(task=task,
                                     data_node=input_data_node,
                                     channel='input1',
                                     mode='no_gather',
                                     type='boolean')

    output_data_object = DataObject.objects.create(
        type='string',
        data={'value': 'answer'}
    )

    output_data_node = create_data_node_from_data_object(output_data_object)
    
    task_output = TaskOutput.objects.create(
        task=task,
        channel='output1',
        type='string',
        mode='no_scatter',
        data_node=output_data_node,
        source={'stream': 'stdout'}
    )
    attempt_output_data_node = create_data_node_from_data_object(output_data_object)
    task_attempt = TaskAttempt.objects.create(
        interpreter = task.interpreter,
        command=task.command,
        environment=task.environment,
        resources=task.resources)
    task.add_to_all_task_attempts(task_attempt)
    task_attempt_output = TaskAttemptOutput.objects.create(
        task_attempt=task_attempt,
        data_node=attempt_output_data_node,
        mode='no_scatter',
        type='file',
        channel='test'
    )
    task_attempt_event = TaskAttemptEvent.objects.create(
        task_attempt=task_attempt,
        event='oops',
        detail='something went wrong',
        is_error=True)

    log_file = TaskAttemptLogFile.objects.create(
        task_attempt=task_attempt,
        log_name='stderr.log',
    )

    file_data = {
        'type': 'file',
        'value': {
            'filename': 'stderr.log',
            'md5': 'eed7ca1bba1c93a7fa5b5dba1307b791',
            'source_type': 'log',
        }
    }
    s = DataObjectSerializer(
        data=file_data,
        context={'task_attempt_log_file': log_file})
    s.is_valid()
    log_file_data_object = s.save()

    return task

class TestTaskSerializer(TestCase):

    def testRender(self):
        task = get_task()
        s = TaskSerializer(task, context=get_mock_context())
        task_data = s.data
        self.assertEqual(task_data['command'],
                         task.command)
