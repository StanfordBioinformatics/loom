import copy
import hashlib
import os
import shutil
import tempfile
import unittest
import yaml


from loomengine_utils import import_manager, file_utils
from loomengine_utils.connection import Connection
from loomengine_utils.exceptions import ImportManagerError
from loomengine_utils.test.test_connection \
    import MockConnection, default_response_data

class TestImportManager(unittest.TestCase):

    token = '12345abcde'

    def setUp(self):
        self.connection = MockConnection('root_url', token=self.token)
        self.import_manager = import_manager.ImportManager(
            self.connection, storage_settings={})
        self.source_directory = tempfile.mkdtemp()
        self.destination_directory = tempfile.mkdtemp()
        self.filenames = ['file0.txt', 'file1.txt', 'file2.txt']
        self.file_paths = []
        self.file_urls = []
        self.md5_sums = []
        for filename in self.filenames:
            file_path = os.path.join(self.source_directory, filename)
            self.file_paths.append(file_path)
            self.file_urls.append('file://'+file_path)
            self.md5_sums.append(self._get_md5(filename))
            with open(file_path, 'w') as f:
                f.write(filename)

    def tearDown(self):
        shutil.rmtree(self.source_directory)
        shutil.rmtree(self.destination_directory)

    def _get_md5(self, data):
        m = hashlib.md5()
        m.update(data)
        return m.hexdigest()

    def testBulkImport(self):
        pass

    def testBulkImportFiles(self):
        pass

    def testBulkImportFile(self):
        pass

    def testBulkImportTemplates(self):
        pass

    def testBulkImportRuns(self):
        def mock_import_file(self, url, comments, **kwargs):
            return url
        self.import_manager.import_file \
            = mock_import_file.__get__(self.import_manager)

        files = self.import_manager._bulk_import_files(
            self.source_directory)
        self.assertEqual(len(files), 3)

    def testImportFromPatterns(self):
        def mock_import_file(self, url, comments, **kwargs):
            return url
        self.import_manager.import_file \
            = mock_import_file.__get__(self.import_manager)
        files = self.import_manager.import_from_patterns(
            [os.path.join(self.source_directory, '*'),], None)
        self.assertEqual(len(files), 3)

    def testGetFileMetadata(self):
        test_metadata = {'test': 'metadata'}
        metadata_path = os.path.join(self.source_directory, 'test.metadata.yaml')
        with open(metadata_path, 'w') as f:
            yaml.dump(test_metadata, f)
        metadata = self.import_manager._get_file_metadata('file://'+metadata_path)
        self.assertEqual(metadata, test_metadata)

    def testGetFileMetadataIgnoreTrue(self):
        test_metadata = {'test': 'metadata'}
        metadata_path = os.path.join(self.source_directory, 'test.metadata.yaml')
        with open(metadata_path, 'w') as f:
            yaml.dump(test_metadata, f)
        metadata = self.import_manager._get_file_metadata('file://'+metadata_path,
                                                          ignore_metadata=True)
        self.assertIsNone(metadata)

    def testGetFileMetadataMissingFile(self):
        metadata_path = os.path.join(self.source_directory, 'test.metadata.yaml')
        metadata = self.import_manager._get_file_metadata('file://'+metadata_path)
        self.assertIsNone(metadata)

    def testGetFileMetadataEmptyFile(self):
        metadata_path = os.path.join(self.source_directory, 'test.metadata.yaml')
        with open(metadata_path, 'w') as f:
            f.write('')
        metadata = self.import_manager._get_file_metadata('file://'+metadata_path)
        self.assertIsNone(metadata)

    def testGetFileMetadataInvalidFormat(self):
        metadata_path = os.path.join(self.source_directory, 'test.metadata.yaml')
        with open(metadata_path, 'w') as f:
            f.write('- not a\nvalid yaml')
        with self.assertRaises(ImportManagerError):
            metadata = self.import_manager._get_file_metadata('file://'+metadata_path)

    def testImportFile(self):
        def mock_get_file_and_metadata_urls(self, url):
            return url, url+'.metadata.yaml'
        def mock_get_file_metadata(self, metadata_url, **kwargs):
            return {}
        def mock_get_source_file(self, url, metadata, **kwargs):
            return None
        def mock_import_file_and_metadata(
                self, source_file,metadata, comments, **kwargs):
            return None
        
        self.import_manager._get_file_and_metadata_urls \
            = mock_get_file_and_metadata_urls.__get__(self.import_manager)
        self.import_manager._get_file_metadata \
            = mock_get_file_metadata.__get__(self.import_manager)
        self.import_manager._get_source_file \
            = mock_get_source_file.__get__(self.import_manager)
        self.import_manager._import_file_and_metadata \
            = mock_import_file_and_metadata.__get__(self.import_manager)

        url = 'file:///some/file'
        comments = None
        self.import_manager.import_file(
            url, comments, link=False, ignore_metadata=False,
            force_duplicates=False, retry=False)
        # Nothing to verify. Just catching syntax errors.

    def testGetFileAndMetadataUrls(self):
        url1 = '/dir/file.metadata.yaml'
        url2 = '/dir/file'
        source_url, metadata_url \
            = self.import_manager._get_file_and_metadata_urls(url1)
        self.assertEqual(url1, metadata_url)
        self.assertEqual(url2, source_url)

        source_url, metadata_url \
            = self.import_manager._get_file_and_metadata_urls(url2)
        self.assertEqual(url1, metadata_url)
        self.assertEqual(url2, source_url)

    def testGetSourceFile(self):
        source_url = 'file://'+os.path.join(self.source_directory, 'file0.txt')
        metadata = {}
        result = self.import_manager._get_source_file(source_url, metadata)
        self.assertEqual(result.get_url(), source_url)

    def testGetSourceFileNoExist(self):
        bad_source_url = 'file://'+os.path.join(self.source_directory, 'nonexist.txt')
        good_source_url = 'file://'+os.path.join(
            self.source_directory, 'file0.txt')

        metadata = {'value': {'file_url': good_source_url}}
        result = self.import_manager._get_source_file(bad_source_url, metadata)
        self.assertEqual(result.get_url(), good_source_url)

    def testGetSourceFileFromMetadata(self):
        original_source_url = '/path/to/file'
        metadata_source_url = '/path/in/metadata'
        metadata = {'value': {'file_url': metadata_source_url}}
        result = self.import_manager._get_source_file_from_metadata(
            original_source_url, metadata)
        self.assertEqual(result.get_path(), metadata_source_url)

    def testGetSourceFileFromMetadataNegInvalidMetadata(self):
        original_source_url = '/path/to/file'
        metadata = {'value': {}}
        with self.assertRaises(ImportManagerError):
            result = self.import_manager._get_source_file_from_metadata(
                original_source_url, metadata)
        
    def testImportFileAndMetadata(self):
        def mock_render_file_data_object_dict(self, source, comments, **kwargs):
            return {}
        def mock_check_for_file_duplicates(self, data_object, **kwargs):
            return data_object
        def mock_execute_file_import(self, data_object, source, **kwargs):
            return data_object

        self.import_manager._render_file_data_object_dict \
            = mock_render_file_data_object_dict.__get__(self.import_manager)
        self.import_manager._check_for_file_duplicates \
            = mock_check_for_file_duplicates.__get__(self.import_manager)
        self.import_manager._execute_file_import \
            = mock_execute_file_import.__get__(self.import_manager)

        self.import_manager.connection.add_route('data-objects/$', 'POST')

        source_path = os.path.join(self.source_directory, 'file0.txt')
        source = file_utils.File(source_path, {})
        metadata = None
        comments = None
        self.import_manager._import_file_and_metadata(source, metadata, comments)

    def testCheckForDuplicatesForceDuplicates(self):
        uuid = 'eebf0f0c-2073-40a9-89f4-caae8ac852f7'
        data_object = {'uuid': uuid}
        self.import_manager.connection.add_route(
            'data-objects/*/',
            'GET',
            content=[])
        result = self.import_manager._check_for_file_duplicates(
            data_object, force_duplicates=True)
        self.assertEqual(result, data_object)

    def testCheckForDuplicates(self):
        uuid = 'eebf0f0c-2073-40a9-89f4-caae8ac852f7'
        filename = 'file.name'
        md5 = 'd0025a317b5e634aa4b079811a5c1951'
        data_object = {'uuid': uuid,
                       'value': {
                           'filename': filename,
                           'md5': md5,
                       }}
        self.import_manager.connection.add_route(
            'data-objects/',
            'GET',
            params={'q': '%s$%s' % (filename, md5), 'type': 'file'},
            content=[])
        self.import_manager.connection.add_route(
            'data-objects/*/',
            'GET',
            content=[])
        result = self.import_manager._check_for_file_duplicates(
            data_object)
        self.assertEqual(data_object, data_object)

    def testCheckForDuplicatesWhenDuplicateExists(self):
        uuid = 'eebf0f0c-2073-40a9-89f4-caae8ac852f7'
        filename = 'file.name'
        md5 = 'd0025a317b5e634aa4b079811a5c1951'
        data_object = {'uuid': uuid,
                       'value': {
                           'filename': filename,
                           'md5': md5,
                       }
        }
        self.import_manager.connection.add_route(
            'data-objects/',
            'GET',
            params={'q': '%s$%s' % (filename, md5), 'type': 'file'},
            content=['first_preexisting', 'second_preexisting'])
        self.import_manager.connection.add_route(
            'data-objects/.*/',
            'GET',
            content='preexisting_model')
        result = self.import_manager._check_for_file_duplicates(
            data_object)
        self.assertEqual(result, data_object)

    def testGetFileDuplicates(self):
        filename = 'file.name'
        md5 = 'd0025a317b5e634aa4b079811a5c1951'
        self.import_manager.connection.add_route(
            'data-objects/', 'GET', params={'q': '%s$%s' % (filename, md5),
                                            'type': 'file'})
        files = self.import_manager._get_file_duplicates(filename, md5)
        self.assertEqual(default_response_data, files)

    def testRenderFileDataObjectDict(self):
        source_path = os.path.join(self.source_directory, 'file0.txt')
        source = file_utils.File(source_path, {})
        comments = None
        file_data_object = self.import_manager._render_file_data_object_dict(
            source, comments)
        self.assertEqual(file_data_object['value']['md5'], self.md5_sums[0])
        self.assertEqual(file_data_object['value']['imported_from_url'],
                         source.get_url())
        self.assertEqual(file_data_object['value']['link'], False)
        self.assertEqual(file_data_object['value']['filename'], 'file0.txt')
        self.assertIsNone(file_data_object['value'].get('import_comments'))

    def testRenderFileDataObjectDictWithComments(self):
        source_path = os.path.join(self.source_directory, 'file0.txt')
        source = file_utils.File(source_path, {})
        comments = 'hmm, nice data'
        file_data_object = self.import_manager._render_file_data_object_dict(
            source, comments)
        self.assertEqual(file_data_object['value']['md5'], self.md5_sums[0])
        self.assertEqual(file_data_object['value']['imported_from_url'],
                         source.get_url())
        self.assertEqual(file_data_object['value']['link'], False)
        self.assertEqual(file_data_object['value']['filename'], 'file0.txt')
        self.assertEqual(file_data_object['value']['import_comments'], comments)

    def testRenderFileDataObjectDictWithConflictingComments(self):
        source_path = os.path.join(self.source_directory, 'file0.txt')
        source = file_utils.File(source_path, {})
        comments = 'hmm, nice data'
        metadata = {'import_comments': 'eww, terrible data'}
        with self.assertRaises(AssertionError):
            file_data_object = self.import_manager._render_file_data_object_dict(
                source, comments, metadata=metadata)

    def testRenderFileDataObjectDictWithConflictingMd5(self):
        source_path = os.path.join(self.source_directory, 'file0.txt')
        source = file_utils.File(source_path, {})
        metadata = {'value': {'md5': '123'}}
        with self.assertRaises(ImportManagerError):
            file_data_object = self.import_manager._render_file_data_object_dict(
                source, None, metadata=metadata)

    def testRenderFileDataObjectDictWithMetadata(self):
        uuid = 'eebf0f0c-2073-40a9-89f4-caae8ac852f7'
        source_path = os.path.join(self.source_directory, 'file0.txt')
        source = file_utils.File(source_path, {})
        comments = None
        metadata_comments = 'eww, terrible data'
        datetime_created = 'MMXVIII'
        metadata = {
            'uuid': uuid,
            'datetime_created': datetime_created,
            'value': {'import_comments': metadata_comments}
        }
        file_data_object = self.import_manager._render_file_data_object_dict(
            source, comments, metadata=metadata)
        self.assertEqual(file_data_object['uuid'], uuid)
        self.assertEqual(file_data_object['datetime_created'], datetime_created)
        self.assertEqual(file_data_object['value']['import_comments'],
                         metadata_comments)

    def testRenderFileDataObjectDictAsLink(self):
        source_path = os.path.join(self.source_directory, 'file0.txt')
        source = file_utils.File(source_path, {})
        comments = None
        file_data_object = self.import_manager._render_file_data_object_dict(
            source, comments, link=True)
        self.assertTrue(file_data_object['value']['link'])
        self.assertEqual(file_data_object['value']['upload_status'], 'complete')

    def testImportResultFile(self):
        output_uuid = 'eebf0f0c-2073-40a9-89f4-caae8ac852f7'
        task_attempt_output = {'uuid': output_uuid}
        file_uuid = '6b79da73-d8f6-49d3-9b5c-1b9121f3a56b'
        source_path = os.path.join(self.source_directory, 'file0.txt')
        source_url = 'file://'+source_path
        destination_path = os.path.join(self.destination_directory, 'file0.txt')
        destination_url = 'file://'+destination_path
        md5 = 'd0025a317b5e634aa4b079811a5c1951'
        filename = 'out.out'
        returned_output = copy.deepcopy(task_attempt_output)
        data_object = {
            'uuid': file_uuid,
            'type': 'file',
            'value': {
                'filename': filename,
                'md5': md5,
                'source_type': 'result',
                'file_url': destination_url
            }}
        returned_output['data'] = {
            'uuid': output_uuid,
            'type': 'file',
            'contents': data_object
        }
        self.connection.add_route('outputs/%s/' % output_uuid, 'PATCH',
                                  content=returned_output)
        self.connection.add_route('data-objects/%s/'%file_uuid, 'PATCH',
                                  content=data_object)
        result = self.import_manager.import_result_file(
            task_attempt_output, source_url)

    def testCreateTaskAttemptOutputFile(self):
        uuid = 'd2c1ea48-4868-41fa-a1ca-6c3957008519'
        task_attempt_output = {'uuid': uuid}
        md5 = 'd0025a317b5e634aa4b079811a5c1951'
        filename = 'out.out'
        self.connection.add_route('outputs/%s/' % uuid, 'PATCH')
        result = self.import_manager._create_task_attempt_output_file(
            task_attempt_output, md5, filename)
        self.assertEqual(result, default_response_data)

    def testImportResultFileList(self):
        output_uuid = 'eebf0f0c-2073-40a9-89f4-caae8ac852f7'
        task_attempt_output = {'uuid': output_uuid}
        file_uuid = '6b79da73-d8f6-49d3-9b5c-1b9121f3a56b'
        source_path = os.path.join(self.source_directory, 'file0.txt')
        source_url = 'file://'+source_path
        destination_path = os.path.join(self.destination_directory, 'file0.txt')
        destination_url = 'file://'+destination_path
        md5 = 'd0025a317b5e634aa4b079811a5c1951'
        filename = 'out.out'
        returned_output = copy.deepcopy(task_attempt_output)
        data_object = {
            'uuid': file_uuid,
            'type': 'file',
            'value': {
                'filename': filename,
                'md5': md5,
                'source_type': 'result',
                'file_url': destination_url
            }}
        returned_output['data'] = {
            'uuid': output_uuid,
            'type': 'file',
            'contents': [data_object,]
        }
        self.connection.add_route('outputs/%s/' % output_uuid, 'PATCH',
                                  content=returned_output)
        self.connection.add_route('data-objects/%s/'%file_uuid, 'PATCH',
                                  content=data_object)
        result = self.import_manager.import_result_file_list(
            task_attempt_output, [source_url,])

    def testCreateTaskAttemptOutputFileArray(self):
        uuid = 'd2c1ea48-4868-41fa-a1ca-6c3957008519'
        task_attempt_output = {'uuid': uuid}
        md5 = 'd0025a317b5e634aa4b079811a5c1951'
        filename = 'out.out'
        self.connection.add_route('outputs/%s/' % uuid, 'PATCH')
        result = self.import_manager._create_task_attempt_output_file_array(
            task_attempt_output, [md5], [filename])
        self.assertEqual(result, default_response_data)

    def testImportLogFile(self):
        task_attempt_uuid = 'd2c1ea48-4868-41fa-a1ca-6c3957008519'
        log_uuid = 'eebf0f0c-2073-40a9-89f4-caae8ac852f7'
        file_uuid = '6b79da73-d8f6-49d3-9b5c-1b9121f3a56b'
        task_attempt = {'uuid': task_attempt_uuid}
        source_path = os.path.join(self.source_directory, 'file0.txt')
        destination_path = os.path.join(self.destination_directory, 'file0.txt')
        data_object = {
            'uuid': file_uuid,
            'value': {
                'upload_status': 'incomplete',
                'filename': 'file0.txt',
                'file_url': 'file://'+destination_path
            }
        }
        log = {
            'uuid': log_uuid,
            'log_name': 'file0.txt',
            'data_object': data_object}
        uploaded_data_object = copy.deepcopy(data_object)
        uploaded_data_object['value']['upload_status'] = 'complete'
        self.connection.add_route(
            'task-attempts/%s/log-files/' % task_attempt_uuid,
            'POST',
            content=log)
        self.connection.add_route('log-files/%s/data-object/'%log_uuid, 'POST',
                                  content=data_object)
        self.connection.add_route('data-objects/%s/'%file_uuid, 'PATCH',
                                  content=uploaded_data_object)
        result = self.import_manager.import_log_file(
            task_attempt, 'file://'+source_path)
        self.assertEqual(result['value']['upload_status'], 'complete')

    def testExecuteFileImport(self):
        uuid = 'eebf0f0c-2073-40a9-89f4-caae8ac852f7'
        source_path = os.path.join(self.source_directory, 'file0.txt')
        destination_path = os.path.join(self.destination_directory, 'file0.txt')
        source = file_utils.File(source_path, {})
        file_data_object = {
            'uuid': uuid,
            'value': {'upload_status': 'incomplete',
                      'file_url': 'file://'+destination_path,
                      'filename': 'file0.txt'
            }}
        uploaded_file_data_object = copy.deepcopy(file_data_object)
        uploaded_file_data_object['value']['upload_status'] = 'complete'
        self.connection.add_route('data-objects/%s/'%uuid, 'PATCH',
                                  content=uploaded_file_data_object)
        result = self.import_manager._execute_file_import(
            file_data_object, source)
        self.assertEqual(result['value']['upload_status'], 'complete')

    def testExecuteFileImportUploadComplete(self):
        source_path = os.path.join(self.source_directory, 'file0.txt')
        source = file_utils.File(source_path, {})
        file_data_object = {
            'uuid': 'eebf0f0c-2073-40a9-89f4-caae8ac852f7',
            'value': {'upload_status': 'complete'
            }}
        result = self.import_manager._execute_file_import(
            file_data_object, source)
        self.assertEqual(result, file_data_object)

    def testSetUploadStatus(self):
        uuid = 'eebf0f0c-2073-40a9-89f4-caae8ac852f7'
        file_data_object = {'uuid': uuid}
        upload_status = 'complete'
        self.connection.add_route('data-objects/%s/'%uuid, 'PATCH')
        result = self.import_manager._set_upload_status(
            file_data_object, upload_status)
        self.assertEqual(result, default_response_data)


if __name__=='__main__':
    unittest.main()
