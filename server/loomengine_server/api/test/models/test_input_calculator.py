from django.test import TestCase

from api.test.models import _get_string_data_object
from api.models.data_objects import DataObject
from api.models.data_nodes import DataNode
from api.models.input_calculator import InputCalculator, InputSetGeneratorNode
from api.models.runs import Run, RunInput

scalar_input_text = 'scalar data'

full_input_data=(
    ([(0,3),(0,1)], 'i'),
    ([(1,3),(0,2)], 'a'),
    ([(1,3),(1,2)], 'm'),
    ([(2,3),(0,5)], 'r'),
    ([(2,3),(1,5)], 'o'),
    ([(2,3),(2,5)], 'b'),
    ([(2,3),(3,5)], 'o'),
    ([(2,3),(4,5)], 't'),
)
partial_input_data = [full_input_data[i] for i in [0,3,7]]

def getScalarInput(channel_name='channel1',
                   mode='no_gather',
                   group=0):
    data_node = DataNode.objects.create(type='string')
    data_node.add_data_object(
        [],
        _get_string_data_object(scalar_input_text),
        save=True)
    step_run_input = RunInput.objects.create(
        channel=channel_name, group=group, mode=mode, type='string')
    step_run_input.data_node = data_node
    step_run_input.save()
    return step_run_input

def getInputWithPartialTree(channel_name='channel1',
                            mode='no_gather',
                            group=0):
    data_node = DataNode.objects.create(type='string')
    for data_path, letter in partial_input_data:
        data_object = _get_string_data_object(letter)
        data_node.add_data_object(data_path, data_object, save=True)
    step_run_input = RunInput.objects.create(
        channel=channel_name, group=group, mode=mode, type='string')
    step_run_input.data_node = data_node
    step_run_input.save()
    return step_run_input

def getInputWithFullTree(channel_name='channel1',
                         mode='no_gather',
                         group=0):
    data_node = DataNode.objects.create(type='string')
    for data_path, letter in full_input_data:
        data_object = _get_string_data_object(letter)
        data_node.add_data_object(data_path, data_object, save=True)
    step_run_input = RunInput.objects.create(
        channel=channel_name, group=group, mode=mode, type='string')
    step_run_input.data_node = data_node
    step_run_input.save()
    return step_run_input

def are_paths_equal(path1, path2):
    if len(path1) != len(path2):
        return False
    for pair1, pair2 in zip(path1, path2):
        if int(pair1[0]) != int(pair2[0]):
            return False
        if int(pair1[1]) != int(pair2[1]):
            return False
    return True


