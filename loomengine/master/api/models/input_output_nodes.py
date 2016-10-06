import copy
import json
import jsonschema

from .base import BaseModel, BasePolymorphicModel
from django.db import models
from django.core.exceptions import ObjectDoesNotExist

from api.models.data_objects import DataObject

"""
InputOutputNodes are connected to facilitate the flow of data in a workflow, e.g. from a 
WorkflowRunInput to the StepRunInput of a StepRun nested in that Workflow, or from a 
StepRunOutput to the StepRunInput of a subsequent Step.
InputOutputNode is inherited by all input/output classes that may need to handle 
data trees with height > 1 (RunRequestInput, WorkflowRunInput/Output, StepRunInput/Output)
but not by TaskRuns, TaskRunAttempts, or TaskDefinitions since these only contain data as 
scalars or 1-dimensional arrays.

Data under each InputOutputNode is represented as a tree of DataNodes. This
lets us represent multidimensional data to allow for nested scatter-gather,
e.g. scatter-scatter-gather-gather, where the layers of scatter are maintained as distinct.
"""

class IndexOutOfRangeError(Exception):
    pass
class DegreeOutOfRangeError(Exception):
    pass
class UnknownDegreeError(Exception):
    pass

nested_lists_of_strings_schema = {
        'oneOf': [
                    { 'type': [ 'string' ] },
                    { 'type': 'array', 'items': {'type': 'string'}},
                    { 'type': 'array', 'items': {'type': 'array', 'items': {'$ref': '#'}}},
                ]
    }

class InputOutputNode(BasePolymorphicModel):
    sender = models.ForeignKey('InputOutputNode',
                               related_name='receivers',
                               null=True)
    channel = models.CharField(max_length=255)
    data_root = models.ForeignKey('DataNode',
                                  related_name='input_output_node',
                                  null=True)
    @property
    def data(self):
        if self.data_root is None:
            return ''
        else:
            return json.dumps(self.data_root.render())

    def add_data_object(self, path, data_object):
        # path is a list of (index, degree) pairs that define a path from root to leaf
        if len(path) == 0:
            self._add_scalar_data_object(data_object)
        else:
            if self.data_root is None:
                root_degree = path[0][1]
                self.data_root = DataNode.objects.create(degree=root_degree)
                self.save()
            self.data_root.add_path(path, data_object)

    def _add_scalar_data_object(self, data_object):
        if self.data_root is not None:
            raise Exception('Tried to add scalar data object but data already exists. Refusing to overwrite.')
        self.data_root = DataNode.objects.create(data_object=data_object)
        self.save()

    def add_data_objects_from_json(self, data_json, data_type):
        try:
            data = json.loads(data_json)
        except ValueError:
            raise Exception("data is not a valid json: '%s'" % data_json)
        try:
            jsonschema.validate(data, nested_lists_of_strings_schema)
        except jsonschema.exceptions.ValidationError:
            raise Exception("Data must be a string, list of strings, or nested lists of strings with uniform depth. Invalid data: '%s'" % data_json)

        path = []
        self._extend_all_paths_and_add_data_objects(data, path, data_type)

    def _extend_all_paths_and_add_data_objects(self, data, path, data_type):
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
                self._extend_all_paths_and_add_data_objects(data[i], path_i, data_type)


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
        return DataNode.objects.create(
            parent=self,
            index=index,
            data_object=data_object)

    def add_branch(self, index, degree):
        self._check_index(index)
        if degree < 0:
            raise DegreeOutOfRangeError('Degree %s is not allowed. Degree must be greater than 0' % degree)
        try:
            existing_branch = self.children.get(index=index)
        except ObjectDoesNotExist:
            existing_branch = None
        if existing_branch is not None:
            assert existing_branch.degree == degree
            return existing_branch
        else:
            return DataNode.objects.create(
                parent=self,
                index=index,
                degree=degree)

    def add_path(self, path, data_object):
        index, degree = path.pop(0)
        assert self.degree == degree
        if len(path) == 0:
            self.add_leaf(index, data_object)
            return
        child_degree = path[0][1]
        child = self.add_branch(index, child_degree)
        child.add_path(path, data_object)

    def _check_index(self, index):
        if self.degree is None:
            raise UnknownDegreeError(
                'Cannot add DataNode child to a parent with degree of None. Set the degree on the parent first.')
        if index < 0 or index >= self.degree:
            raise IndexOutOfRangeError(
                'Out of range index %s. DataNode parent has degree %s, so index should be in the range 0 to %s' % (
                    index, self.degree, self.degree-1))

    def is_leaf(self):
        return self.degree is None

    def render(self):
        if self.is_leaf():
            return self.data_object.get_display_value()
        else:
            return [child.render() for child in self.children.order_by('index').all()]

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
        self.data_object = input_node.indexed_data_objects.first().data_object
        self.channel = input_node.channel


class InputSet(object):
    """An InputNodeSet can produce one or more InputSets, and each
    InputSet corresponds to a single TaskRun.
    """

    def __init__(self, input_nodes):
        self.input_items = [InputItem(i) for i in input_nodes]

    def __iter__(self):
        return self.input_items.__iter__()

