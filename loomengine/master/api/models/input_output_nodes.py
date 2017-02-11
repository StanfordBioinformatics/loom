from .base import BaseModel
from django.db import models

from api.models.data_objects import DataObject
from api.models.data_trees import DataNode

"""
InputOutputNodes are connected to facilitate the flow of data in a workflow, e.g. from 
a WorkflowRunInput to the StepRunInput of a StepRun nested in that Workflow, or from a 
StepRunOutput to the StepRunInput of a subsequent Step.

InputOutputNode is inherited by all input/output classes that may need to handle 
data trees with height > 1 (RunRequestInput, WorkflowRunInput/Output, 
StepRunInput/Output) but not by TaskRuns, TaskRunAttempts, or TaskDefinitions since 
these only contain data as scalars or 1-dimensional arrays.
"""

class ConnectError(Exception):
    pass

class InputOutputNode(BaseModel):
    channel = models.CharField(max_length=255)
    data_root = models.ForeignKey('DataNode',
                                  null=True)

    type = models.CharField(
        max_length=255,
        choices=DataObject.TYPE_CHOICES)

    @property
    def data(self):
        # Dummy attribute required by serializers.
        # DataNodeSerializer is needed to render this field.
        # We don't implement that as a model method here to avoid
        # circular dependencies between models and serializers.
        # To access data directly use the data_root field instead.
        return

    def get_data_as_scalar(self):
        # This function is a temporary patch to run without parallel
        # workflows enabled.
        if not self.data_root:
            return None
        return self.data_root.data_object

    def add_data_as_scalar(self, data_object):
        self.add_data_object([], data_object)

    def get_data_object(self, path):
        # Get the data object at the given path.
        return self.data_root.get_data_object(path)

    def _initialize_data_root(self):
        self.data_root = DataNode.objects.create()
        self.data_root.root_node = self.data_root
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

    class Meta:
        abstract = True
        app_label = 'api'


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
        self.type = self.data_object.type
        self.channel = input_node.channel


class InputSet(object):
    """An InputNodeSet can produce one or more InputSets, and each
    InputSet corresponds to a single TaskRun.
    """

    def __init__(self, input_nodes):
        self.input_items = [InputItem(i) for i in input_nodes]

    def __iter__(self):
        return self.input_items.__iter__()
