from django.test import TestCase

from api.test.models import _get_string_data_object
from api.models.data_nodes import *
from api.models.input_output_nodes import *

from api.models.runs import RunOutput


class TestInputOutputNode(TestCase):

    def testAddDataObject(self):
        io_node = RunOutput.objects.create(channel='test',
                                           mode='no_scatter', type='string')
        path = [(1,2), (0,1)]
        string_value = 'text'
        data_object = _get_string_data_object(string_value)
        io_node.add_data_object(path, data_object)
        with self.assertRaises(MissingBranchError):
            io_node.get_data_object([(0,2),(0,1)])
        self.assertEqual(
            io_node.get_data_object([(1,2),(0,1)]).substitution_value,
            string_value)
 
    def testConnect(self):
        io_node1 = RunOutput.objects.create(channel='test',
                                                mode='no_scatter', type='string')
        io_node2 = RunOutput.objects.create(channel='test',
                                                mode='no_scatter', type='string')

        io_node1.connect(io_node2)
        self.assertEqual(io_node1.data_node.id, io_node2.data_node.id)

    def testIsConnected(self):
        io_node1 = RunOutput.objects.create(channel='test',
                                                mode='no_scatter', type='string')
        io_node2 = RunOutput.objects.create(channel='test',
                                                mode='no_scatter', type='string')
        self.assertFalse(io_node1.is_connected(io_node2))

        io_node1.connect(io_node2)
        self.assertTrue(io_node1.is_connected(io_node2))

    def testConnectError(self):
        io_node1 = RunOutput.objects.create(channel='test',
                                                mode='no_scatter', type='string')
        io_node2 = RunOutput.objects.create(channel='test',
                                                mode='no_scatter', type='string')

        io_node1._initialize_data_node()
        io_node2._initialize_data_node()

        with self.assertRaises(AssertionError):
            io_node1.connect(io_node2)
