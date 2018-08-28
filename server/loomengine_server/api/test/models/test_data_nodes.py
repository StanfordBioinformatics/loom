from django.core.exceptions import ValidationError
from django.test import TestCase

from api.test.models import _get_string_data_object
from api.models.data_nodes import *


class TestDataNode(TestCase):

    INPUT_DATA=(
        ([(0,3),(0,1)], 'i'),
        ([(1,3),(0,2)], 'a'),
        ([(1,3),(1,2)], 'm'),
        ([(2,3),(0,5)], 'r'),
        ([(2,3),(1,5)], 'o'),
        ([(2,3),(2,5)], 'b'),
        ([(2,3),(3,5)], 'o'),
        ([(2,3),(4,5)], 't'),
    )

    def getTree(self, data):
        root = DataNode.objects.create(type='string')
        self.addData(root, data)
        return root

    def addData(self, root, data):
        for data_path, value in data:
            data_object = _get_string_data_object(value)
            root.add_data_object(data_path, data_object)

    def testAddDataObject(self):
        root = self.getTree(self.INPUT_DATA)

        # spot check [['i'],['a','m'],['r','o','b','o','t']]
        self.assertEqual(root.get_data_object([(0,3),(0,1)]).substitution_value, 'i')
        self.assertEqual(root.get_data_object([(1,3),(0,2)]).substitution_value, 'a')
        self.assertEqual(root.get_data_object([(1,3),(1,2)]).substitution_value, 'm')
        self.assertEqual(root.get_data_object([(2,3),(4,5)]).substitution_value, 't')

        # Verify that we get the same result after saving
        self.assertTrue(root.get_children()[0].id is None)
        root.save_with_children()
        self.assertEqual(root.get_data_object([(0,3),(0,1)]).substitution_value, 'i')
        self.assertEqual(root.get_data_object([(1,3),(0,2)]).substitution_value, 'a')
        self.assertEqual(root.get_data_object([(1,3),(1,2)]).substitution_value, 'm')
        self.assertEqual(root.get_data_object([(2,3),(4,5)]).substitution_value, 't')
        self.assertTrue(root.get_children()[0].id is not None)

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

        root = self.getTree(input_data)

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
        with self.assertRaises(NodeAlreadyExistsError):
            root.add_leaf(0, data_object)

    def testIndexOutOfRangeError(self):
        degree = 2
        data_object = _get_string_data_object('text')
        root = DataNode.objects.create(degree=degree, type='string')
        with self.assertRaises(IndexOutOfRangeError):
            root.add_leaf(degree, data_object)
        with self.assertRaises(IndexOutOfRangeError):
            root.add_leaf(-1, data_object)

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

        root = self.getTree(some_of_the_data)

        self.assertFalse(root.is_ready([]))
        self.assertFalse(root.is_ready([(2,3),]))
        self.assertFalse(root.is_ready([(2,3),(3,5)]))
        self.assertTrue(root.is_ready([(0,3),]))
        self.assertTrue(root.is_ready([(0,3),(0,1)]))

        self.addData(root, the_rest_of_the_data)
            
        self.assertTrue(root.is_ready([]))
        self.assertTrue(root.is_ready([(2,3),]))
        self.assertTrue(root.is_ready([(2,3),(3,5)]))
        self.assertTrue(root.is_ready([(0,3),]))
        self.assertTrue(root.is_ready([(0,3),(0,1)]))

    def testClone(self):
        tree1 = self.getTree(self.INPUT_DATA)
        child1 = tree1.get_node([(2,3)])
        grandchild1 = tree1.get_node([(2,3),(4,5)])

        tree2 = tree1.clone()
        child2 = tree2.get_node([(2,3)])
        grandchild2 = tree2.get_node([(2,3),(4,5)])

        self.assertEqual(grandchild1.data_object.uuid, grandchild2.data_object.uuid)

        self.assertNotEqual(tree1.uuid, tree2.uuid)
        self.assertNotEqual(child1.uuid, child2.uuid)
        self.assertNotEqual(grandchild1.uuid, grandchild2.uuid)

    def testClone_withSeed(self):
        tree1 = self.getTree(self.INPUT_DATA)
        child1 = tree1.get_node([(2,3)])
        grandchild1 = tree1.get_node([(2,3),(4,5)])

        tree2 = DataNode.objects.create(type='string')

        tree1.clone(seed=tree2)
        child2 = tree2.get_node([(2,3)])
        grandchild2 = tree2.get_node([(2,3),(4,5)])

        self.assertEqual(grandchild1.data_object.uuid, grandchild2.data_object.uuid)

        self.assertNotEqual(tree1.uuid, tree2.uuid)
        self.assertNotEqual(child1.uuid, child2.uuid)
        self.assertNotEqual(grandchild1.uuid, grandchild2.uuid)
        
    def testClone_leaf(self):
        leaf = DataNode.objects.create(type='string')
        leaf.add_data_object(
            [], _get_string_data_object(
                'al ultimo se lo estan comiendo las hormigas'))
        clone = leaf.clone()
        self.assertNotEqual(leaf.uuid, clone.uuid)
        self.assertEqual(leaf.data_object.uuid, clone.data_object.uuid)

    def testFlattenedClone(self):
        tree1 = self.getTree(self.INPUT_DATA)
        penult_grandchild1 = tree1.get_node([(2,3),(3,5)])
        last_grandchild1 = tree1.get_node([(2,3),(4,5)])

        tree2 = tree1.flattened_clone()
        penult_child2 = tree2.get_node([(6,8)])
        last_child2 = tree2.get_node([(7,8)])

        self.assertEqual(penult_grandchild1.data_object.uuid,
                         penult_child2.data_object.uuid)
        self.assertEqual(last_grandchild1.data_object.uuid,
                         last_child2.data_object.uuid)

        self.assertNotEqual(tree1.uuid, tree2.uuid)
        self.assertNotEqual(penult_grandchild1.uuid, penult_child2.uuid)
        self.assertNotEqual(last_grandchild1.uuid, last_child2.uuid)
        
    def testFlattenedClone_leaf(self):
        leaf = DataNode.objects.create(type='string')
        leaf.add_data_object(
            [], _get_string_data_object(
                'al ultimo se lo estan comiendo las hormigas'))
        clone = leaf.flattened_clone()
        self.assertNotEqual(leaf.uuid, clone.uuid)
        self.assertEqual(leaf.data_object.uuid, clone.data_object.uuid)

    def testGetOrCreateNode_existing(self):
        tree = self.getTree(self.INPUT_DATA)

        # If node exists, return it.
        old_node = tree.get_node([(2,3),(3,5)])
        node = tree.get_or_create_node([(2,3),(3,5)])
        self.assertEqual(old_node.uuid, node.uuid)

    def testGetOrCreateNode_created(self):
        tree = DataNode.objects.create(type='string')

        # If node does not exist, create a path to it.
        node = tree.get_or_create_node([(2,3),(3,5)])
        new_node = tree.get_node([(2,3),(3,5)])
        self.assertEqual(new_node.uuid, node.uuid)

    def testCalculateContentsFingerprint(self):
        node = self.getTree(self.INPUT_DATA)
        self.assertEqual(
            node.calculate_contents_fingerprint(),
            'd7405829b255d1dd4af90780a4b20286')

    def testCalculateContentsFingerprintOrderMatters(self):
        swapped_order_input_data=(
            ([(0,3),(0,1)], 'i'),
            ([(1,3),(0,2)], 'a'),
            ([(1,3),(1,2)], 'm'),
            ([(2,3),(0,5)], 'r'),
            ([(2,3),(1,5)], 'o'),
            ([(2,3),(2,5)], 'b'),
            ([(2,3),(3,5)], 't'), # order swapped
            ([(2,3),(4,5)], 'o'), # order swapped
        )
        node1 = self.getTree(self.INPUT_DATA)
        node2 = self.getTree(swapped_order_input_data)
        
        self.assertNotEqual(
            node1.calculate_contents_fingerprint(),
            node2.calculate_contents_fingerprint())
