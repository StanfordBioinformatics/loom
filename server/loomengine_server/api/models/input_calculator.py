import copy
import re

from data_nodes import DegreeMismatchError

"""InputCalculator analyzes the set of nodes acting as inputs
for one Run to determine when sufficient data is available to 
create a new Task. For parallel Runs, many Tasks may be created.

InputCalculator includes logic for dot-product or cross-product combination
of array inputs, and complex combinations of the two. This behavior
is defined by these two properties on a RunInput:
- mode: [gather/no_gather/gather(n)]
- group: integer >= 0

Any input that is no_gather will provide the TaskInput with a scalar 
DataObject, while gather* mode will produce an array of DataObjects.

Consider that non-scalar inputs may simply be arrays, or may be trees of 
greater hight. When a non-scalar input is provided to a "no_gather" 
channel, it acts as an iterator and produces one Task for each DataObject.

When a non-scalar input is provided to the a "gather" channel, the TaskInput 
will receive an array of DataObjects, but the Run will still iterate and 
produce many Tasks if the gather depth is less than the height of the DataNode 
tree.

So every input has the potential to require iteration while producing either 
scalar or array inputs, and the number of Tasks in the iteration may differ 
between inputs.

"group" governs the dot/cross product behavior of that iteration when 
multiple inputs are present. If all inputs had different group numbers, the 
Run would perform a cross-product of all inputs. The number of Tasks would 
equal the product of the number of iterations on each step. Conversely, if 
all inputs had the same group number, a dot product would be performed across 
all inputs, and the number of Tasks would equal the number of iterations on 
any input. (The number of iterations on all inputs would have to be the same 
in this case, or a runtime error will be raised.)

This behavior can be generalized to any combination of dot-products and 
cross-products across inputs. A dot-product is performed for all inputs 
in the same group (and all are required to have the same number of 
iterations). A cross-product is performed between all groups, with the 
order of the cross-product corresponding to the order of group numbers.
"""


class InputCalculator(object):

    def __init__(self, run):
        data_channels = run.inputs.all()
        groups = set()
        for data_channel in data_channels:
            groups.add(data_channel.group)

        combined_generator = None
        for group in groups:
            # These will be processed in order of group id, ensuring
            # correct order for cross products.
            group_data_channels = filter(lambda n: n.group==group, data_channels)
            group_generator = None
            for node in group_data_channels:
                try:
                    generator = InputSetGeneratorNode.create_from_data_channel(node)
                except DegreeMismatchError:
                    raise Exception(
                        'Input dimensions do not match in group %s' % group)
                if group_generator is None:
                    group_generator = generator
                else:
                    group_generator = group_generator.dot_product(generator)

            if combined_generator is None:
                combined_generator = group_generator
            else:
                combined_generator = combined_generator.cross_product(group_generator)

        self.generator = combined_generator

    def get_input_sets(self):
        seed_path = []
        return self.generator.get_input_sets(seed_path)


