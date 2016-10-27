import copy
import json
import jsonschema

from .base import BaseModel, BasePolymorphicModel
from django.db import models
from django.core.exceptions import ObjectDoesNotExist

from api.models.data_objects import DataObject

"""
InputOutputNodes are connected to facilitate the flow of data in a workflow, e.g. from 
a WorkflowRunInput to the StepRunInput of a StepRun nested in that Workflow, or from a 
StepRunOutput to the StepRunInput of a subsequent Step.

InputOutputNode is inherited by all input/output classes that may need to handle 
data trees with height > 1 (RunRequestInput, WorkflowRunInput/Output, 
StepRunInput/Output) but not by TaskRuns, TaskRunAttempts, or TaskDefinitions since 
these only contain data as scalars or 1-dimensional arrays.

Data under each InputOutputNode is represented as a tree of DataNodes. This
lets us represent multidimensional data to allow for nested scatter-gather,
e.g. scatter-scatter-gather-gather, where the layers of scatter are maintained as 
distinct.
"""

class IndexOutOfRangeError(Exception):
    pass
class DegreeOutOfRangeError(Exception):
    pass
class DegreeMismatchError(Exception):
    pass
class UnknownDegreeError(Exception):
    pass
class LeafDataAlreadyExistsError(Exception):
    pass
class RootDataAlreadyExistsError(Exception):
    pass
class UnexpectedLeafNodeError(Exception):
    pass
class ConnectError(Exception):
    pass


# value to be rendered for missing branches
PLACEHOLDER_VALUE = ''


class InputOutputNode(BasePolymorphicModel):
    channel = models.CharField(max_length=255)
    data_root = models.ForeignKey('DataNode',
                                  related_name='input_output_nodes',
                                  null=True)

    @property
    def data(self):
        # Return a string representation of the data tree
        if self.data_root is None:
            return json.dumps(PLACEHOLDER_VALUE)
        else:
            return json.dumps(self.data_root.render())

    def get_data_as_scalar(self):
        # This function is a temporary patch to run without parallel
        # workflows enabled.
        if not self.data_root:
            return None
        return self.data_root.data_object
        
    #def get_data_object(self, path):
        # Get the data object at the given path.
    #    return self.data_root.get_data_object(path)

    def _initialize_data_root(self):
        self.data_root = DataNode.objects.create()
        self.save()

    def add_data_object(self, path, data_object):
        # 'path' is a list of (index, degree) pairs that define a path from root to
        # leaf. For example, in this data
        # '[["file1.txt@id1", "file2.txt@id2"], ["file3.txt@id3", "file4.txt@id4"]]'
        # the path [(0, 2),(1, 2)], corresponds with the first (index 0) of 2 branches,
        # and the second of 2 leaves on that branch, i.e. 'file2.txt@id2'.
        # If path is length 0, data is assumed to be scalar
        if self.data_root is None:
            self._initialize_data_root()
        self.data_root.add_data_object(path, data_object)

    def add_data_objects_from_json(self, data_json, data_type):
        # data_json can be a string representation of a single value,
        # a list of strings, or a list of (lists of)^n strings. This
        # function will add each leaf data object at its corresponding path.
        # e.g. if data_json is "['10', '20']", for data_type 'integer',
        # we will add two data objects, with value 10 at path (0,2),
        # and value 20 at path (1,2)
        if self.data_root is None:
            self._initialize_data_root()
        self.data_root.add_data_objects_from_json(data_json, data_type)

    def is_connected(self, connected_node):
        if self.data_root is None or connected_node.data_root is None:
            return False
        return self.data_root.id == connected_node.data_root.id

    def connect(self, connected_node):
        # Nodes that share the same data should be connected,
        # e.g. a StepOutput that feeds into the StepInput of a subsequent step.

        if self.is_connected(connected_node):
            return

        # Both nodes are already initialized
        if connected_node.data_root is not None and self.data_root is not None:
            raise ConnectError('Failed to connect because nodes are already '\
                               'initialized with non-matching data')

        # If neither is initialized, initialize and connect
        if connected_node.data_root is None and self.data_root is None:
            connected_node._initialize_data_root()
            self.data_root = connected_node.data_root
            self.save()

        # If one is initialized, connect the other
        if self.data_root is None:
            self.data_root = connected_node.data_root
            self.save()
        elif connected_node.data_root is None:
            connected_node.data_root = self.data_root
            connected_node.save()


