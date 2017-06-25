import copy
import uuid
from django.core.exceptions import ValidationError
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
                         data['contents']['filename'])

    def testRender_file(self):
        file_data = fixtures.data_objects.file_data_object['contents']
        data_object = DataObject.create_and_initialize_file_resource(**file_data)
        s = DataObjectSerializer(data_object,
                                 context=get_mock_context())
        rendered_data = s.data
        value = rendered_data['contents']
        self.assertEqual(value['filename'], file_data['filename'])
        self.assertEqual(value['md5'], file_data['md5'])
        self.assertEqual(value['source_type'], file_data['source_type'])
        self.assertEqual(value['import_comments'], file_data['import_comments'])
        self.assertEqual(value['imported_from_url'], file_data['imported_from_url'])

    def testRoundTrip_file(self):
        file_data = fixtures.data_objects.file_data_object['contents']
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
        self.assertEqual(rendered_1['contents']['filename'],
                         rendered_2['contents']['filename'])
        self.assertEqual(rendered_1['contents']['md5'],
                         rendered_2['contents']['md5'])
        self.assertEqual(rendered_1['contents']['import_comments'],
                         rendered_2['contents']['import_comments'])
        self.assertEqual(rendered_1['contents']['imported_from_url'],
                         rendered_2['contents']['imported_from_url'])
        self.assertEqual(rendered_1['contents']['upload_status'],
                         rendered_2['contents']['upload_status'])
        self.assertEqual(rendered_1['contents']['source_type'],
                         rendered_2['contents']['source_type'])
        self.assertEqual(rendered_1['contents']['file_url'],
                            rendered_2['contents']['file_url'])

    def testCreate_errorUuidCollision(self):
        file_data = copy.deepcopy(fixtures.data_objects.file_data_object)['contents']
        data_object = DataObject.create_and_initialize_file_resource(**file_data)
        s = DataObjectSerializer(data_object,
                                 context=get_mock_context())
        rendered_1 = s.data

        # update UUID to avoid collision
        s = DataObjectSerializer(data=rendered_1)
        s.is_valid(raise_exception=True)
        with self.assertRaises(ValidationError):
            data_object = s.save()

    def testCreate_noDroolOnFail(self):
        file_data = copy.deepcopy(fixtures.data_objects.file_data_object)
        file_data['contents']['md5'] = 'invalid_md5'

        data_object_count_before = DataObject.objects.count()
        s = DataObjectSerializer(data=file_data)
        s.is_valid(raise_exception=True)
        with self.assertRaises(ValidationError):
            s.save()
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
            self.assertEqual(data_object.contents, data['contents'])

            rendered_data = DataObjectSerializer(
                data_object, context=get_mock_context()).data
            self.assertEqual(data_object.contents, rendered_data['contents'])

    def testRoundTrip_nonFileTypes(self):
        for data in self.data_object_fixtures:
            s1 = DataObjectSerializer(data=data)
            s1.is_valid(raise_exception=True)
            data_object_1 = s1.save()
            self.assertEqual(data_object_1.contents, data['contents'])
            rendered_data = DataObjectSerializer(
                data_object_1, context=get_mock_context()).data

            # Update UUID to avoid collision
            rendered_data['uuid'] = uuid.uuid4()
            s2 = DataObjectSerializer(data=rendered_data)
            s2.is_valid(raise_exception=True)
            data_object_2 = s2.save()
            self.assertEqual(data_object_1.contents, data_object_2.contents)
