from django.test import TestCase

from api.models.base import FilterHelper
from api.models.data_objects import DataObject, FileResource
from api import exceptions


def _create_file_data_object():
    data_object = DataObject.create_and_initialize_file_resource(
        filename='myfile.dat',
        source_type='imported',
        imported_from_url='file:///data/myfile.dat',
        import_comments='Test data',
        md5='081deeb1218a094526005f5f00ffd0a1'
    )
    return data_object

def _create_file_data_object_2():
    data_object = DataObject.create_and_initialize_file_resource(
        filename='myfile.dat',
        source_type='imported',
        imported_from_url='file:///data/myfile.dat',
        import_comments='Test data',
        md5='4175ed4ee06b828ff008949e28a61bf2'
    )
    return data_object

def _create_file_data_object_3():
    data_object = DataObject.create_and_initialize_file_resource(
        filename='myfile2.dat',
        source_type='imported',
        imported_from_url='file:///data/myfile.dat',
        import_comments='Test data',
        md5='081deeb1218a094526005f5f00ffd0a1'
    )
    return data_object


class TestFilterHelper(TestCase):

    def setUp(self):
        self.file_data_object = _create_file_data_object()
        self.file_data_object_2 = _create_file_data_object_2()
        self.file_data_object_3 = _create_file_data_object_3()
        self.filter_helper = FilterHelper(DataObject)

        self.name = self.file_data_object.file_resource.filename
        self.uuid = '@%s' % str(self.file_data_object.uuid)
        self.short_uuid = self.uuid[0:8]
        self.hash = '$%s' % self.file_data_object.file_resource.md5
           
    def testFilterByNameOrIdOrHash(self):
        for (query_string, expected_count) in [
                (self.name, 2),
                (self.uuid, 1),
                (self.short_uuid, 1),
                (self.hash, 2),
                (self.name+self.uuid, 1),
                (self.name+self.short_uuid, 1),
                (self.name+self.hash, 1),
                (self.name+self.hash+self.uuid, 1),
                (self.name+self.uuid+self.hash, 1),
                (self.name+self.hash+self.short_uuid, 1),
                (self.name+self.short_uuid+self.hash, 1),]:
            results = self.filter_helper.filter_by_name_or_id_or_tag_or_hash(
                query_string)
            self.assertEqual(results.count(), expected_count)
            self.assertTrue(self.file_data_object.id in [r.id for r in results.all()])

    def testFilterMultipleByNameOrIdOrHash(self):
        for (query_strings, expected_counts) in [
                ([self.name,], [2,]),
                ([self.uuid,], [1,]),
                ([self.short_uuid,], [1,]),
                ([self.hash,], [2,]),
                ([self.name+self.uuid,], [1,]),
                ([self.name+self.short_uuid,], [1,]),
                ([self.name+self.hash,], [1,]),
                ([self.name+self.hash+self.uuid,], [1,]),
                ([self.name+self.uuid+self.hash,], [1,]),
                ([self.name+self.hash+self.short_uuid,], [1,]),
                ([self.name+self.short_uuid+self.hash,], [1,]),]:
            results = self.filter_helper.filter_multiple_by_name_or_id_or_tag_or_hash(
                query_strings)
            for (query_string, expected_count) in zip(query_strings, expected_counts):
                self.assertEqual(len(results[query_string]), expected_count)
                self.assertTrue(self.file_data_object.id in
                                [r.id for r in results[query_string]])

    def testFilterByNameOrIdOrHashNoMatch(self):
        results =self.filter_helper.filter_by_name_or_id_or_tag_or_hash(
            'dont_match_nothing')
        self.assertEqual(results.count(), 0)

    def testFilterByNameOrId(self):
        for (query_string, expected_count) in [
                (self.name, 2),
                (self.uuid, 1),
                (self.short_uuid, 1),
                (self.name+self.uuid, 1),
                (self.name+self.short_uuid, 1),]:
            results = self.filter_helper.filter_by_name_or_id_or_tag(query_string)
            self.assertEqual(results.count(), expected_count)
            self.assertTrue(self.file_data_object.id in [r.id for r in results.all()])

    def testFilterMultipleByNameOrId(self):
        for (query_strings, expected_counts) in [
                ([self.name,], [2,]),
                ([self.uuid,], [1,]),
                ([self.short_uuid, self.name], [1,2]),
                ([self.name+self.uuid, self.name], [1,2]),
        ]:
            results = self.filter_helper.filter_multiple_by_name_or_id_or_tag(
                query_strings)
            for (query_string, expected_count) in zip(query_strings, expected_counts):
                self.assertEqual(len(results[query_string]), expected_count)
                self.assertTrue(self.file_data_object.id in
                                [r.id for r in results[query_string]])

    def testFilterByNameOrIdNoMatch(self):
        results = self.filter_helper.filter_by_name_or_id_or_tag('dont_match_nothing')
        self.assertEqual(results.count(), 0)

    def testParseAsNameOrIdOrHash(self):
        for (input_string, input_name, input_uuid, input_hash_value) in [
                ('name', 'name', None, None),
                ('@uuid', None, 'uuid', None),
                ('$hash', None, None, 'hash'),
                ('name@uuid', 'name', 'uuid', None),
                ('name$hash', 'name', None, 'hash'),
                ('name@uuid$hash', 'name', 'uuid', 'hash'),
                ('name$hash@uuid', 'name', 'uuid', 'hash'),
        ]:
            (name, uuid, tag, hash_value) = self.filter_helper._parse_as_name_or_id_or_tag_or_hash(
                input_string)
            self.assertEqual(name, input_name)
            self.assertEqual(uuid, input_uuid)
            self.assertEqual(hash_value, input_hash_value)

    def testParseAsNameOrId(self):
        for (input_string, input_name, input_uuid) in [
                ('name', 'name', None),
                ('@uuid', None, 'uuid'),
                ('name@uuid', 'name', 'uuid'),
        ]:
            (name, uuid, tag) = self.filter_helper._parse_as_name_or_id_or_tag(
                input_string)
            self.assertEqual(name, input_name)
            self.assertEqual(uuid, input_uuid)


class TestFilterMixin(TestCase):

    def TestFilterByNameOrIdOrHash(self):
        file_data_object = _create_file_data_object()
        query_string = file_data_object.filename
        results = DataObject.filter_by_name_or_id_or_tag_or_hash(query_string)
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().id, file_data_object.id)

    def TestFilterByNameOrId(self):
        file_data_object = _create_file_data_object()
        query_string = file_data_object.filename
        results = DataObject.filter_by_name_or_id_or_tag(query_string)
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().id, file_data_object.id)
            

class TestBase(TestCase):

    def testMetaAppLabel(self):
        file_data_object = _create_file_data_object()
        self.assertEqual(file_data_object.Meta.app_label, 'api')

    def testConcurrentUpdate(self):
        file_data_object = _create_file_data_object()
        file_id = file_data_object.id

        file1 = DataObject.objects.get(id=file_id)
        file2 = DataObject.objects.get(id=file_id)

        file1.filename = 'one'
        file2.flename = 'two'

        file1.save()
        with self.assertRaises(exceptions.ConcurrentModificationError):
            file2.save()