class DataNode(BaseModel):
    parent = models.ForeignKey(
        'DataNode',
        null=True,
        related_name = 'children')
    index = models.IntegerField(null=True) # 0 <= index < self.parent.degree; null if no parent
    degree = models.IntegerField(null=True) # expected number of children; null if leaf
    data_object = models.ForeignKey('DataObject',
                                    related_name = 'data_nodes',
                                    null=True) # null except on leaves

    def add_leaf(self, index, data_object):
        self._check_index(index)
        try:
            existing_leaf = self.children.get(index=index)
        except ObjectDoesNotExist:
            existing_leaf = None
        if existing_leaf is not None:
            raise LeafDataAlreadyExistsError(
                'Leaf data node already exists at this index')
        else:
            return DataNode.objects.create(
                parent=self,
                index=index,
                data_object=data_object)

    def add_branch(self, index, degree):
        self._check_index(index)
        if degree < 0:
            raise DegreeOutOfRangeError(
                'Degree %s is not allowed. Degree must be >= 0' % degree)
        try:
            existing_branch = self.children.get(index=index)
        except ObjectDoesNotExist:
            existing_branch = None
        if existing_branch is not None:
            if existing_branch.data_object is not None:
                raise UnexpectedLeafNodeError('Expected branch but found leaf')
            if existing_branch.degree != degree:
                raise DegreeMismatchError(
                    'Degree of branch conflicts with a value set previously')
            return existing_branch
        else:
            return DataNode.objects.create(
                parent=self,
                index=index,
                degree=degree)

    def add_data_object(self, path, data_object):
        if len(path) == 0:
            self._add_scalar_data_object(data_object)
        else:
            if self.degree is None:
                self.degree = path[0][1]
                self.save()
            self._extend_path_and_add_data_at_leaf(path, data_object)

    def _add_scalar_data_object(self, data_object):
        if not self._is_uninitialized():
            raise RootDataAlreadyExistsError(
                "Failed to add scalar data since the root DataNode is "\
                "already initialized")
        self.data_object = data_object
        self.save()

    def _is_uninitialized(self):
        return (self.degree is None
                and self.index is None
                and self.data_object is None)

    def _extend_path_and_add_data_at_leaf(self, path, data_object):
        index, degree = path.pop(0)
        assert self.degree == degree
        if len(path) == 0:
            self.add_leaf(index, data_object)
            return
        child_degree = path[0][1]
        child = self.add_branch(index, child_degree)
        child._extend_path_and_add_data_at_leaf(path, data_object)

    def _check_index(self, index):
        if self.degree is None:
            raise UnknownDegreeError(
                'Cannot add DataNode child to a parent with degree of None. '\
                'Set the degree on the parent first.')
        if index < 0 or index >= self.degree:
            raise IndexOutOfRangeError(
                'Out of range index %s. DataNode parent has degree %s, so index '\
                'should be in the range 0 to %s' % (
                    index, self.degree, self.degree-1))

    def _is_leaf(self):
        return self.degree is None and self.data_object is not None

    def add_data_objects_from_json(self, data_json, data_type):
        data = self._deserialize_data_json(data_json)
        path = []
        self._extend_all_paths_and_add_data_at_leaves(data, path, data_type)

    def _deserialize_data_json(self, data_json):
        # Convert '[["one","two"],"three"]' to [['one','two'],'three'].

        nested_lists_of_strings_schema = {
            # schema used to verify that data contains only a string,
            # a list of strings, or a list of (lists of)^n strings.
            # These are the only valid structures for user-provided data values,
            # e.g. 'file.txt@id',
            # '["file1.txt@id1", "file2.txt@id2"]', or
            # '[["file1.txt@id1", "file2.txt@id2"], ["file3.txt@id3"]]'.
            'oneOf': [
                { 'type': [ 'string' ] },
                { 'type': 'array', 'items': {'type': 'string'}},
                { 'type': 'array', 'items': {
                    'type': 'array', 'items': {'$ref': '#'}}},
            ]
        }
        try:
            data = json.loads(data_json)
        except ValueError:
            # assume data_json is a string representing a single value
            data = data_json
        try:
            jsonschema.validate(data, nested_lists_of_strings_schema)
        except jsonschema.exceptions.ValidationError:
            raise jsonschema.exceptions.ValidationError(
                "Data must be a string, list of strings, "\
                "or nested lists of strings with uniform depth. "\
                "Invalid data: '%s'" % data_json)
        return data

    def _extend_all_paths_and_add_data_at_leaves(self, data, path, data_type):
        # Recursive function that extends 'path' until reaching a leaf node,
        # where data is finally added.
        # 'path' is the partial path to some intermediate
        # node, while 'data' is the representation of all branches and leaves
        # beyond that path.
        # For example, given path (0,2) and data [['10','20']['30','40']],
        # the function places all data under (0,2) and ignores the other
        # root-level branch (1,2).
        # The function adds these four data objects at
        # their corresponding paths:
        # 10 at [(0,2), (0,2), (0,2)]
        # 20 at [(0,2), (0,2), (1,2)]
        # 30 at [(0,2), (1,2), (0,2)]
        # 40 at [(0,2), (1,2), (1,2)]
        if not isinstance(data, list):
            data_object = DataObject.get_by_value(
                data,
                data_type)
            self.add_data_object(path, data_object)
            return
        else:
            for i in range(len(data)):
                path_i = copy.deepcopy(path)
                path_i.append((i, len(data)))
                self._extend_all_paths_and_add_data_at_leaves(
                    data[i], path_i, data_type)

    def render(self):
        if self._is_uninitialized():
            return PLACEHOLDER_VALUE
        if self._is_leaf():
            return self.data_object.get_display_value()
        else:
            data = [PLACEHOLDER_VALUE] * self.degree
            for child in self.children.all():
                data[child.index] = child.render()
            return data

class InputNodeSet(object):
    """Set of nodes acting as inputs for one step.
    Each input node may have more than one DataObject,
    and DataObjects may arrive to the node at different times.
    An InputNodeSet corresponds to a single StepRun.
    """
    def __init__(self, input_nodes):
        self.input_nodes = input_nodes

    def get_ready_input_sets(self):
        # This is simplified and only handles scalar inputs
        for input_node in self.input_nodes:
            if not input_node.is_ready():
                return []
        return [InputSet(self.input_nodes)]

    def get_missing_inputs(self):
        missing = []
        for input_node in self.input_nodes:
            if not input_node.is_ready():
                missing.append(input_node)
        return missing


class InputItem(object):
    """A DataObject and its channel name"""

    def __init__(self, input_node):
        self.data_object = input_node.get_data_as_scalar()
        self.channel = input_node.channel


class InputSet(object):
    """An InputNodeSet can produce one or more InputSets, and each
    InputSet corresponds to a single TaskRun.
    """

    def __init__(self, input_nodes):
        self.input_items = [InputItem(i) for i in input_nodes]

    def __iter__(self):
        return self.input_items.__iter__()
