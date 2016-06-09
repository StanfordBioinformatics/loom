from django.test import TestCase
from analysis.models.channels import Channel, ChannelOutput
from analysis.models.data_objects import DataObject
from . import fixtures
from .common import ModelTestMixin

class TestChannel(TestCase, ModelTestMixin):

    def testChannelOutputModel(self):
        o = ChannelOutput.create(fixtures.channel_output)
        self.roundTrip(o)

    def testChannelModel(self):
        o = Channel.create(fixtures.channel)
        self.roundTrip(o)

    def testAddDataObject(self):
        do = DataObject.create(fixtures.file_2)
        channel = Channel.create(fixtures.channel)
        old_count = channel.outputs.first().data_objects.count()

        channel.push(do)

        count = channel.outputs.first().data_objects.count()
        self.assertEqual(count, old_count+1)
