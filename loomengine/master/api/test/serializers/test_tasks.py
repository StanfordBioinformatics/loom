from django.test import TestCase
from rest_framework import serializers

from api.serializers.tasks import *
from api.models.tasks import *
from api.models.data_objects import BooleanDataObject


def get_task():
    task = Task.objects.create(
        interpreter='/bin/bash',
        command='echo {{input1}}',
        rendered_command='echo True'
    )
    input_data_object = BooleanDataObject.objects.create(
        type='boolean',
        value=True
    )
    input = TaskInput.objects.create(task=task,
                                     data_object=input_data_object,
                                     channel='input1',
                                     type='boolean')
    output = TaskOutput.objects.create(
        task=task,
        channel='output1',
        type='string'
    )
    output_source = TaskOutputSource.objects.create(
        task_output=output,
        stream='stdout'
    )
    resources = TaskResourceSet.objects.create(
        task=task,
        memory='1',
        disk_size='1',
        cores='1')
    environment = TaskDockerEnvironment.objects.create(
        type='docker',
        task=task,
        docker_image='ubuntu'
    )
    return task


class TestTaskSerializer(TestCase):
    
    def testRender(self):
        task = get_task()
        s = TaskSerializer(task)
        task_data = s.data
        self.assertEqual(task_data['command'],
                         task.command)

class TestTaskSerializerIdOnly(TestCase):

    def testRender(self):
        task = get_task()
        s = TaskSerializerIdOnly(task)
        task_data = s.data
        self.assertEqual(task_data['id'],
                         task.id.hex)

    
    
