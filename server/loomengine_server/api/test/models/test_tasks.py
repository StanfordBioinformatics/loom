from django.test import TestCase

from api.test.models import _get_string_data_node
from api.models.data_objects import *
from api.models.tasks import *


def get_task():
    task = Task.objects.create(
        interpreter='/bin/bash',
        raw_command='echo {{input1}}; echo {{ input3|join(", ") }}',
        command='echo True',
        resources={'memory': '1', 'disk_size': '1', 'cores': '1'},
        environment={'docker_image': 'ubuntu'},
        data_path = [[0,1],],
    )
    input_data_node = _get_string_data_node('input1')

    input = TaskInput.objects.create(task=task,
                                     data_node=input_data_node,
                                     channel='input1',
                                     mode='no_gather',
                                     type='boolean')

    input_data_node2 = _get_string_data_node('input2')
    input2 = TaskInput.objects.create(task=task,
                                      data_node=input_data_node2,
                                      channel='input2',
                                      mode='no_gather',
                                      type='string')

    input_data_node3 = _get_string_data_node(
        ['salud','amor','dinero'])

    input3 = TaskInput.objects.create(task=task,
                                      data_node=input_data_node3,
                                      channel='input3',
                                      mode='gather',
                                      type='string')
    output = TaskOutput.objects.create(
        task=task,
        channel='output1',
        type='string',
        mode='no_scatter',
        source={'filename': '{{input2}}.txt'}
    )
    return task


class TestTask(TestCase):

    def testCreate(self):
        task = get_task()
        self.assertTrue(task.command.startswith('echo'))

    def testCreateAttempt(self):
        task = get_task()
        task_attempt = task.create_and_activate_task_attempt()
        self.assertEqual(task_attempt.command, task.command)

    def testGetInputContext(self):
        task = get_task()
        context = task.get_input_context()
        self.assertEqual(context['input3'][2], 'dinero')
        self.assertEqual(str(context['input3']), 'salud amor dinero')
        command = task.render_command(task.inputs.all(), task.outputs.all())
        self.assertEqual(command, 'echo input1; echo salud, amor, dinero')

    def testGetContentsForFingerprint(self):
        task = get_task()
        self.assertEqual(task.calculate_contents_fingerprint(),
                         'ae60c524085e58e8008fe455db3f4ac6')


class TestTaskAttempt(TestCase):

    def setUp(self):
        self.task = get_task()
        self.task_attempt = self.task.create_and_activate_task_attempt()

    def testCreateAttempt(self):
        self.assertEqual(self.task_attempt.outputs.first().channel,
                         self.task.outputs.first().channel)
        self.assertEqual(self.task_attempt.outputs.first().type,
                         self.task.outputs.first().type)
        self.assertEqual(self.task_attempt.outputs.first().source.get('stream'),
                         self.task.outputs.first().source.get('stream'))
        self.assertEqual(self.task_attempt.outputs.first().source.get('filename'),
                         'input2.txt')
