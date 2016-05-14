from django.db import models
from .base import AnalysisAppInstanceModel
from .data_objects import DataObject
from .workflow_runs import InputOutputNode
from universalmodels import fields

"""
This module defines Channels for passing data between inputs/outputs of steps or workflows
"""


class Channel(AnalysisAppInstanceModel):
    """Channel acts as a queue for data objects being being passed into or out of steps or workflows.
    """

    channel_name = fields.CharField(max_length=255)
    channel_outputs = fields.OneToManyField('ChannelOutput')
    sender = fields.ForeignKey('InputOutputNode', related_name='to_channel')
    is_closed_to_new_data = fields.BooleanField(default=False)

    @classmethod
    def create_from_sender(cls, sender):
        return cls.create({
            'sender': sender.to_struct(),
            'channel_name': sender.channel_name
        })
    
    def add_data_object(self, data_object):
        for output in self.channel_outputs.all():
            output._add_data_object(data_object)

    def add_receiver(self, receiver):
        self.channel_outputs.add(
            ChannelOutput.create(
                {'receiver': receiver.to_struct()}
            )
        )

    def close(self):
        self.update({'is_closed_to_new_data': True})


class ChannelOutput(AnalysisAppInstanceModel):
    """Every channel can have only one source but 0 or many destinations, representing
    the possibility that a file produce by one step can be used by 0 or many other 
    steps. Each of these destinations has its own queue, implemented as a ChannelOutput.
    """

    data_objects = fields.ManyToManyField('DataObject')
    receiver = fields.ForeignKey('InputOutputNode', related_name='from_channel')

    def _add_data_object(self, data_object):
        self.data_objects.add(data_object)
                
    def is_empty(self):
        return self.data_objects.count() == 0

    def is_dead(self):
        return self.channel.is_closed_to_new_data and self.is_empty()

    def pop(self):
        data_object = self.data_objects.first()
        self.data_objects = self.data_objects.all()[1:]
        return data_object
