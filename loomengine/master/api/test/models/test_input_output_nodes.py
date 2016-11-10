from django.test import TestCase
import json
import jsonschema

from api.models.data_objects import *
from api.models.input_output_nodes import *


# Value used to represent missing values in rendered data
PLACEHOLDER_VALUE = {}

def _get_string_data_object(text):
    return StringDataObject.objects.create(
        type='string',
        value=text
    )

class TestInputOutputNode(TestCase):

    def testAddDataObjects(self):
        data = [["i"], ["a", "m"], ["r", "o", "b", "o", "t"]]
        io_node = InputOutputNode.objects.create(channel='test')
        io_node.add_data_objects(data, 'string')
        # Spot check
        self.assertEqual(io_node.to_data_struct()[0][0]['value'], data[0][0])
        self.assertEqual(io_node.to_data_struct()[2][3]['value'], data[2][3])
        
    def testAddDataObject(self):
        io_node = InputOutputNode.objects.create(channel='test')
        path = [(1,2), (0,1)]
        data_object = _get_string_data_object('text')
        io_node.add_data_object(path, data_object)
        self.assertEqual(io_node.to_data_struct()[0], PLACEHOLDER_VALUE)
        self.assertEqual(io_node.to_data_struct()[1][0]['value'], 'text')

    def testConnect(self):
        io_node1 = InputOutputNode.objects.create(channel='test')
        io_node2 = InputOutputNode.objects.create(channel='test')

        io_node1.connect(io_node2)
        self.assertEqual(io_node1.data_root.id, io_node2.data_root.id)

    def testIsConnected(self):
        io_node1 = InputOutputNode.objects.create(channel='test')
        io_node2 = InputOutputNode.objects.create(channel='test')
        self.assertFalse(io_node1.is_connected(io_node2))

        io_node1.connect(io_node2)
        self.assertTrue(io_node1.is_connected(io_node2))

    def testConnectError(self):
        io_node1 = InputOutputNode.objects.create(channel='test')
        io_node2 = InputOutputNode.objects.create(channel='test')

        io_node1._initialize_data_root()
        io_node2._initialize_data_root()

        with self.assertRaises(ConnectError):
            io_node1.connect(io_node2)

    def testDataPropertyWithNoDataRoot(self):
        io_node = InputOutputNode.objects.create(channel='test')
        self.assertEqual(io_node.to_data_struct(), PLACEHOLDER_VALUE)
        
