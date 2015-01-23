import hashlib
import json
from django.core.exceptions import ValidationError
from django.test import TestCase
from .models import _BaseModel, _BaseModelData, _Hashable, Application, DataObject, Environment

class TestHashable(TestCase):
    def setUp(self):
        self.data = '{"some": 3, "data": [4, 5]}'
        self.data_sorted_keys = json.dumps(json.loads(self.data),sort_keys=True)
        self.h = _Hashable(_json=self.data)
        self.h.save()

    def test_json(self):
        self.assertEqual(self.h._get_json(), self.data_sorted_keys)

    def test_calculate_unique_id(self):
        self.assertEqual(self.h.get_id(), hashlib.sha256(self.data_sorted_keys).hexdigest())

    def test_get_by_id(self):
        self.assertIsNotNone(_Hashable.get_by_id(self.h.get_id()))

    def test_invalid_id(self):
        good_id = self.h.get_id()
        bad_id = 'fjioe392'
        self.h._id = bad_id
        # ID should be recalculated on save
        self.h.save()
        self.assertEqual(self.h.get_id(), good_id)

    def test_invalid_json(self):
        bad_json = 'This string is not a valid JSON'
        self.h._json = bad_json
        with self.assertRaises(ValidationError):
            self.h.save()

    def test_whitespace(self):
        data = """{
   "data_type": "boolean",
   "value": false
}"""
        data_whitespace_removed = '{"data_type": "boolean", "value": false}'
        o = _Hashable(_json=data)
        o.save()
        self.assertEqual(o._get_json(), data_whitespace_removed)


class TestBaseModelData(TestCase):
    def setUp(self):
        self.data = '{"some": 3, "data": [4, 5]}'
        self.data_sorted_keys = json.dumps(json.loads(self.data),sort_keys=True)
        self.d = _BaseModelData.create(self.data)
        self.d.save()

    def test_create(self):
        self.assertEqual(self.d._get_json(), self.data_sorted_keys)

    def test_get_by_id(self):
        self.assertIsNotNone(_BaseModelData.get_by_id(self.d.get_id()))

    def test_invalid_metadata(self):
        # This should throw an error if it contains a field called 'metadata'
        invalid_data = json.loads(self.data)
        invalid_data['metadata'] = {"something": [1,2,3]}
        self.d._json = json.dumps(invalid_data)
        with self.assertRaises(ValidationError):
            self.d.save()

class TestBaseModel(TestCase):
    def setUp(self):
        self.data = '{"some": 3, "data": [4, 5], "metadata": ["January", "22"]}'
        self.data_no_metadata = '{"some": 3, "data": [4, 5]}'
        self.metadata = '["January", "22"]'
        self.data_sorted_keys = json.dumps(json.loads(self.data),sort_keys=True)
        self.b = _BaseModel._create_model_from_json(self.data)

    def test_get_data_id(self):
        # data_id should match the hash of the data without metadata
        data = json.dumps(json.loads(self.data_no_metadata), sort_keys=True)
        self.assertEqual(self.b.get_data_id(), hashlib.sha256(data).hexdigest())

    def test_get_data_as_json(self):
        data = json.dumps(json.loads(self.data_no_metadata), sort_keys=True)
        self.assertEqual(self.b.get_data_as_json(metadata=False), data)

        data = json.dumps(json.loads(self.data), sort_keys=True)
        self.assertEqual(self.b.get_data_as_json(metadata=True), data)

    def test_invalid_json(self):
        data_obj = json.loads(self.b._get_json())
        data_obj['badkey'] = 3
        self.b._json = json.dumps(data_obj, sort_keys=True)
        with self.assertRaises(ValidationError):
            self.b.save()

    def test_get_by_id(self):
        self.assertIsNotNone(_BaseModel.get_by_id(self.b.get_id()))

class TestApplication(TestCase):

    def test_application(self):
        data_obj = {
            "metadata": {"name": "bwa",
                         "version": "0.7.4"},
            "application_type": "local",
            "paths": [
                {"PATH": "/usr/bin"}
            ]
        }
        data_json = json.dumps(data_obj, sort_keys=True)
        a = Application.create(data_json)
        self.assertEqual(a.get_data_as_json(), data_json)

class TestEnvironment(TestCase):

    def test_environment(self):
        data = {
            "metadata": {
                "version":
                3.2
            },
            "applications": [
                {"application_type": "local",
                 "paths": {
                     "PATH": "/usr/bin"
                 }
             },
                {"application_type": "local",
                 "paths": {
                     "PATH": "/usr/local/bin"
                 }
             }
            ]
        }

        data_json = json.dumps(data, sort_keys=True)

        e = Environment.create(data_json)
        self.assertEqual(e.get_data_as_json(), data_json)
        self.assertEqual(e.get_applications(), data['applications'])

    def test_invalid(self):
        with self.assertRaises(ValidationError):
            e = Environment.create('{"badkey": "value"}')


class TestDataObjects(TestCase):

    def test_boolean(self):
        data = '{"data_type": "boolean", "value": false}'
        o = DataObject.create(data)
        self.assertEqual(o.get_data_as_json(), data)

    def test_file(self):
        data = '{"data_type": "file", "value": {"hash_algorithm": "sha-256", "hash_value": "f2ca1bb6c7e907d06dafe4687e579fce76b37e4e93b7605022da52e6ccc26fd2"}}'
        o = DataObject.create(data)
        self.assertEqual(o.get_data_as_json(), data)

    def test_array(self):
        data = '{"data_type": "array[boolean]", "value": [false, true, false]}'
        o = DataObject.create(data)
        self.assertEqual(o.get_data_as_json(), data)

    def test_deep_array(self):
        data = '{"data_type": "array[array[boolean]]", "value": [[true, false], [false, false]]}'
        o = DataObject.create(data)
        self.assertEqual(o.get_data_as_json(), data)

    def test_invalid_array(self):
        data = '{"data_type": "array[boolean]", "value": false}'
        with self.assertRaises(ValidationError):
            o = DataObject.create(data)

    def test_tuple(self):
        data = '{"data_type": "tuple[boolean, string, integer]", "value": [false, "count", 5]}'
        o = DataObject.create(data)
        self.assertEqual(o.get_data_as_json(), data)

    def test_invalid_tuple(self):
        data = '{"data_type": "tuple[boolean]", "value": false}'
        with self.assertRaises(ValidationError):
            o = DataObject.create(data)

    def test_invalid_type(self):
        data = '{"data_type": "vegetable", "value": "cucumber"}'
        with self.assertRaises(ValidationError):
            o = DataObject.create(data)

    def test_get_data_type(self):
        data = '{"data_type": "boolean", "value": false}'
        o = DataObject.create(data)
        self.assertEqual(o.get_value(), False)

    def test_get_value(self):
        data = '{"data_type": "boolean", "value": false}'
        o = DataObject.create(data)
        self.assertEqual(o.get_data_type(), "boolean")


#class TestPort(TestCase):

#    def test_port(self):
#        data = '{"data_type": "array[tuple[boolean, string, file]", "metadata": {"author": "Herodotus"}, "name": "testport", "port_type": "input"}'
#        o = Port.create(data)
#        self.assertEqual(o.get_data_as_json(), data)

