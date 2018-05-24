from django.test import TestCase
from rest_framework import serializers

from . import get_mock_context, get_mock_request
from api.serializers.data_nodes import URLDataNodeSerializer, \
    DataNodeSerializer
from api.serializers.data_objects import DataObjectSerializer

class TestURLDataNodeSerializer(TestCase):
    def testNoContents(self):
        raw_data = 7
        s = DataNodeSerializer(
            data={'contents': raw_data}, 
            context={'type': 'integer'})
        s.is_valid()
        data_object = s.save()

        s = URLDataNodeSerializer(
            data_object,
            context=get_mock_context())
        data = s.data
        
        # only uuid and url should be rendered
        self.assertTrue('uuid' in data)
        self.assertTrue('url' in data)
        self.assertEqual(len(data.keys()), 2)
        

class TestDataNodeSerializer(TestCase):

    def testValidateString(self):
        raw_data = "[3,[]]]"
        s = DataNodeSerializer(
            data={'contents': raw_data}, 
            context={'type': 'string'})
        self.assertTrue(s.is_valid(raise_exception=True))

    def testValidateInteger(self):
        raw_data = 7
        s = DataNodeSerializer(
            data={'contents': raw_data}, 
            context={'type': 'integer'})
        self.assertTrue(s.is_valid(raise_exception=True))

    def testValidateFloat(self):
        raw_data = 3.2
        s = DataNodeSerializer(
            data={'contents': raw_data}, 
            context={'type': 'float'})
        self.assertTrue(s.is_valid(raise_exception=True))

    def testValidateBoolean(self):
        raw_data = False
        s = DataNodeSerializer(
            data={'contents': raw_data},
            context={'type': 'boolean'})
        self.assertTrue(s.is_valid(raise_exception=True))

    def testValidateLists(self):
        for data in [['word', 'draw'],
                     [3.2,2.3],
                     [7,3],
                     [True,False]]:
            s = DataNodeSerializer(data={'contents': data})
            self.assertTrue(s.is_valid(raise_exception=True))

    def testValidateListOfLists(self):
        s = DataNodeSerializer(data={
            'contents': [[['word','drow'],['word','drow']],
                         [['word','drow'],['word','drow']]]},
                               context={'type': 'string'})
        self.assertTrue(s.is_valid(raise_exception=True))

    def testValidateEmptyList(self):
        s = DataNodeSerializer(data={'contents': []},
                               context={'type': 'string'})
        self.assertTrue(s.is_valid(raise_exception=True))

    def testValidateDict(self):
        s = DataNodeSerializer(
            data={'contents': {'type': 'integer', 'contents': 3}},
            context={'type': 'integer'})
        self.assertTrue(s.is_valid(raise_exception=True))

    def testValidateListOfDicts(self):
        s = DataNodeSerializer(
            data={'contents': 
                  [{'type': 'integer', 'contents': 3},
                   {'type': 'integer', 'contents': 4}]},
            context={'type': 'string'})
        self.assertTrue(s.is_valid(raise_exception=True))

    def testNegValidationError(self):
        s = DataNodeSerializer(
            data={'contents': [[["string"],
                                [{"not": "string"}]]]},
            context={'type': 'string'})
        with self.assertRaises(serializers.ValidationError):
            s.is_valid(raise_exception=True)

    def testNegValidateMixed(self):
        s = DataNodeSerializer(data={'contents': ['x',3]})
        with self.assertRaises(serializers.ValidationError):
            s.is_valid(raise_exception=True)

    def testNegValidateNonuniformDepth(self):
        s = DataNodeSerializer(data={'contents': [3,[4,5]]})
        with self.assertRaises(serializers.ValidationError):
            s.is_valid(raise_exception=True)

    def testNegValidateMismatchedTypes(self):
        s = DataNodeSerializer(data={'contents': [[3,4],['a','b']]})
        with self.assertRaises(serializers.ValidationError):
            s.is_valid(raise_exception=True)

    def testNegValidateMismatchedObjectTypes(self):
        s = DataNodeSerializer(
            data={'contents': [
                [{'type': 'integer', 'contents': 3}],
                [{'type': 'string', 'contents': 'a'}]
            ]},
            context={'type': 'string'})
        with self.assertRaises(serializers.ValidationError):
            s.is_valid(raise_exception=True)

    def testCreateString(self):
        raw_data = "[3,[]]]"
        s = DataNodeSerializer(
            data={'contents': raw_data}, 
            context={'type': 'string'})
        s.is_valid(raise_exception=True)
        m = s.save()
        data = DataNodeSerializer(m, context=get_mock_context()).data
        self.assertEqual(data['contents']['value'], raw_data)

    def testCreateInteger(self):
        raw_data = 7
        s = DataNodeSerializer(
            data={'contents': raw_data}, 
            context={'type': 'integer'})
        s.is_valid(raise_exception=True)
        m = s.save()
        data = DataNodeSerializer(m, context=get_mock_context()).data
        self.assertEqual(data['contents']['value'], raw_data)

    def testCreateFloat(self):
        raw_data = 3.2
        s = DataNodeSerializer(
            data={'contents': raw_data}, 
            context={'type': 'float'})
        s.is_valid(raise_exception=True)
        m = s.save()
        data = DataNodeSerializer(m, context=get_mock_context()).data
        self.assertEqual(data['contents']['value'], raw_data)

    def testCreateBoolean(self):
        raw_data = False
        s = DataNodeSerializer(
            data={'contents': raw_data},
            context={'type': 'boolean'})
        s.is_valid(raise_exception=True)
        m = s.save()
        data = DataNodeSerializer(m, context=get_mock_context()).data
        self.assertEqual(data['contents']['value'], raw_data)

    def testCreateReference(self):
        value = True
        s = DataObjectSerializer(data={'type': 'boolean', 'value': value})
        s.is_valid(raise_exception=True)
        do = s.save()
        contents = {'uuid': do.uuid,
                    'url': 'http://127.0.0.1/data-objects/%s/' % do.uuid}

        s = DataNodeSerializer(
            data={'contents': contents},
            context={'type': 'boolean'})
        s.is_valid(raise_exception=True)
        m = s.save()
        self.assertEqual(m.data_object.value, value)

    def testCreateList(self):
        raw_data = ['word', 'draw']
        s = DataNodeSerializer(data={'contents': raw_data},
                               context={'type': 'string'})
        s.is_valid(raise_exception=True)
        m = s.save()
        data = DataNodeSerializer(m, context=get_mock_context()).data
        self.assertEqual(data['contents'][0]['value'], raw_data[0])

    def testCreateListOfLists(self):
        s = DataNodeSerializer(data={
            'contents': [[['word','drow'],['word','drow']],
                     [['word','drow'],['word','drow']]]},
                               context={'type': 'string'})
        self.assertTrue(s.is_valid(raise_exception=True))

    def testCreateEmptyList(self):
        s = DataNodeSerializer(data={'contents': []},
                                       context={'type': 'string'})
        s.is_valid(raise_exception=True)
        m = s.save()
        data = DataNodeSerializer(m, context=get_mock_context()).data
        self.assertEqual(data['contents'], [])


    def testCreateDict(self):
        raw_data = {'type': 'integer', 'value': 3}
        s = DataNodeSerializer(
            data={'contents': raw_data},
            context={'type': 'integer'})
        s.is_valid(raise_exception=True)
        m = s.save()
        data = DataNodeSerializer(m, context=get_mock_context()).data
        self.assertEqual(data['contents']['value'], raw_data['value'])

    def testCreateListOfDicts(self):
        raw_data = [{'type': 'integer', 'value': 3},
                    {'type': 'integer', 'value': 4}]
        s = DataNodeSerializer(
            data={'contents': raw_data},
            context={'type': 'integer'})
        s.is_valid(raise_exception=True)
        m = s.save()
        data = DataNodeSerializer(m, context=get_mock_context()).data
        self.assertEqual(data['contents'][0]['value'], raw_data[0]['value'])
        self.assertEqual(data['contents'][1]['value'], raw_data[1]['value'])

    def testDataToData(self):
        raw_data = "something"
        s = DataNodeSerializer(
            data={'contents': raw_data}, 
            context={'type': 'string',
                     'request': get_mock_request()})
        s.is_valid(raise_exception=True)
        s.save()
        self.assertEqual(s.data['contents']['value'], raw_data)
