from django.test import TestCase
from analysis.models.channels import Channel, ChannelOutput
from analysis.models.data_objects import DataObject
from .fixtures.channels import *
from .fixtures.data_objects import *
from .common import UniversalModelTestMixin

class TestChannel(TestCase, UniversalModelTestMixin):

    def testChannelOutputModel(self):
        o = ChannelOutput.create(channel_output_struct)
        self.roundTripJson(o)
        self.roundTripStruct(o)

    def testChannelModel(self):
        o = Channel.create(channel_struct)
        self.roundTripJson(o)
        self.roundTripStruct(o)

    def testAddDataObject(self):
        do = DataObject.create(file_struct_2)
        channel = Channel.create(channel_struct)
        old_count = channel.channel_outputs.first().data_objects.count()

        channel.add_data_object(do)

        count = channel.channel_outputs.first().data_objects.count()
        self.assertEqual(count, old_count+1)
