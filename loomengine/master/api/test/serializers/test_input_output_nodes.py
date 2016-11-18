from django.test import TestCase
from rest_framework import serializers

from api.serializers.data_objects import *
from api.serializers.input_output_nodes import *
from . import fixtures


class TestInputOutputNodeDataFieldSerializer(TestCase):

    def testValidateString(self):
        raw_data = "[3,[]]]"
        s = InputOutputNodeDataFieldSerializer(
            data={"data": raw_data}, 
            context={'type': 'string'})
        self.assertTrue(s.is_valid(raise_exception=True))

    def testValidateInteger(self):
        raw_data = 7
        s = InputOutputNodeDataFieldSerializer(
            data={'data': raw_data}, 
            context={'type': 'integer'})
        self.assertTrue(s.is_valid(raise_exception=True))

    def testValidateFloat(self):
        raw_data = 3.2
        s = InputOutputNodeDataFieldSerializer(
            data={'data': raw_data}, 
            context={'type': 'float'})
        self.assertTrue(s.is_valid(raise_exception=True))

    def testValidateBoolean(self):
        raw_data = False
        s = InputOutputNodeDataFieldSerializer(
            data={'data': raw_data},
            context={'type': 'boolean'})
        self.assertTrue(s.is_valid(raise_exception=True))

    def testValidateLists(self):
        for data in [['word', 'draw'],
                     [3.2,2.3],
                     [7,3],
                     [True,False]]:
            s = InputOutputNodeDataFieldSerializer(data={'data': data})
            self.assertTrue(s.is_valid(raise_exception=True))

    def testValidateListOfLists(self):
        s = InputOutputNodeDataFieldSerializer(data={
            'data': [[['word','drow'],['word','drow']],
                     [['word','drow'],['word','drow']]]},
                               context={'type': 'string'})
        self.assertTrue(s.is_valid(raise_exception=True))

    def testValidateEmptyList(self):
        s = InputOutputNodeDataFieldSerializer(data={'data': []},
                               context={'type': 'string'})
        self.assertTrue(s.is_valid(raise_exception=True))

    def testValidateDict(self):
        s = InputOutputNodeDataFieldSerializer(
            data={'data': {'type': 'integer', 'value': 3}},
            context={'type': 'integer'})
        self.assertTrue(s.is_valid(raise_exception=True))

    def testValidateListOfDicts(self):
        s = InputOutputNodeDataFieldSerializer(
            data={'data': 
                  [{'type': 'integer', 'value': 3},
                   {'type': 'integer', 'value': 4}]},
            context={'type': 'string'})
        self.assertTrue(s.is_valid(raise_exception=True))

    def testNegValidationError(self):
        s = InputOutputNodeDataFieldSerializer(
            data={'data': [[["string"],
                            [{"not": "string"}]]]},
            context={'type': 'string'})
        with self.assertRaises(serializers.ValidationError):
            s.is_valid(raise_exception=True)

    def testNegValidateMixed(self):
        s = InputOutputNodeDataFieldSerializer(data={'data': ['x',3]})
        with self.assertRaises(serializers.ValidationError):
            s.is_valid(raise_exception=True)

    def testNegValidateNonuniformDepth(self):
        s = InputOutputNodeDataFieldSerializer(data={'data': [3,[4,5]]})
        with self.assertRaises(serializers.ValidationError):
            s.is_valid(raise_exception=True)

    def testNegValidateMismatchedTypes(self):
        s = InputOutputNodeDataFieldSerializer(data={'data': [[3,4],['a','b']]})
        with self.assertRaises(serializers.ValidationError):
            s.is_valid(raise_exception=True)

    def testNegValidateMismatchedObjectTypes(self):
        s = InputOutputNodeDataFieldSerializer(
            data={'data': [
                [{'type': 'integer', 'value': 3}],
                [{'type': 'string', 'value': 'a'}]
            ]},
            context={'type': 'string'})
        with self.assertRaises(serializers.ValidationError):
            s.is_valid(raise_exception=True)

    def testCreateString(self):
        raw_data = "[3,[]]]"
        s = InputOutputNodeDataFieldSerializer(
            data={"data": raw_data}, 
            context={'type': 'string'})
        s.is_valid(raise_exception=True)
        m = s.save()
        data = InputOutputNodeDataFieldSerializer(m).data
        self.assertEqual(data['data']['value'], raw_data)

    def testCreateInteger(self):
        raw_data = 7
        s = InputOutputNodeDataFieldSerializer(
            data={'data': raw_data}, 
            context={'type': 'integer'})
        s.is_valid(raise_exception=True)
        m = s.save()
        data = InputOutputNodeDataFieldSerializer(m).data
        self.assertEqual(data['data']['value'], raw_data)

    def testCreateFloat(self):
        raw_data = 3.2
        s = InputOutputNodeDataFieldSerializer(
            data={'data': raw_data}, 
            context={'type': 'float'})
        s.is_valid(raise_exception=True)
        m = s.save()
        data = InputOutputNodeDataFieldSerializer(m).data
        self.assertEqual(data['data']['value'], raw_data)

    def testCreateBoolean(self):
        raw_data = False
        s = InputOutputNodeDataFieldSerializer(
            data={'data': raw_data},
            context={'type': 'boolean'})
        s.is_valid(raise_exception=True)
        m = s.save()
        data = InputOutputNodeDataFieldSerializer(m).data
        self.assertEqual(data['data']['value'], raw_data)

    def testCreateList(self):
        raw_data = ['word', 'draw']
        s = InputOutputNodeDataFieldSerializer(data={'data': raw_data},
                               context={'type': 'string'})
        s.is_valid(raise_exception=True)
        m = s.save()
        data = InputOutputNodeDataFieldSerializer(m).data
        self.assertEqual(data['data'][0]['value'], raw_data[0])

    def testCreateListOfLists(self):
        s = InputOutputNodeDataFieldSerializer(data={
            'data': [[['word','drow'],['word','drow']],
                     [['word','drow'],['word','drow']]]},
                               context={'type': 'string'})
        self.assertTrue(s.is_valid(raise_exception=True))

    def testCreateEmptyList(self):
        s = InputOutputNodeDataFieldSerializer(data={'data': []},
                               context={'type': 'string'})
        s.is_valid(raise_exception=True)
        m = s.save()
        data = InputOutputNodeDataFieldSerializer(m).data
        self.assertEqual(data['data'], [])


    def testCreateDict(self):
        raw_data = {'type': 'integer', 'value': 3}
        s = InputOutputNodeDataFieldSerializer(
            data={'data': raw_data},
            context={'type': 'integer'})
        s.is_valid(raise_exception=True)
        m = s.save()
        data = InputOutputNodeDataFieldSerializer(m).data
        self.assertEqual(data['data']['value'], raw_data['value'])

    def testCreateListOfDicts(self):
        raw_data = [{'type': 'integer', 'value': 3},
                    {'type': 'integer', 'value': 4}]
        s = InputOutputNodeDataFieldSerializer(
            data={'data': raw_data},
            context={'type': 'integer'})
        s.is_valid(raise_exception=True)
        m = s.save()
        data = InputOutputNodeDataFieldSerializer(m).data
        self.assertEqual(data['data'][0]['value'], raw_data[0]['value'])
        self.assertEqual(data['data'][1]['value'], raw_data[1]['value'])

    def testDataToData(self):
        raw_data = "something"
        s = InputOutputNodeDataFieldSerializer(
            data={"data": raw_data}, 
            context={'type': 'string'})
        s.is_valid(raise_exception=True)
        self.assertEqual(s.data['data'], raw_data)
