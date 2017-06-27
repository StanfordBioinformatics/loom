from django.db import models

from .base import BaseModel
from api.models.data_objects import DataObject
from api.models.data_nodes import DataNode


"""
InputOutputNodes are connected to facilitate the flow of data in a run, e.g. 
from one RunInput to the RunInput of a child Run, or from a 
RunOutput to the RunInput of a subsequent Run.

InputOutputNode is inherited by Run input/output classes, 
including RunRequest Input, but not by TaskRuns or TaskRunAttempts 
since these do not share the full data tree.
"""


class InputOutputNode(BaseModel):
    channel = models.CharField(max_length=255)
    data_node = models.ForeignKey('DataNode',
                                   # related_name would cause conflicts on children
                                  null=True,
                                  blank=True)
    type = models.CharField(
        max_length=255,
        choices=DataObject.DATA_TYPE_CHOICES)

    @property
    def data(self):
        # Dummy attribute required by serializers.
        # DataTreeNodeSerializer is needed to render this field.
        # We don't implement that as a model method here to avoid
        # circular dependencies between models and serializers.
        # To access data directly use the data_node field instead.
        return

    def get_data_object(self, data_path):
        # Get the data object at the given data_path.
        return self.data_node.get_data_object(data_path)

    def get_ready_data_nodes(self, seed_path, gather_depth):
        return self.data_node.get_ready_data_nodes(seed_path, gather_depth)
    
    def initialize_data_node(self):
        self.setattrs_and_save_with_retries(
            {'data_node': DataNode.objects.create(type=self.type)})

    def add_data_object(self, data_path, data_object):
        # 'data_path' is a list of (index, degree) pairs that define a path
        # from root to leaf. For example, in this data
        # '[["file1.txt@id1", "file2.txt@id2"], ["file3.txt@id3", "file4.txt@id4"]]'
        # the data_path [(0, 2),(1, 2)], corresponds with the first
        # (index 0) of 2 branches,
        # and the second of 2 leaves on that branch, i.e. 'file2.txt@id2'.
        # If data_path is length 0, data is scalar
        if self.data_node is None:
            self.initialize_data_node()
        self.data_node.add_data_object(data_path, data_object)

    def is_connected(self, connected_node):
        # Nodes are connected by sharing a common DataNode
        if self.data_node is None or connected_node.data_node is None:
            return False
        return self.data_node.id == connected_node.data_node.id

    def connect(self, connected_node):
        # Nodes that share the same data should be connected,
        # e.g. a RunOutput that feeds into the RunInput of a subsequent Run.

        if self.is_connected(connected_node):
            return

        # Types must match
        assert connected_node.type == self.type, \
            'Type mismatch, cannot connect nodes'

        # Nodes should not both already be initialized
        assert connected_node.data_node is None or self.data_node is None, \
            'Cannot connect. Both nodes already '\
            'initialized with non-matching data'

        # If neither is initialized, initialize and connect
        if connected_node.data_node is None and self.data_node is None:
            connected_node.initialize_data_node()
            self.data_node = connected_node.data_node
            self.save()
            return

        # If one is initialized, connect the other
        if self.data_node is None:
            self.data_node = connected_node.data_node
            self.save()
        elif connected_node.data_node is None:
            connected_node.data_node = self.data_node
            connected_node.save()

    class Meta:
        abstract = True
        app_label = 'api'