class TestInputCalculator(TestCase):

    def testSingleScalarInput(self):
        channel = 'a_scalar_channel'
        step_run_input = getScalarInput(
            mode='no_gather', channel_name=channel, group=0)
        run = Run.objects.create(is_leaf=True)
        run.inputs.add(step_run_input)
        t = InputCalculator(run)
        input_sets = t.get_input_sets()
        self.assertEqual(len(input_sets), 1)
        self.assertEqual(input_sets[0].data_path, [])
        input_items = input_sets[0].input_items
        self.assertEqual(len(input_items), 1)
        self.assertEqual(input_items[0].channel, channel)
        self.assertEqual(input_items[0].data_node.data_object.substitution_value,
                         scalar_input_text)

    def testSingleParallelInput(self):
        channel = 'a_parallel_channel'
        step_run_input = getInputWithPartialTree(
            mode='no_gather', channel_name=channel, group=0)
        run = Run.objects.create(is_leaf=True)
        run.inputs.add(step_run_input)
        t = InputCalculator(run)
        input_sets = t.get_input_sets()

        self.assertEqual(len(input_sets), 3)
        self.assertTrue(are_paths_equal(input_sets[0].data_path, [(0,3),(0,1)]))
        input_items = input_sets[0].input_items
        self.assertEqual(len(input_items), 1)
        self.assertEqual(input_items[0].channel, channel)
        self.assertEqual(input_items[0].data_node.data_object.substitution_value,
                         'i')

    def testSingleParallelInputWithGatherMissingData(self):
        channel = 'a_parallel_channel'
        step_run_input = getInputWithPartialTree(
            mode='gather(2)', channel_name=channel, group=0)
        run = Run.objects.create(is_leaf=True)
        run.inputs.add(step_run_input)
        t = InputCalculator(run)
        input_sets = t.get_input_sets()
        self.assertEqual(len(input_sets), 0) #Nothing ready

    def testSingleParallelInputWithGather(self):
        channel = 'a_parallel_channel'
        step_run_input = getInputWithFullTree(
            mode='gather(2)', channel_name=channel, group=0)
        run = Run.objects.create(is_leaf=True)
        run.inputs.add(step_run_input)
        t = InputCalculator(run)
        input_sets = t.get_input_sets()
        self.assertEqual(len(input_sets), 1)
        self.assertEqual(input_sets[0].data_path, [])
        input_items = input_sets[0].input_items
        self.assertEqual(len(input_items), 1)
        self.assertEqual(input_items[0].channel, channel)
        self.assertEqual(input_items[0].data_node.substitution_value,
                         ['i','a','m','r','o','b','o','t'])

    def testTwoInputsSameGroup(self):
        channel = 'channel1'
        input1 = getInputWithPartialTree(
            mode='no_gather', channel_name=channel, group=0)

        channel2 = 'channel2'
        input2 = getScalarInput(
            mode='no_gather', channel_name=channel2, group=0)

        run = Run.objects.create(is_leaf=True)
        run.inputs.add(input1)
        run.inputs.add(input2)
        t = InputCalculator(run)
        input_sets = t.get_input_sets()
        self.assertEqual(len(input_sets), 3)
        self.assertTrue(are_paths_equal(input_sets[0].data_path, [(0,3),(0,1)]))
        input_items = input_sets[0].input_items
        self.assertEqual(len(input_items), 2)

    def testTwoInputsDifferentGroups(self):
        channel = 'channel1'
        input1 = getInputWithPartialTree(
            mode='no_gather', channel_name=channel, group=0)

        channel2 = 'channel2'
        input2 = getScalarInput(
            mode='no_gather', channel_name=channel2, group=1)

        run = Run.objects.create(is_leaf=True)
        run.inputs.add(input1)
        run.inputs.add(input2)
        t = InputCalculator(run)
        input_sets = t.get_input_sets()
        self.assertEqual(len(input_sets), 3)
        self.assertTrue(are_paths_equal(input_sets[0].data_path, [(0,3),(0,1)]))
        input_items = input_sets[0].input_items
        self.assertEqual(len(input_items), 2)

    def testTwoParallelInputsDifferentGroups(self):
        channel = 'channel1'
        input1 = getInputWithPartialTree(
            mode='no_gather', channel_name=channel, group=0)

        channel2 = 'channel2'
        input2 = getInputWithFullTree(
            mode='no_gather', channel_name=channel2, group=1)

        run = Run.objects.create(is_leaf=True)
        run.inputs.add(input1)
        run.inputs.add(input2)
        t = InputCalculator(run)
        input_sets = t.get_input_sets()
        self.assertEqual(len(input_sets), 3*8)
        self.assertTrue(are_paths_equal(
            input_sets[0].data_path, [(0,3),(0,1),(0,3),(0,1)]))
        self.assertTrue(are_paths_equal(
            input_sets[8].data_path, [(2,3),(0,5),(0,3),(0,1)]))
        input_items = input_sets[0].input_items
        self.assertEqual(len(input_items), 2)

        # Now reverse order of groups
        channel = 'channel1'
        input1 = getInputWithPartialTree(
            mode='no_gather', channel_name=channel, group=1)

        channel2 = 'channel2'
        input2 = getInputWithFullTree(
            mode='no_gather', channel_name=channel2, group=0)

        run = Run.objects.create(is_leaf=True)
        run.inputs.add(input1)
        run.inputs.add(input2)
        t = InputCalculator(run)
        input_sets = t.get_input_sets()
        self.assertEqual(len(input_sets), 8*3)
        self.assertTrue(are_paths_equal(
            input_sets[0].data_path, [(0,3),(0,1),(0,3),(0,1)]))
        self.assertTrue(are_paths_equal(
            input_sets[4].data_path, [(1,3),(0,2),(2,3),(0,5)]))
        input_items = input_sets[0].input_items
        self.assertEqual(len(input_items), 2)

    def testTwoParallelInputsDifferentGroupsBothGather(self):
        channel = 'channel1'
        input1 = getInputWithPartialTree(
            mode='gather', channel_name=channel, group=0)

        channel2 = 'channel2'
        input2 = getInputWithFullTree(
            mode='gather', channel_name=channel2, group=1)

        run = Run.objects.create(is_leaf=True)
        run.inputs.add(input1)
        run.inputs.add(input2)
        t = InputCalculator(run)
        input_sets = t.get_input_sets()
        self.assertEqual(len(input_sets), 1*3)
        self.assertTrue(are_paths_equal(input_sets[0].data_path, [(0,3),(0,3)]))
        self.assertTrue(are_paths_equal(input_sets[1].data_path, [(0,3),(1,3)]))
        input_items = input_sets[0].input_items
        self.assertEqual(len(input_items), 2)

        
