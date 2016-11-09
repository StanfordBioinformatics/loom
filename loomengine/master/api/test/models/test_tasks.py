from django.test import TestCase
from api.models.data_objects import *
from api.models.tasks import *


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


class TestTask(TestCase):

    def testCreate(self):
        task = get_task()
        self.assertTrue(task.command.startswith('echo'))

    def testCreateAttempt(self):
        task = get_task()
        task_attempt = task.create_attempt()
        self.assertEqual(task_attempt.rendered_command, task.rendered_command)


class TestTaskAttempt(TestCase):

    def setUp(self):
        self.task = get_task()
        self.task_attempt = self.task.create_attempt()

    def testCreateAttempt(self):
        self.assertEqual(self.task_attempt.outputs.first().channel,
                         self.task.outputs.first().channel)
        self.assertEqual(self.task_attempt.outputs.first().type,
                         self.task.outputs.first().type)
        self.assertEqual(self.task_attempt.outputs.first().source.stream,
                         self.task.outputs.first().source.stream)
        