class InputSetGeneratorNode(object):
    """A class for creating InputSets from various possible input configurations.

    Must handle the following variations in inputs:
    - Varied dimensionality of data on each input: scalar, array, or nested aray data
      e.g. 1, [1,2], or [[1,2],[3,4,5]], and so on.
    - One or more input in an input group (i.e. dot product), 
      e.g., combining two channels in the same group, 
      [1;2] * [3;4] -> [1,2;3,4]
    - One or more input groups (i.e. cross product), 
      e.g., combining two channels in different groups, 
      [1;2] x [3;4] -> [1,3;1,4;2,3;2,4]
    - "Gather" behavior or one or more inputs, 
       e.g. [1,2] -> Array(1,2), where the Array serves as an input to a single task
       or [[1,2],[3,4,5]] -> [Array(1,2),Array(3,4,5)], where each Array serves as an
       input to a task
    - "Gather(n)" behavior on one or more inputs,
      e.g. for gather(2), [[1,2],[3,4,5]] -> [Array(1,2,3,4,5)]

    An InputSetGeneratorNode may be triggered when one new DataObject arrives, 
    so it is not necessary to scan the whole data tree on the target input. 
    Instead, a target_data_path specifies which subtree to check for new 
    InputSets. (This target_data_path must be adjusted prior to calling 
    InputSetGeneratorNode if the input has "gather" mode.)
    """

    def __init__(self, index=None):
        self.index = index # Remains None for root node only
        self.degree = None # Remains None for leaf nodes only
        self.children = {} # key is index, value is InputSetGeneratorNode
        self.input_items = [] # list of InputItems, only on leaf nodes

    @classmethod
    def create_from_data_channel(cls, data_channel):
        """Scan the data tree on the given data_channel to create a corresponding
        InputSetGenerator tree.
        """
        gather_depth = cls._get_gather_depth(data_channel)

        generator = InputSetGeneratorNode()
        for (data_path, data_node) in data_channel.get_ready_data_nodes(
                [], gather_depth):
            flat_data_node = data_node.flattened_clone(save=False)
            input_item = InputItem(
                flat_data_node, data_channel.channel,
                data_channel.as_channel, mode=data_channel.mode)
            generator._add_input_item(data_path, input_item)
        return generator

    @classmethod
    def _get_gather_depth(cls, node):
        mode = node.mode
        if mode == 'no_gather':
            return 0
        elif mode == 'gather':
            return 1
        else:
            match = re.match('gather\(([0-9]+)\)', mode)
            if match is None:
                raise Exception('Failed to parse input mode %s' % mode)
            return int(match.groups()[0])
    
    def _add_input_item(self, data_path, input_item):
        return self._add_input_items(data_path, [input_item,])

    def _add_input_items(self, data_path, input_items):
        if len(data_path) == 0:
            self.input_items.extend(input_items)
            return

        (index, degree) = data_path.pop(0)

        if self.degree is None:
            self.degree = degree
        assert degree == self.degree, 'Degree mismatch'
        if not self.children.get(index):
            self.children[index] = InputSetGeneratorNode(index=index)
        self.children[index]._add_input_items(data_path, input_items)

    def dot_product(self, generator_B):
        generator_A_dot_B = InputSetGeneratorNode()
        for input_set_A in self.get_input_sets([]):
            seed_node_B = generator_B.get_node(input_set_A.data_path)
            if seed_node_B is None:
                continue
            for input_set_B in seed_node_B.get_input_sets(input_set_A.data_path):
                data_path = self._select_longer_path(
                    input_set_A.data_path, input_set_B.data_path)
                input_items = input_set_A.input_items + input_set_B.input_items
                generator_A_dot_B._add_input_items(data_path, input_items)
        return generator_A_dot_B

    def _select_longer_path(self, path1, path2):
        if len(path1) > len(path2):
            longer_path = path1
            shorter_path = path2
        else:
            longer_path = path2
            shorter_path=path1
        assert shorter_path == longer_path[0:len(shorter_path)], 'path mismatch'
        return longer_path

    def cross_product(self, generator_B):
        generator_A_cross_B = InputSetGeneratorNode()
        for input_set_A in self.get_input_sets([]):
            for input_set_B in generator_B.get_input_sets([]):
                data_path = input_set_A.data_path + input_set_B.data_path
                input_items = input_set_A.input_items + input_set_B.input_items
                generator_A_cross_B._add_input_items(data_path, input_items)
        return generator_A_cross_B

    def get_input_sets(self, seed_path):
        if self._is_leaf:
            path = copy.deepcopy(seed_path)
            if not self.input_items:
                return []
            else:
                return [InputSet(path, self.input_items)]
        else:
            input_sets = []
            for child in self.children.values():
                path = copy.deepcopy(seed_path)
                path.append([child.index, self.degree])
                input_sets.extend(child.get_input_sets(path))
            return input_sets

    @property
    def _is_leaf(self):
        return self.degree == None

    def get_node(self, path):
        if self._is_leaf:
            return self
        if len(path) == 0:
            return self
        path = copy.copy(path)
        index, degree = path.pop(0)
        assert degree == self.degree, 'degree mismatch in get_node'
        child = self.children.get(index)
        if not child:
            return None
        else:
            return child.get_node(path)

class InputSet(object):
    """All the information needed to create a Task from a given StepRun.
    """

    def __iter__(self):
        return self.input_items.__iter__()

    def __init__(self, data_path, input_items):
        self.data_path = data_path
        self.input_items = input_items


class InputItem(object):
    """All the information needed by the Task to construct one TaskInput.
    For array inputs, we avoid creating the ArrayDataObject now and instead
    provide the data_node from which the array can be generated. That way,
    if we find that the downstream Task has already been created, we can
    refrain from creating a new ArrayDataObject for no reason.
    """

    def __init__(self, data_node, channel, as_channel, mode):
        self.channel = channel
        self.as_channel = as_channel
        self.data_node = data_node
        self.mode = mode

    @property
    def type(self):
        return self.data_node.type
