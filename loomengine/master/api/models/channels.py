from .base import BaseModel, BasePolymorphicModel
from django.db import models
from django.core.exceptions import ObjectDoesNotExist

from api.models.data_objects import DataObject

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

    @property
    def value(self):
        if self.indexed_data_objects.count() == 0:
            return ''
        elif self.indexed_data_objects.count() > 1:
            raise Exception("Can't handle more than one input")
        return self.indexed_data_objects.first().get_display_value()

    def push(self, *args):
        # Calling push() with no arguments, it will push all data to receivers.
        # If you call push() with an item, it will register that item to this node and
        # push it to all receivers.
        # The item may be either a data_object or an indexed_data_object.
        if args:
            if len(args) > 1:
                raise Exception
            item = args[0]
            try:
                # If it's an indexed data object, retrieve the data object
                data_object = item.data_object
            except AttributeError:
                data_object = item
            indexed_data_object = self.add_indexed_data_object(data_object)
            self.push_items([indexed_data_object])
        else:
            self.push_items(self.indexed_data_objects.all())

    def push_items(self, indexed_data_objects):
        for indexed_data_object in indexed_data_objects:
            self.push_to_receivers(indexed_data_object)
        
    def push_to_receivers(self, indexed_data_object):
        for receiver in self.receivers.all():
            receiver.push(indexed_data_object)

    def add_indexed_data_object(self, data_object):
        if self.indexed_data_objects.count() > 0:
            # don't re-add if it was already added.
            assert data_object.id \
                == self.indexed_data_objects.first().data_object.id
            return self.indexed_data_objects.first()
        else:
            indexed_data_object = IndexedDataObject.objects.create(
                input_output_node = self,
                data_object = data_object
            )
            self.indexed_data_objects.add(indexed_data_object)
            return indexed_data_object

    def is_ready(self):
        # TODO - handle parallel
        try:
            return self.indexed_data_objects.first().is_ready()
        except AttributeError:
            return False


class IndexedDataObject(BaseModel):
    """Embodies many-to-many relation between InputOutputNode and 
    DataObject. Tracks whether the DataObject index.
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

    def get_display_value(self):
        if self.data_object is None:
            return ''
        return self.data_object.get_display_value()
        
    
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
