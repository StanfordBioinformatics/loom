from django.db import models
from .base import AnalysisAppInstanceModel
from .data import Data
from .workflow_runs import InputOutputNode
from universalmodels import fields

"""
This module defines Channels for passing data between inputs/outputs of steps or workflows
"""


class Channel(AnalysisAppInstanceModel):
    """Channel acts as a queue for data being being passed into or out of steps or workflows.
    """

    channel_name = fields.CharField(max_length=255)
    channel_outputs = fields.OneToManyField('ChannelOutput')
    sender = fields.OneToOneField('InputOutputNode', related_name='to_channel')
    is_closed_to_new_data = fields.BooleanField(default=False)

    @classmethod
    def create_from_sender(cls, sender):
        return cls.create({
            'sender': sender.to_struct(),
            'channel_name': sender.channel_name
        })
    
    def add_data(self, data):
        for output in self.channel_outputs.all():
            output._add_data(data)

    def add_receivers(self, receivers):
        for receiver in receivers:
            self.add_receiver(receiver)

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

    datas = fields.ManyToManyField('Data')
    receiver = fields.ForeignKey('InputOutputNode', related_name='from_channel')

    def _add_data(self, data):
        self.datas.add(data)
                
    def is_empty(self):
        return self.datas.count() == 0

    def is_dead(self):
        return self.channel.is_closed_to_new_data and self.is_empty()

    def pop(self):
        data = self.datas.first()
        self.datas = self.datas.all()[1:]
        return data
