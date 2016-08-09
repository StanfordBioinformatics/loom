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

    sender = models.ForeignKey('InputOutputNode', related_name='receivers', null=True)
    channel = models.CharField(max_length=255)
    data_object = models.ForeignKey(
        'DataObject',
        related_name='input_output_nodes',
        on_delete=models.PROTECT,
        null=True)

    def push(self, *args, **kwargs):
        return self.downcast().push(*args, **kwargs)

class TypedInputOutputNode(InputOutputNode):

    type = models.CharField(
        max_length=255,
        choices=DataObject.TYPE_CHOICES
    )

    class Meta:
        abstract = True


class ChannelSet(object):

    def __init__(self, inputs):
        self._are_inputs_initialized = True
        self.channels = []
        for input in inputs:
            try:
                self.channels.append(input.from_channel)
            except ObjectDoesNotExist:
                self._are_inputs_initialized=False

    def get_ready_input_sets(self):
        if not self._are_inputs_initialized:
            return []
        else:
            for channel in self.channels:
                if channel.is_empty():
                    return []
            return [InputSet(self.channels)]


class InputItem(object):
    
    def __init__(self, channel):
        self.data_object = channel.pop()
        self.channel = channel.channel.name


class InputSet(object):

    def __init__(self, channels):
        self.input_items = [InputItem(c) for c in channels]

    def __iter__(self):
        return self.input_items.__iter__()
