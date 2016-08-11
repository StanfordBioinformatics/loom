from .base import BaseModel, BasePolymorphicModel
from django.db import models
from django.core.exceptions import ObjectDoesNotExist

from analysis.models.data_objects import DataObject
from analysis.fields import DuplicateManyToManyField

"""
Channels represent the path for flow of data between nodes (inputs and 
outputs). Channels have no state, and are just represented in the database 
as a ForeignKey relationship between receiver node and sender node.
"""


class InputOutputNode(BasePolymorphicModel):

    sender = models.ForeignKey('InputOutputNode',
                               related_name='receivers',
                               null=True)
    channel = models.CharField(max_length=255)

    def push(self, indexed_data_object):
        self.add_indexed_data_object(indexed_data_object.data_object)
        self.push_to_receivers(indexed_data_object)

    def push_all(self):
        for indexed_data_object in self.indexed_data_objects.all():
            self.push_to_receivers(indexed_data_object)

    def push_to_receivers(self, indexed_data_object):
        for receiver in self.receivers.all():
            receiver.push(indexed_data_object)

    def add_indexed_data_object(self, data_object):
        if self.indexed_data_objects.count() == 0:
            self.indexed_data_objects.add(
                IndexedDataObject.objects.create(
                    input_output_node = self,
                    data_object = data_object
                ))


class TypedInputOutputNode(InputOutputNode):

    type = models.CharField(
        max_length=255,
        choices=DataObject.TYPE_CHOICES
    )

    class Meta:
        abstract = True


class IndexedDataObject(BaseModel):
    """Embodies many-to-many relation between InputOutputNode and 
    DataObject. Tracks whether the DataObject index and wehther it has
    been used.
    """

    input_output_node = models.ForeignKey('InputOutputNode',
                                          related_name='indexed_data_objects')
    data_object = models.ForeignKey(
        'DataObject',
        related_name='indexed_data_object',
        on_delete=models.PROTECT,
        null=True)

    def is_ready(self):
        if self.data_object is None:
            return False
        return self.data_object.is_ready()

"""
class Index(BaseModel):
    indexed_data_object = models.ForeignKey('IndexedDataObject',
                                            related_name='indexes')
    dimension = models.IntegerField()
    position = models.IntegerField()
"""

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
        return InputSet(self.input_nodes)


class InputItem(object):
    """A DataObject and its channel name"""
    
    def __init__(self, input_node):
        self.data_object = input_node.pop()
        self.channel = input_node.channel


class InputSet(object):
    """An InputNodeSet can produce one or more InputSets, and each
    InputSet corresponds to a single TaskRun.
    """

    def __init__(self, input_nodes):
        self.input_items = [InputItem(i) for i in input_nodes]

    def __iter__(self):
        return self.input_items.__iter__()
