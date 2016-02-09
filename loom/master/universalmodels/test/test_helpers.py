from django.test import TestCase
import uuid
from universalmodels.helpers import NonserializableTypeConverter

class TestNonserializableTypeConverter(TestCase):

    def testConvertScalar(self):
        id = uuid.uuid4()
        self.assertEqual(str(id), NonserializableTypeConverter.convert(id))

    def testConvertList(self):
        l = [uuid.uuid4(), 'x']
        converted_l = NonserializableTypeConverter.convert_struct(l)
        self.assertEqual(l[1], converted_l[1])
        self.assertEqual(str(l[0]), converted_l[0])

    def testConvertDict(self):
        d = {
            'id': uuid.uuid4(), 
            'name': 'x'
            }
        converted_d = NonserializableTypeConverter.convert_struct(d)
        self.assertEqual(str(d['id']), converted_d['id'])
        self.assertEqual(d['name'], converted_d['name'])
