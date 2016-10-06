from django.test import TestCase

from api.models.data_objects import *
from api.models.input_output_nodes import *


class TestDataNode(TestCase):

    def _get_string_data_object(self, text):
        return StringDataObject.objects.create(
            string_content=StringContent.objects.create(
                string_value=text
            )
        )
    
    def testScatterScatterGatherGather(self):
        input_text = 'i am robot'
        sentence = self._get_string_data_object(input_text)
        root1 = DataNode.objects.create(data_object=sentence)
        
        self.assertEqual(sentence.string_content.string_value, input_text)
        self.assertIsNone(root1.degree)
        self.assertIsNone(root1.index)
        self.assertEqual(root1.data_object.id, sentence.id)
        
        word_list = input_text.split(' ')
        root2 = DataNode.objects.create(degree = len(word_list))

        for i in range(len(word_list)):
            word_text = word_list[i]
            word = self._get_string_data_object(word_text)
            leaf = root2.add_leaf(i, word)
            self.assertEqual(leaf.data_object.id, word.id)

        root3 = DataNode.objects.create(degree=len(word_list))
        for i in range(len(word_list)):
            word_text = word_list[i]
            branch = root3.add_branch(i, len(word_text))
            for j in range(len(word_text)):
                letter_text = word_text[j]
                letter = self._get_string_data_object(letter_text)
                leaf = branch.add_leaf(j, letter)
                self.assertEqual(leaf.data_object.id, letter.id)

    def testRender(self):
        input_text = 'i am robot'
        word_list = input_text.split(' ')
        root = DataNode.objects.create(degree=len(word_list))
        for i in range(len(word_list)):
            word_text = word_list[i]
            branch = root.add_branch(i, len(word_text))
            for j in range(len(word_text)):
                letter_text = word_text[j]
                letter = self._get_string_data_object(letter_text)
                leaf = branch.add_leaf(j, letter)
                self.assertEqual(leaf.data_object.id, letter.id)

        data = root.render()

        self.assertEqual(data[0][0], 'i')
        self.assertEqual(data[2][4], 't')

    def testIndexOutOfRange(self):
        degree = 2
        data_object = self._get_string_data_object('text')
        root = DataNode.objects.create(degree=degree)
        with self.assertRaises(IndexOutOfRangeError):
            root.add_leaf(degree, data_object)
        with self.assertRaises(IndexOutOfRangeError):
            root.add_leaf(-1, data_object)

    def testUnknownParentDegree(self):
        data_object = self._get_string_data_object('text')
        root = DataNode.objects.create(degree=None)
        with self.assertRaises(UnknownDegreeError):
            root.add_leaf(0, data_object)

    def testAddPath(self):
        data=(
            ([(0,3),(0,1)], 'i'),
            ([(1,3),(0,2)], 'a'),
            ([(1,3),(1,2)], 'm'),
            ([(2,3),(0,5)], 'r'),
            ([(2,3),(1,5)], 'o'),
            ([(2,3),(2,5)], 'b'),
            ([(2,3),(3,5)], 'o'),
            ([(2,3),(4,5)], 't'),
        )
        
        io_node = InputOutputNode.objects.create()
        
        for path, letter in data:
            data_object = self._get_string_data_object(letter)
            io_node.add_data_object(path, data_object)

        self.assertEqual(io_node.data_root.render()[2][4], 't')

    def testAddDataObjectsFromJson(self):
        data='[["i"],["a","m"],["r","o","b","o","t"]]'
        data_type = 'string'
        io_node = InputOutputNode.objects.create()
        io_node.add_data_objects_from_json(data, data_type)

        self.assertEqual(io_node.data_root.render()[2][4], 't')
