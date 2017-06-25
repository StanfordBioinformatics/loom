from django.test import TestCase
from rest_framework import serializers

from . import get_mock_context, get_mock_request
from api.serializers.data_nodes import DataNodeSerializer


class TestDataNodeSerializer(TestCase):

    def testValidateString(self):
        raw_data = "[3,[]]]"
        s = DataNodeSerializer(
            data={'data': raw_data}, 
            context={'type': 'string'})
        self.assertTrue(s.is_valid(raise_exception=True))

    def testValidateInteger(self):
        raw_data = 7
        s = DataNodeSerializer(
            data={'data': raw_data}, 
            context={'type': 'integer'})
        self.assertTrue(s.is_valid(raise_exception=True))

    def testValidateFloat(self):
        raw_data = 3.2
        s = DataNodeSerializer(
            data={'data': raw_data}, 
            context={'type': 'float'})
        self.assertTrue(s.is_valid(raise_exception=True))

    def testValidateBoolean(self):
        raw_data = False
        s = DataNodeSerializer(
            data={'data': raw_data},
            context={'type': 'boolean'})
        self.assertTrue(s.is_valid(raise_exception=True))

    def testValidateLists(self):
        for data in [['word', 'draw'],
                     [3.2,2.3],
                     [7,3],
                     [True,False]]:
            s = DataNodeSerializer(data={'data': data})
            self.assertTrue(s.is_valid(raise_exception=True))

    def testValidateListOfLists(self):
        s = DataNodeSerializer(data={
            'data': [[['word','drow'],['word','drow']],
                         [['word','drow'],['word','drow']]]},
                               context={'type': 'string'})
        self.assertTrue(s.is_valid(raise_exception=True))

    def testValidateEmptyList(self):
        s = DataNodeSerializer(data={'data': []},
                               context={'type': 'string'})
        self.assertTrue(s.is_valid(raise_exception=True))

    def testValidateDict(self):
        s = DataNodeSerializer(
            data={'data': {'type': 'integer', 'contents': 3}},
            context={'type': 'integer'})
        self.assertTrue(s.is_valid(raise_exception=True))

    def testValidateListOfDicts(self):
        s = DataNodeSerializer(
            data={'data': 
                  [{'type': 'integer', 'contents': 3},
                   {'type': 'integer', 'contents': 4}]},
            context={'type': 'string'})
        self.assertTrue(s.is_valid(raise_exception=True))

    def testNegValidationError(self):
        s = DataNodeSerializer(
            data={'data': [[["string"],
                                [{"not": "string"}]]]},
            context={'type': 'string'})
        with self.assertRaises(serializers.ValidationError):
            s.is_valid(raise_exception=True)

    def testNegValidateMixed(self):
        s = DataNodeSerializer(data={'data': ['x',3]})
        with self.assertRaises(serializers.ValidationError):
            s.is_valid(raise_exception=True)

    def testNegValidateNonuniformDepth(self):
        s = DataNodeSerializer(data={'data': [3,[4,5]]})
        with self.assertRaises(serializers.ValidationError):
            s.is_valid(raise_exception=True)

    def testNegValidateMismatchedTypes(self):
        s = DataNodeSerializer(data={'data': [[3,4],['a','b']]})
        with self.assertRaises(serializers.ValidationError):
            s.is_valid(raise_exception=True)

    def testNegValidateMismatchedObjectTypes(self):
        s = DataNodeSerializer(
            data={'data': [
                [{'type': 'integer', 'contents': 3}],
                [{'type': 'string', 'contents': 'a'}]
            ]},
            context={'type': 'string'})
        with self.assertRaises(serializers.ValidationError):
            s.is_valid(raise_exception=True)

    def testCreateString(self):
        raw_data = "[3,[]]]"
        s = DataNodeSerializer(
            data={'data': raw_data}, 
            context={'type': 'string'})
        s.is_valid(raise_exception=True)
        m = s.save()
        data = DataNodeSerializer(m, context=get_mock_context()).data
        self.assertEqual(data['data']['contents'], raw_data)

    def testCreateInteger(self):
        raw_data = 7
        s = DataNodeSerializer(
            data={'data': raw_data}, 
            context={'type': 'integer'})
        s.is_valid(raise_exception=True)
        m = s.save()
        data = DataNodeSerializer(m, context=get_mock_context()).data
        self.assertEqual(data['data']['contents'], raw_data)

    def testCreateFloat(self):
        raw_data = 3.2
        s = DataNodeSerializer(
            data={'data': raw_data}, 
            context={'type': 'float'})
        s.is_valid(raise_exception=True)
        m = s.save()
        data = DataNodeSerializer(m, context=get_mock_context()).data
        self.assertEqual(data['data']['contents'], raw_data)

    def testCreateBoolean(self):
        raw_data = False
        s = DataNodeSerializer(
            data={'data': raw_data},
            context={'type': 'boolean'})
        s.is_valid(raise_exception=True)
        m = s.save()
        data = DataNodeSerializer(m, context=get_mock_context()).data
        self.assertEqual(data['data']['contents'], raw_data)

    def testCreateList(self):
        raw_data = ['word', 'draw']
        s = DataNodeSerializer(data={'data': raw_data},
                               context={'type': 'string'})
        s.is_valid(raise_exception=True)
        m = s.save()
        data = DataNodeSerializer(m, context=get_mock_context()).data
        self.assertEqual(data['data'][0]['contents'], raw_data[0])

    def testCreateListOfLists(self):
        s = DataNodeSerializer(data={
            'data': [[['word','drow'],['word','drow']],
                     [['word','drow'],['word','drow']]]},
                               context={'type': 'string'})
        self.assertTrue(s.is_valid(raise_exception=True))

    def testCreateEmptyList(self):
        s = DataNodeSerializer(data={'data': []},
                               context={'type': 'string'})
        s.is_valid(raise_exception=True)
        m = s.save()
        data = DataNodeSerializer(m, context=get_mock_context()).data
        self.assertEqual(data['data'], [])


    def testCreateDict(self):
        raw_data = {'type': 'integer', 'contents': 3}
        s = DataNodeSerializer(
            data={'data': raw_data},
            context={'type': 'integer'})
        s.is_valid(raise_exception=True)
        m = s.save()
        data = DataNodeSerializer(m, context=get_mock_context()).data
        self.assertEqual(data['data']['contents'], raw_data['contents'])

    def testCreateListOfDicts(self):
        raw_data = [{'type': 'integer', 'contents': 3},
                    {'type': 'integer', 'contents': 4}]
        s = DataNodeSerializer(
            data={'data': raw_data},
            context={'type': 'integer'})
        s.is_valid(raise_exception=True)
        m = s.save()
        data = DataNodeSerializer(m, context=get_mock_context()).data
        self.assertEqual(data['data'][0]['contents'], raw_data[0]['contents'])
        self.assertEqual(data['data'][1]['contents'], raw_data[1]['contents'])

    def testDataToData(self):
        raw_data = "something"
        s = DataNodeSerializer(
            data={'data': raw_data}, 
            context={'type': 'string',
                     'request': get_mock_request()})
        s.is_valid(raise_exception=True)
        s.save()
        self.assertEqual(s.data['data']['contents'], raw_data)