class TestInputSetGeneratorNode(TestCase):

    def testCreateFromRoot(self):
        step_run_input = getInputWithFullTree(mode='no_gather')
        generator = InputSetGeneratorNode.create_from_data_channel(step_run_input)
        input_sets = generator.get_input_sets([])
        self.assertEqual(len(input_sets), len(full_input_data))
        
    def testCreateFromRootWithGather(self):
        step_run_input = getInputWithFullTree(mode='gather')
        generator = InputSetGeneratorNode.create_from_data_channel(
            step_run_input)
        input_sets = generator.get_input_sets([])
        self.assertEqual(len(input_sets), 3) # 8 letters are merged into 3 arrays

    def testDotProduct(self):
        # Dot product of full and partial trees should produce a tree
        # with the shape of the partial tree but InputItems from both.
        # True for either order.
        step_run_input_full = getInputWithFullTree(mode='no_gather')
        step_run_input_partial = getInputWithPartialTree(mode='no_gather')
        generator_full = InputSetGeneratorNode.create_from_data_channel(
            step_run_input_full)
        generator_partial = InputSetGeneratorNode.create_from_data_channel(
            step_run_input_partial)
        generator_combined = generator_full.dot_product(generator_partial)
        generator_reverse = generator_partial.dot_product(generator_full)
        input_sets = generator_combined.get_input_sets([])
        input_sets_reverse = generator_reverse.get_input_sets([])
        self.assertEqual(len(input_sets), 3)
        self.assertEqual(len(input_sets_reverse), 3)
        self.assertEqual(input_sets[0].input_items[0]\
                          .data_node.data_object.substitution_value, 'i')
        self.assertEqual(input_sets[0].input_items[1]\
                          .data_node.data_object.substitution_value, 'i')
        self.assertEqual(input_sets_reverse[0].input_items[0]\
                          .data_node.data_object.substitution_value, 'i')
        self.assertEqual(input_sets_reverse[0].input_items[1]\
                          .data_node.data_object.substitution_value, 'i')

    def testCrossProduct(self):
        step_run_input_full = getInputWithFullTree(mode='no_gather')
        step_run_input_partial = getInputWithPartialTree(mode='no_gather')
        generator_full = InputSetGeneratorNode.create_from_data_channel(
            step_run_input_full)
        generator_partial = InputSetGeneratorNode.create_from_data_channel(
            step_run_input_partial)
        generator_combined = generator_full.cross_product(generator_partial)
        generator_reverse = generator_partial.cross_product(generator_full)
        input_sets = generator_combined.get_input_sets([])
        input_sets_reverse = generator_reverse.get_input_sets([])
        self.assertEqual(len(input_sets), 3 * 8)
        self.assertEqual(len(input_sets_reverse), 8 * 3)
        self.assertEqual(input_sets[0].input_items[0]\
                          .data_node.data_object.substitution_value, 'i')
        self.assertEqual(input_sets[0].input_items[1]\
                          .data_node.data_object.substitution_value, 'i')
        self.assertEqual(input_sets_reverse[0].input_items[0]\
                          .data_node.data_object.substitution_value, 'i')
        self.assertEqual(input_sets_reverse[0].input_items[1]\
                          .data_node.data_object.substitution_value, 'i')


# TEST CASES
# isang group lang:
# done - scalar input on 1 channel, no_gather
# done - scalar input on 2 channels, same group, no_gather
# todo - 1-d array on 1 channel, no_gather
# Use case - a user runs a 1-d no_gather workflow with an array input.
# This spawns a series of tasks, each of which produces a scalar output
# todo - 1-d array on 2 channels, same group, both no_gather

# multigroup
# todo - scalar input on 2 channels, different groups, no_gather
# todo - 1-d array on 1 channel, gather
# todo - 1-d array on 2 channels, same group, both gather
# todo - 1-d array on 2 channels, different groups, one with gather, one with no gather

# NEG TEST CASES
# Gather on channel with scalar data

