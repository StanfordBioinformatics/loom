from django.core.exceptions import ValidationError
from django.test import TestCase

from api.test.models import _get_string_data_object
from api.models.data_nodes import *


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
        
        root = DataNode.objects.create(type='string')
        
        for data_path, letter in input_data:
            data_object = _get_string_data_object(letter)
            root.add_data_object(data_path, data_object)

        # spot check [['i'],['a','m'],['r','o','b','o','t']]
        self.assertEqual(root.get_data_object([(0,3),(0,1)]).substitution_value, 'i')
        self.assertEqual(root.get_data_object([(1,3),(0,2)]).substitution_value, 'a')
        self.assertEqual(root.get_data_object([(1,3),(1,2)]).substitution_value, 'm')
        self.assertEqual(root.get_data_object([(2,3),(4,5)]).substitution_value, 't')

    def testMissingData(self):
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

        root = DataNode.objects.create(type='string')
        
        for data_path, letter in input_data:
            data_object = _get_string_data_object(letter)
            root.add_data_object(data_path, data_object)

        # spot check [['i'],['a','m'],['r','o','b','o','t']]
        self.assertEqual(root.get_data_object([(0,3),(0,1)]).substitution_value, 'i')
        with self.assertRaises(MissingBranchError):
            root.get_data_object([(1,3),])
        with self.assertRaises(MissingBranchError):
            root.get_data_object([(2,3),(1,5)])
        self.assertEqual(root.get_data_object([(2,3),(4,5)]).substitution_value, 't')

    def testAddScalarDataObject(self):
        root = DataNode.objects.create(type='string')
        text = 'text'
        data_object = _get_string_data_object(text)
        data_path = []
        root.add_data_object(data_path, data_object)
        self.assertEqual(root.get_data_object(data_path).substitution_value, text)
        
    def testAddScalarDataObjectTwice(self):
        root = DataNode.objects.create(type='string')
        text = 'text'
        data_object = _get_string_data_object(text)
        data_path = []
        root.add_data_object(data_path, data_object)
        with self.assertRaises(DataAlreadyExistsError):
            root.add_data_object(data_path, data_object)
        
    def testAddBranchTwice(self):
        root = DataNode.objects.create(degree=2, type='string')
        branch1 = root.add_branch(1, 1)
        branch2 = root.add_branch(1, 1)
        self.assertEqual(branch1.id, branch2.id)

    def testAddBranchOverLeaf(self):
        root = DataNode.objects.create(degree=2, type='string')
        data_object = _get_string_data_object('text')
        root.add_leaf(1, data_object)
        with self.assertRaises(UnexpectedLeafNodeError):
            root.add_branch(1, 1)

    def testAddLeafOverBranch(self):
        root = DataNode.objects.create(degree=2, type='string')
        data_object = _get_string_data_object('text')
        root.add_leaf(1, data_object)
        with self.assertRaises(UnexpectedLeafNodeError):
            root.add_branch(1, 1)

    def testAddLeafTwice(self):
        root = DataNode.objects.create(degree=1, type='string')
        data_object = _get_string_data_object('text')
        root.add_leaf(0, data_object)
        with self.assertRaises(LeafAlreadyExistsError):
            root.add_leaf(0, data_object)

    def testIndexOutOfRangeError(self):
        degree = 2
        data_object = _get_string_data_object('text')
        root = DataNode.objects.create(degree=degree, type='string')
        with self.assertRaises(IndexOutOfRangeError):
            root.add_leaf(degree, data_object)
        with self.assertRaises(IndexOutOfRangeError):
            root.add_leaf(-1, data_object)

    def testDegreeOutOfRangeError(self):
        data_object = _get_string_data_object('text')
        root = DataNode.objects.create(degree=2, type='string')
        with self.assertRaises(ValidationError):
            root.add_branch(1, -1)

    def testDegreeMismatchError(self):
        data_object = _get_string_data_object('text')
        root = DataNode.objects.create(degree=2, type='string')
        root.add_branch(1, 2)
        with self.assertRaises(DegreeMismatchError):
            root.add_branch(1, 3)
        
    def testUnknownDegreeError(self):
        data_object = _get_string_data_object('text')
        root = DataNode.objects.create(type='string')
        with self.assertRaises(UnknownDegreeError):
            root.add_leaf(0, data_object)

    def testIsReady(self):
        some_of_the_data=(
            ([(0,3),(0,1)], 'i'),
            ([(1,3),(0,2)], 'a'),
            ([(2,3),(0,5)], 'r'),
            ([(2,3),(1,5)], 'o'),
            ([(2,3),(2,5)], 'b'),
            ([(2,3),(4,5)], 't'),
        )

        the_rest_of_the_data = (
            ([(2,3),(3,5)], 'o'),
            ([(1,3),(1,2)], 'm'),
        )
        
        root = DataNode.objects.create(type='string')
        
        for data_path, letter in some_of_the_data:
            data_object = _get_string_data_object(letter)
            root.add_data_object(data_path, data_object)

        self.assertFalse(root.is_ready([]))
        self.assertFalse(root.is_ready([(2,3),]))
        self.assertFalse(root.is_ready([(2,3),(3,5)]))
        self.assertTrue(root.is_ready([(0,3),]))
        self.assertTrue(root.is_ready([(0,3),(0,1)]))

        for data_path, letter in the_rest_of_the_data:
            data_object = _get_string_data_object(letter)
            root.add_data_object(data_path, data_object)
            
        self.assertTrue(root.is_ready([]))
        self.assertTrue(root.is_ready([(2,3),]))
        self.assertTrue(root.is_ready([(2,3),(3,5)]))
        self.assertTrue(root.is_ready([(0,3),]))
        self.assertTrue(root.is_ready([(0,3),(0,1)]))
