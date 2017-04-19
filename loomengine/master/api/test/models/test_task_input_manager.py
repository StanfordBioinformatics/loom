from django.test import TestCase
from api.models.data_objects import DataObject
from api.models.task_input_manager import TaskInputManager
from api.models.runs import StepRunInput

class TestScalarInputs(TestCase):

    def testSingleScalarInput(self):
        channel = 'channel1'
        index = []
        string_data = 'input1_data'

        input1 = StepRunInput.objects.create(
            channel = channel,
            group = 0,
            mode = 'no_gather',
            type = 'string'
        )
        data_object = DataObject.get_by_value(string_data, 'string')
        input1.add_data_object([], data_object)
        input_nodes = [input1]
        t = TaskInputManager(input_nodes)
        input_sets = t.get_ready_input_sets(channel, index)

        self.assertEqual(len(input_sets), 1)
        self.assertEqual(input_sets[0].data_path, [])
        input_items = input_sets[0].input_items
        self.assertEqual(len(input_items), 1)
        self.assertEqual(input_items[0].channel, channel)
        self.assertEqual(input_items[0].data_object.substitution_value,
                         string_data)

    def testSingleScalarInputNoData(self):
        channel = 'channel1'
        index = []

        input1 = StepRunInput.objects.create(
            channel = channel,
            group = 0,
            mode = 'no_gather',
            type = 'string'
        )
        input_nodes = [input1]
        t = TaskInputManager(input_nodes)
        input_sets = t.get_ready_input_sets(channel, index)

        self.assertEqual(len(input_sets), 0)

    def testTwoScalarInputs(self):
        channel1 = 'channel1'
        channel2 = 'channel2'
        index = []
        string_data1 = 'input1_data'
        string_data2 = 'input2_data'

        input1 = StepRunInput.objects.create(
            channel = channel1,
            group = 0,
            mode = 'no_gather',
            type = 'string'
        )
        input2 = StepRunInput.objects.create(
            channel = channel2,
            group = 0,
            mode = 'no_gather',
            type = 'string'
        )
        data_object1 = DataObject.get_by_value(string_data1, 'string')
        input1.add_data_object([], data_object1)
        data_object2 = DataObject.get_by_value(string_data2, 'string')
        input2.add_data_object([], data_object2)
        input_nodes = [input1, input2]
        t = TaskInputManager(input_nodes)
        input_sets = t.get_ready_input_sets(channel1, index)

        self.assertEqual(len(input_sets), 1)
        self.assertEqual(input_sets[0].data_path, [])
        input_items = input_sets[0].input_items
        self.assertEqual(len(input_items), 2)
        self.assertEqual(input_items[0].channel, channel1)
        self.assertEqual(input_items[0].data_object.substitution_value,
                         string_data1)
        self.assertEqual(input_items[1].channel, channel2)
        self.assertEqual(input_items[1].data_object.substitution_value,
                         string_data2)

    def testTwoScalarInputsNoData(self):
        channel1 = 'channel1'
        channel2 = 'channel2'
        index = []

        input1 = StepRunInput.objects.create(
            channel = channel1,
            group = 0,
            mode = 'no_gather',
            type = 'string'
        )
        input2 = StepRunInput.objects.create(
            channel = channel2,
            group = 0,
            mode = 'no_gather',
            type = 'string'
        )
        input_nodes = [input1, input2]
        t = TaskInputManager(input_nodes)
        input_sets = t.get_ready_input_sets(channel1, index)

        self.assertEqual(len(input_sets), 0)

class TestArrayInputs(TestCase):

    def testSingleArrayInput(self):
        channel = 'channel1'
        string_data = ['one', 'two', 'three']

        input = StepRunInput.objects.create(
            channel=channel,
            group = 0,
            mode = 'no_gather',
            type = 'string'
        )
        data_objects = [
            DataObject.get_by_value(string_data[i], 'string')
            for i in range(len(string_data))]
        degree = len(data_objects)
        for i in range(len(data_objects)):
            input.add_data_object([(i,degree)], data_objects[i])

        input_nodes = [input]

        for index in range(len(data_objects)):
            data_path = [(index, len(data_objects)),]
            t = TaskInputManager(input_nodes)
            input_sets = t.get_ready_input_sets(channel, data_path)
            self.assertEqual(len(input_sets), 1)
            self.assertEqual(input_sets[index].data_path, data_path)
            input_items = input_sets[0].input_items
            self.assertEqual(len(input_items), 1)
            self.assertEqual(input_items[index].channel, channel)
            self.assertEqual(input_items[index].data_object.substitution_value,
                             string_data[index])

# TEST CASES
# done - scalar input on 1 channel, no_gather
# done - scalar input on 2 channels, same group, no_gather
# todo - 1-d array on 1 channel, no_gather
# todo - 1-d array on 1 channel, gather
# todo - 1-d array on 2 channels, same group, both no_gather
# todo - 1-d array on 2 channels, same group, both gather
# todo - 1-d array on 2 channels, different groups, one with gather, one with no gather

# NEG TEST CASES
# Gather on channel with scalar data

