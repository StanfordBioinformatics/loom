from django.core.exceptions import ObjectDoesNotExist
from django.db import models

from analysis.models.base import AnalysisAppInstanceModel
from analysis.models.data_objects import DataObject
from universalmodels import fields

"""
This module defines Channels for passing data between inputs/outputs of steps or workflows
"""


class Channel(AnalysisAppInstanceModel):
    """Channel acts as a queue for data being being passed into or out of steps or workflows.
    """

    name = fields.CharField(max_length=255)
    outputs = fields.OneToManyField('ChannelOutput')
    data_objects = fields.ManyToManyField('DataObject')
    sender = fields.OneToOneField('InputOutputNode', related_name='to_channel', null=True)
    is_closed_to_new_data = fields.BooleanField(default=False)

    @classmethod
    def create_from_sender(cls, sender, channel_name):
        channel = cls.create({'name': channel_name})
        channel.sender = sender
        channel.save()
        return channel

    def push(self, data_object):
        if self.is_closed_to_new_data:
            return
        self.data_objects.add(data_object)
        for output in self.outputs.all():
            output._push(data_object)
        self.save()

    def add_receivers(self, receivers):
        for receiver in receivers:
            self.add_receiver(receiver)

    def add_receiver(self, receiver):
        output = ChannelOutput.create({
            # Typically data_objects is empty, we pass along any data_objects already
            # received for cases when a receiver is added after the run has progressed
            'data_objects': [do for do in self.data_objects.all()]
        })
        output.receiver = receiver
        output.save()
        self.outputs.add(output)

    def close(self):
        self.is_closed_to_new_data = True
        self.save()


class ChannelOutput(AnalysisAppInstanceModel):
    """Every channel can have only one source but 0 or many destinations, representing
    the possibility that a file produce by one step can be used by 0 or many other 
    steps. Each of these destinations has its own queue, implemented as a ChannelOutput.
    """

    data_objects = fields.ManyToManyField('DataObject')
    receiver = fields.OneToOneField('InputOutputNode', related_name='from_channel', null=True)

    def _push(self, data_object):
        self.data_objects.add(data_object)
        self.save()
        self.receiver.push(data_object)

    def is_empty(self):
        return self.data_objects.count() == 0

    def is_dead(self):
        return self.channel.is_closed_to_new_data and self.is_empty()

    def pop(self):
        data_object = self.data_objects.first()
        self.data_objects = self.data_objects.all()[1:]
        return data_object.downcast()

    def forward(self, to_channel):
        """Pass channel contents to the downstream channel
        """
        if not self.is_empty():
            to_channel.push(self.pop())

        if self.is_dead():
            to_channel.close()


class InputOutputNode(AnalysisAppInstanceModel):

    def push(self, *args, **kwargs):
        return self.downcast().push(*args, **kwargs)

    def has_destination(self, destination):
        try:
            return destination.from_channel.channel.sender._id == self._id
        except ObjectDoesNotExist:
            return False
            

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
