from django.test import TestCase, override_settings
import yaml

from api.test.models.test_templates import get_template
from api.models.data_objects import *
from api.models.runs import Run, TaskNode
from api.models.input_calculator import InputCalculator
from api.serializers.runs import  RunSerializer
from api.test.helper import request_run_from_template_file

def get_run():
    template = get_template()
    run_data = {'template': '@%s' % template.uuid}
    s = RunSerializer(data=run_data)
    s.is_valid(raise_exception=True)
    run = s.save()
    return run

class TestRun(TestCase):

    def testCreate(self):
        with self.settings(TEST_DISABLE_ASYNC_DELAY=True,
                           TEST_NO_PUSH_INPUTS=True):
            run = get_run()
        self.assertTrue(run.name == 'one_two')
        self.assertTrue(
            run.steps.get(name='step_one')\
            .inputs.get(channel='one')\
            .is_connected(
                run.inputs.get(channel='one')))


class TestInputCalculator(TestCase):

    def testSimple(self):
        with self.settings(TEST_DISABLE_ASYNC_DELAY=True, TEST_NO_CREATE_TASK=True):
            run = request_run_from_template_file(
                os.path.join(os.path.dirname(__file__), '..', '..', 'test',
                             'fixtures', 'simple', 'simple.yaml'),
                word_in='puppy')

        sets = InputCalculator(run).get_input_sets()
               
        self.assertEqual(len(sets), 1)
        self.assertEqual(sets[0].data_path, [])
        input_items = [item for item in sets[0]]
        self.assertEqual(len(input_items), 1)
        self.assertEqual(input_items[0].channel, 'word_in')

class MockTask(object):

    def __init__(self, data_path=[], status_is_finished=True):
        self.status_is_finished = status_is_finished
        self.data_path = data_path

class TestTaskNode(TestCase):

    def testEmpty(self):
        node = TaskNode()
        self.assertFalse(node.is_complete())

    def testScalarWithFinishedStatus(self):
        task = MockTask(status_is_finished=True)
        tree = TaskNode.create_from_task_list([task])
        self.assertTrue(tree.is_complete())

    def testScalarWithUnfinishedStatus(self):
        task = MockTask(status_is_finished=False)
        tree = TaskNode.create_from_task_list([task])
        self.assertFalse(tree.is_complete())

    def testArrayWithFinishedStatus(self):
        task1 = MockTask(status_is_finished=True, data_path=[[0,2]])
        task2 = MockTask(status_is_finished=True, data_path=[[1,2]])
        tree = TaskNode.create_from_task_list([task1,task2])
        self.assertTrue(tree.is_complete())

    def testArrayWithUnfinishedStatus(self):
        task1 = MockTask(status_is_finished=True, data_path=[[0,2]])
        task2 = MockTask(status_is_finished=False, data_path=[[1,2]])
        tree = TaskNode.create_from_task_list([task1,task2])
        self.assertFalse(tree.is_complete())

    def testArrayWithFinishedStatusAndMissingNodes(self):
        task1 = MockTask(status_is_finished=True, data_path=[[0,2]])
        tree = TaskNode.create_from_task_list([task1])
        self.assertFalse(tree.is_complete())

    def testArrayWithUnfinishedStatusAndMissingNodes(self):
        task1 = MockTask(status_is_finished=False, data_path=[[0,2]])
        tree = TaskNode.create_from_task_list([task1])
        self.assertFalse(tree.is_complete())

    def testTreeWithFinishedStatus(self):
        task11 = MockTask(status_is_finished=True, data_path=[[0,2],[0,2]])
        task12 = MockTask(status_is_finished=True, data_path=[[0,2],[1,2]])
        task21 = MockTask(status_is_finished=True, data_path=[[1,2],[0,2]])
        task22 = MockTask(status_is_finished=True, data_path=[[1,2],[1,2]])
        tree = TaskNode.create_from_task_list([task11,task12,task21,task22])
        self.assertTrue(tree.is_complete())

    def testTreeWithUnfinishedStatus(self):
        task11 = MockTask(status_is_finished=True, data_path=[[0,2],[0,2]])
        task12 = MockTask(status_is_finished=True, data_path=[[0,2],[1,2]])
        task21 = MockTask(status_is_finished=False, data_path=[[1,2],[0,2]])
        task22 = MockTask(status_is_finished=True, data_path=[[1,2],[1,2]])
        tree = TaskNode.create_from_task_list([task11,task12,task21,task22])
        self.assertFalse(tree.is_complete())

    def testTreeWithFinishedStatusAndMissingNodes(self):
        task11 = MockTask(status_is_finished=True, data_path=[[0,2],[0,2]])
        task12 = MockTask(status_is_finished=True, data_path=[[0,2],[1,2]])
        task22 = MockTask(status_is_finished=True, data_path=[[1,2],[1,2]])
        tree = TaskNode.create_from_task_list([task11,task12,task22])
        self.assertFalse(tree.is_complete())

    def testTreeWithUnfinishedStatusAndMissingNodes(self):
        task11 = MockTask(status_is_finished=True, data_path=[[0,2],[0,2]])
        task21 = MockTask(status_is_finished=False, data_path=[[1,2],[0,2]])
        task22 = MockTask(status_is_finished=True, data_path=[[1,2],[1,2]])
        tree = TaskNode.create_from_task_list([task11,task21,task22])
        self.assertFalse(tree.is_complete())
