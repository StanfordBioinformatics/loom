from django.core.exceptions import ValidationError
from django.test import TestCase
from .models import DataObject, Port

class TestDataObjects(TestCase):

    def test_boolean(self):
        data = '{"type": "boolean", "value": false}'
        o = DataObject.create(data)
        self.assertEqual(o.to_json(metadata=False), data)

    def test_file(self):
        data = '{"type": "file", "value": {"hash_algorithm": "sha-256", "hash_value": "f2ca1bb6c7e907d06dafe4687e579fce76b37e4e93b7605022da52e6ccc26fd2"}}'
        o = DataObject.create(data)
        self.assertEqual(o.to_json(metadata=False), data)

    def test_array(self):
        data = '{"type": "array[boolean]", "value": [false, true, false]}'
        o = DataObject.create(data)
        self.assertEqual(o.to_json(metadata=False), data)

    def test_deep_array(self):
        data = '{"type": "array[array[boolean]]", "value": [[true, false], [false, false]]}'
        o = DataObject.create(data)
        self.assertEqual(o.to_json(metadata=False), data)

    def test_invalid_array(self):
        data = '{"type": "array[boolean]", "value": false}'
        with self.assertRaises(ValidationError):
            o = DataObject.create(data)

    def test_tuple(self):
        data = '{"type": "tuple[boolean, string, integer]", "value": [false, "count", 5]}'
        o = DataObject.create(data)
        self.assertEqual(o.to_json(metadata=False), data)

    def test_invalid_tuple(self):
        data = '{"type": "tuple[boolean]", "value": false}'
        with self.assertRaises(ValidationError):
            o = DataObject.create(data)

    def test_sorted_keys(self):
        data = '{"value": false, "type": "boolean"}'
        sorted_data = '{"type": "boolean", "value": false}'

        o = DataObject.create(data)
        self.assertEqual(o.to_json(metadata=False), sorted_data) 

    def test_invalid_type(self):
        data = '{"type": "vegetable", "value": "cucumber"}'
        with self.assertRaises(ValidationError):
            o = DataObject.create(data)

    def test_whitespace(self):
        data = """{
   "type": "boolean",
   "value": false
}"""
        data_whitespace_removed = '{"type": "boolean", "value": false}'
        o = DataObject.create(data)
        self.assertEqual(o.to_json(metadata=False), data_whitespace_removed)

class TestPort(TestCase):

    def test_port(self):
        data = '{"data_type": "array[tuple[boolean, string, file]", "metadata": {"author": "Herodotus"}, "name": "testport", "port_type": "input"}'
        o = Port.create(data)
        self.assertEqual(o.to_json(), data)
