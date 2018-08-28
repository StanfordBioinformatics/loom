import copy
import uuid
from rest_framework.serializers import ValidationError
from django.test import TestCase

from . import fixtures, get_mock_context
from api.serializers.data_objects import DataObjectSerializer, \
    FileResourceSerializer
from api.models.data_objects import DataObject


class TestDataObjectSerializer(TestCase):

    def testCreate_file(self):
        data = fixtures.data_objects.file_data_object
        s = DataObjectSerializer(data=data)
        s.is_valid(raise_exception=True)
        data_object = s.save()
        self.assertEqual(data_object.file_resource.filename,
                         data['value']['filename'])

    def testCreate_countQueries(self):
        data = fixtures.data_objects.file_data_object
        s = DataObjectSerializer(data=data)
        s.is_valid(raise_exception=True)
        self.assertNumQueries(4, lambda: s.save())

    def testRender_file(self):
        file_data = fixtures.data_objects.file_data_object['value']
        data_object = DataObject.create_and_initialize_file_resource(**file_data)
        s = DataObjectSerializer(data_object,
                                 context=get_mock_context())
        rendered_data = s.data
        value = rendered_data['value']
        self.assertEqual(value['filename'], file_data['filename'])
        self.assertEqual(value['md5'], file_data['md5'])
        self.assertEqual(value['source_type'], file_data['source_type'])
        self.assertEqual(value['import_comments'], file_data['import_comments'])
        self.assertEqual(value['imported_from_url'], file_data['imported_from_url'])

    def testRoundTrip_file(self):
        file_data = fixtures.data_objects.file_data_object['value']
        data_object = DataObject.create_and_initialize_file_resource(**file_data)
        s = DataObjectSerializer(data_object,
                                 context=get_mock_context())
        rendered_1 = s.data

        # update UUID to avoid collision
        input_2 = copy.deepcopy(rendered_1)
        input_2['uuid'] = str(uuid.uuid4())
        s = DataObjectSerializer(data=input_2)
        s.is_valid(raise_exception=True)
        data_object = s.save()
        s = DataObjectSerializer(data_object,
                                 context=get_mock_context())
        rendered_2 = s.data

        self.assertEqual(rendered_1['type'],
                         rendered_2['type'])
        self.assertEqual(rendered_1['datetime_created'],
                         rendered_2['datetime_created'])
        self.assertNotEqual(rendered_1['uuid'],
                            rendered_2['uuid'])
        self.assertNotEqual(rendered_1['url'],
                            rendered_2['url'])
        self.assertEqual(rendered_1['value']['filename'],
                         rendered_2['value']['filename'])
        self.assertEqual(rendered_1['value']['md5'],
                         rendered_2['value']['md5'])
        self.assertEqual(rendered_1['value']['import_comments'],
                         rendered_2['value']['import_comments'])
        self.assertEqual(rendered_1['value']['imported_from_url'],
                         rendered_2['value']['imported_from_url'])
        self.assertEqual(rendered_1['value']['upload_status'],
                         rendered_2['value']['upload_status'])
        self.assertEqual(rendered_1['value']['source_type'],
                         rendered_2['value']['source_type'])
        self.assertEqual(rendered_1['value']['file_url'],
                            rendered_2['value']['file_url'])

    def testCreate_AlreadyExists(self):
        file_data = copy.deepcopy(fixtures.data_objects.file_data_object)['value']
        data_object = DataObject.create_and_initialize_file_resource(**file_data)
        s = DataObjectSerializer(data_object,
                                 context=get_mock_context())
        rendered_1 = s.data

        data_object_count_before = DataObject.objects.count()
        s = DataObjectSerializer(data=rendered_1)
        s.is_valid(raise_exception=True)
        data_object = s.save()

        # Verify that no new object was created
        data_object_count_after = DataObject.objects.count()
        self.assertEqual(data_object_count_before, data_object_count_after)

    def testCreate_ErrorAlreadyExistsWithMismatch(self):
        file_data = copy.deepcopy(fixtures.data_objects.file_data_object)['value']
        data_object = DataObject.create_and_initialize_file_resource(**file_data)
        s = DataObjectSerializer(data_object,
                                 context=get_mock_context())
        data_object_count_before = DataObject.objects.count()

        rendered_1 = s.data
        rendered_1['value']['md5'] = '192f08c86f675deca469ea50ffac38e0'
        s = DataObjectSerializer(data=rendered_1)
        with self.assertRaises(ValidationError):
            s.is_valid(raise_exception=True)
            data_object = s.save()

        # Verify that no new object was created
        data_object_count_after = DataObject.objects.count()
        self.assertEqual(data_object_count_before, data_object_count_after)
            
    def testCreate_noDroolOnFail(self):
        file_data = copy.deepcopy(fixtures.data_objects.file_data_object)
        file_data['value']['md5'] = 'invalid_md5'

        data_object_count_before = DataObject.objects.count()
        s = DataObjectSerializer(data=file_data)
        s.is_valid(raise_exception=True)
        with self.assertRaises(ValidationError):
            m = s.save()
        data_object_count_after = DataObject.objects.count()

        self.assertEqual(data_object_count_before, data_object_count_after)

    data_object_fixtures = [
        copy.deepcopy(fixtures.data_objects.string_data_object),
        copy.deepcopy(fixtures.data_objects.boolean_data_object),
        copy.deepcopy(fixtures.data_objects.float_data_object),
        copy.deepcopy(fixtures.data_objects.integer_data_object)
    ]
        
    def testCreate_nonFileTypes(self):
        for data in self.data_object_fixtures:
            s = DataObjectSerializer(data=data)
            s.is_valid(raise_exception=True)
            data_object = s.save()
            self.assertEqual(data_object.value, data['value'])

            rendered_data = DataObjectSerializer(
                data_object, context=get_mock_context()).data
            self.assertEqual(data_object.value, rendered_data['value'])

    def testRoundTrip_nonFileTypes(self):
        for data in self.data_object_fixtures:
            s1 = DataObjectSerializer(data=data)
            s1.is_valid(raise_exception=True)
            data_object_1 = s1.save()
            self.assertEqual(data_object_1.value, data['value'])
            rendered_data = DataObjectSerializer(
                data_object_1, context=get_mock_context()).data

            # Update UUID to avoid collision
            rendered_data['uuid'] = uuid.uuid4()
            s2 = DataObjectSerializer(data=rendered_data)
            s2.is_valid(raise_exception=True)
            data_object_2 = s2.save()
            self.assertEqual(data_object_1.value, data_object_2.value)

def TestDataObjectUpdateSerializer(TestCase):

    def testUpdateUploadStatus(self):
        file_data = fixtures.data_objects.file_data_object['value']
        data_object = DataObject.create_and_initialize_file_resource(**file_data)
        s = DataObjectSerializer(data_object,
                                 context=get_mock_context())
        s.save()

        s2 = DataObjectUpdateSerializer(data_object)
        s2.update(
            data_object, {'value': {'upload_status': 'error'}})
        self.assertEqual(s2.data['value']['upload_status'], 'error')


    def testUpdateProtectedValue(self):
        file_data = fixtures.data_objects.file_data_object['value']
        data_object = DataObject.create_and_initialize_file_resource(**file_data)
        s = DataObjectSerializer(data_object,
                                 context=get_mock_context())
        s.save()

        s2 = DataObjectUpdateSerializer(data_object)
        with self.assertRaises(ValidationError):
            s2.update(
                data_object, {'type': 'string'})