class TestDataNode(TestCase):

    def testAddDataObject(self):
        input_data=(
            ([(0,3),(0,1)], 'i'),
            ([(1,3),(0,2)], 'a'),
            ([(1,3),(1,2)], 'm'),
            ([(2,3),(0,5)], 'r'),
            ([(2,3),(1,5)], 'o'),
            ([(2,3),(2,5)], 'b'),
            ([(2,3),(3,5)], 'o'),
            ([(2,3),(4,5)], 't'),
        )
        
        root = DataNode.objects.create()
        
        for path, letter in input_data:
            data_object = _get_string_data_object(letter)
            root.add_data_object(path, data_object)

        # spot check [['i'],['a','m'],['r','o','b','o','t']]
        output_data = root.to_data_struct()
        self.assertEqual(output_data[0][0]['value'], 'i')
        self.assertEqual(output_data[1][0]['value'], 'a')
        self.assertEqual(output_data[1][1]['value'], 'm')
        self.assertEqual(output_data[2][4]['value'], 't')

    def testRenderWithMissingData(self):
        input_data=(
            ([(0,3),(0,1)], 'i'),
            #([(1,3),(0,2)], 'a'),
            #([(1,3),(1,2)], 'm'),
            ([(2,3),(0,5)], 'r'),
            #([(2,3),(1,5)], 'o'),
            ([(2,3),(2,5)], 'b'),
            ([(2,3),(3,5)], 'o'),
            ([(2,3),(4,5)], 't'),
        )

        root = DataNode.objects.create()
        
        for path, letter in input_data:
            data_object = _get_string_data_object(letter)
            root.add_data_object(path, data_object)

        # spot check [['i'],['a','m'],['r','o','b','o','t']]
        output_data = root.to_data_struct()
        self.assertEqual(output_data[0][0]['value'], 'i')
        self.assertEqual(output_data[1], PLACEHOLDER_VALUE)
        self.assertEqual(output_data[2][1], PLACEHOLDER_VALUE)
        self.assertEqual(output_data[2][4]['value'], 't')

    def testRenderUninitialized(self):
        root = DataNode.objects.create()
        self.assertEqual(root.to_data_struct(), PLACEHOLDER_VALUE)
        
    def testAddScalarDataObject(self):
        root = DataNode.objects.create()
        text = 'text'
        data_object = _get_string_data_object(text)
        path = []
        root.add_data_object(path, data_object)
        self.assertEqual(root.to_data_struct()['value'], text)
        
    def testAddScalarDataObjectTwice(self):
        root = DataNode.objects.create()
        text = 'text'
        data_object = _get_string_data_object(text)
        path = []
        root.add_data_object(path, data_object)
        with self.assertRaises(RootDataAlreadyExistsError):
            root.add_data_object(path, data_object)
        
    def testAddBranchTwice(self):
        root = DataNode.objects.create(degree=2)
        branch1 = root.add_branch(1, 1)
        branch2 = root.add_branch(1, 1)
        self.assertEqual(branch1.id, branch2.id)

    def testAddBranchOverLeaf(self):
        root = DataNode.objects.create(degree=2)
        data_object = _get_string_data_object('text')
        root.add_leaf(1, data_object)
        with self.assertRaises(UnexpectedLeafNodeError):
            root.add_branch(1, 1)

    def testAddLeafOverBranch(self):
        root = DataNode.objects.create(degree=2)
        data_object = _get_string_data_object('text')
        root.add_leaf(1, data_object)
        with self.assertRaises(UnexpectedLeafNodeError):
            root.add_branch(1, 1)

    def testAddLeafTwice(self):
        root = DataNode.objects.create(degree=1)
        data_object = _get_string_data_object('text')
        root.add_leaf(0, data_object)
        with self.assertRaises(LeafDataAlreadyExistsError):
            root.add_leaf(0, data_object)

    def testAddDataObjects(self):
        data = [["i"],["a","m"],["r","o","b","o","t"]]
        root = DataNode.objects.create()
        root.add_data_objects(data, 'string')
        # spot check [['i'],['a','m'],['r','o','b','o','t']]
        output_data = root.to_data_struct()
        self.assertEqual(output_data[0][0]['value'], 'i')
        self.assertEqual(output_data[1][0]['value'], 'a')
        self.assertEqual(output_data[1][1]['value'], 'm')
        self.assertEqual(output_data[2][4]['value'], 't')

    def testAddDataObjectsWithString(self):
        root = DataNode.objects.create()
        input_string = 'just a string'
        root.add_data_objects(input_string, 'string')
        self.assertEqual(root.to_data_struct()['value'], input_string)

    def testIndexOutOfRangeError(self):
        degree = 2
        data_object = _get_string_data_object('text')
        root = DataNode.objects.create(degree=degree)
        with self.assertRaises(IndexOutOfRangeError):
            root.add_leaf(degree, data_object)
        with self.assertRaises(IndexOutOfRangeError):
            root.add_leaf(-1, data_object)

    def testDegreeOutOfRangeError(self):
        data_object = _get_string_data_object('text')
        root = DataNode.objects.create(degree=2)
        with self.assertRaises(DegreeOutOfRangeError):
            root.add_branch(1, -1)

    def testDegreeMismatchError(self):
        data_object = _get_string_data_object('text')
        root = DataNode.objects.create(degree=2)
        root.add_branch(1, 2)
        with self.assertRaises(DegreeMismatchError):
            root.add_branch(1, 3)
        
    def testUnknownDegreeError(self):
        data_object = _get_string_data_object('text')
        root = DataNode.objects.create()
        with self.assertRaises(UnknownDegreeError):
            root.add_leaf(0, data_object)

    def testValidationError(self):
        root = DataNode.objects.create()
        data = [[["string"],[{"not": "string"}]]]
        with self.assertRaises(jsonschema.exceptions.ValidationError):
            root.add_data_objects(data, 'string')
