from django.db import models
from .base import AnalysisAppInstanceModel
from .data_objects import DataObject
from .workflow_runs import InputOutput
from universalmodels import fields

"""
This module defines Channels for passing data between inputs/outputs of steps or workflows
"""


class Channel(AnalysisAppInstanceModel):
    """Channel acts as a queue for data being being passed into or out of steps or workflows.
    """

    name = fields.CharField(max_length=255)
    outputs = fields.OneToManyField('ChannelOutput')
    sender = fields.OneToOneField('InputOutput', related_name='to_channel', null=True)
    is_closed_to_new_data = fields.BooleanField(default=False)

    @classmethod
    def create_from_sender(cls, sender, channel_name):
        channel = cls.create({'name': channel_name})
        channel.sender = sender
        channel.save()
        return channel
    
    def push(self, data_object):
        for output in self.outputs.all():
            output.push(data_object)

    def add_receivers(self, receivers):
        for receiver in receivers:
            self.add_receiver(receiver)

    def add_receiver(self, receiver):
        output = ChannelOutput.create({})
        output.receiver = receiver
        output.save()
        self.outputs.add(output)

    def close(self):
        self.update({'is_closed_to_new_data': True})


class ChannelOutput(AnalysisAppInstanceModel):
    """Every channel can have only one source but 0 or many destinations, representing
    the possibility that a file produce by one step can be used by 0 or many other 
    steps. Each of these destinations has its own queue, implemented as a ChannelOutput.
    """

    data_objects = fields.ManyToManyField('DataObject')
    receiver = fields.OneToOneField('InputOutput', related_name='from_channel', null=True)

    def push(self, data_object):
        self.data_objects.add(data_object)
        self.receiver.push()

    def is_empty(self):
        return self.data_objects.count() == 0

    def is_dead(self):
        return self.channel.is_closed_to_new_data and self.is_empty()

    def pop(self):
        data_object = self.data_objects.first()
        self.data_objects = self.data_objects.all()[1:]
        return data_object.downcast()
