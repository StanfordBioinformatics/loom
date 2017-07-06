from django.test import TestCase

from api.test.models import _get_string_data_object
from api.models.data_nodes import *
from api.models.data_channels import *

from api.models.runs import RunOutput


class TestInputOutputNode(TestCase):

    def testAddDataObject(self):
        data_channel = RunOutput.objects.create(channel='test',
                                           mode='no_scatter', type='string')
        path = [(1,2), (0,1)]
        string_value = 'text'
        data_object = _get_string_data_object(string_value)
        data_channel.add_data_object(path, data_object)
        with self.assertRaises(MissingBranchError):
            data_channel.get_data_object([(0,2),(0,1)])
        self.assertEqual(
            data_channel.get_data_object([(1,2),(0,1)]).substitution_value,
            string_value)
 
    def testConnect(self):
        data_channel1 = RunOutput.objects.create(channel='test',
                                                mode='no_scatter', type='string')
        data_channel2 = RunOutput.objects.create(channel='test',
                                                mode='no_scatter', type='string')

        data_channel1.connect(data_channel2)
        self.assertEqual(data_channel1.data_node.id, data_channel2.data_node.id)

    def testIsConnected(self):
        data_channel1 = RunOutput.objects.create(channel='test',
                                                mode='no_scatter', type='string')
        data_channel2 = RunOutput.objects.create(channel='test',
                                                mode='no_scatter', type='string')
        self.assertFalse(data_channel1.is_connected(data_channel2))

        data_channel1.connect(data_channel2)
        self.assertTrue(data_channel1.is_connected(data_channel2))

    def testConnectError(self):
        data_channel1 = RunOutput.objects.create(channel='test',
                                                mode='no_scatter', type='string')
        data_channel2 = RunOutput.objects.create(channel='test',
                                                mode='no_scatter', type='string')

        data_channel1.initialize_data_node()
        data_channel2.initialize_data_node()

        with self.assertRaises(AssertionError):
            data_channel1.connect(data_channel2)
