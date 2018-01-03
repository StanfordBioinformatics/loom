import datetime
import hashlib
import json
import os
import shutil
import tempfile
import unittest
import uuid

from loomengine_utils import export_manager, md5calc
from loomengine_utils.connection import Connection
from loomengine_utils.test.test_connection import MockConnection

class TestExportManagerFunctions(unittest.TestCase):
    
    def testReplaceNoneWithEmptyList(self):
        empty1 = None
        not_empty1 = [1,2,3]
        empty2 = export_manager._replace_none_with_empty_list(empty1)
        not_empty2 = export_manager._replace_none_with_empty_list(not_empty1)
        self.assertEqual(empty2, [])
        self.assertEqual(not_empty1, not_empty2)

    def testGetDefaultDestinationDirectory(self):
        dir1 = export_manager._get_default_bulk_export_directory()
        self.assertTrue(dir1.startswith(
            os.path.join(os.getcwd(), 'loom-bulk-export-')))


class TestExportManager(unittest.TestCase):

    token = '12345abcde'
    
    def setUp(self):
        self.connection = MockConnection('root_url', token=self.token)
        self.export_manager = export_manager.ExportManager(
            self.connection, storage_settings={})
        self.source_dir = tempfile.mkdtemp()
        self.destination_directory = tempfile.mkdtemp()
        self.filenames = ['file0.txt', 'file1.txt', 'file2.txt']
        self.file_paths = []
        self.file_urls = []
        self.md5_sums = []
        for filename in self.filenames:
            file_path = os.path.join(self.source_dir, filename)
            self.file_paths.append(file_path)
            self.file_urls.append('file://'+file_path)
            self.md5_sums.append(self._get_md5(filename))
            with open(file_path, 'w') as f:
                f.write(filename)

    def tearDown(self):
        shutil.rmtree(self.source_dir)
        shutil.rmtree(self.destination_directory)

    def _get_md5(self, data):
        m = hashlib.md5()
        m.update(data)
        return m.hexdigest()
        
    def _get_data_object(self, filename, md5, file_url):
        data_object_id = str(uuid.uuid4())
        return {
            'uuid': data_object_id,
            'url': 'http://127.0.0.1:8000/api/data-objects/%s/' % data_object_id,
            'type': 'file',
            'datetime_created': datetime.datetime.now().strftime('%Y-%m-%dT%H.%M.%SZ'),
            'value': {
                'filename': 'filename',
                'file_url': file_url,
                'source_type': 'imported',
                'upload_status': 'complete',
                'link': False,
                'md5': md5,
            }}

    def testExportFile(self):
        data_object = self._get_data_object(
            self.filenames[0], self.md5_sums[0], self.file_urls[0])
        self.connection.add_route(
            'data-objects/',
            'GET',
            params={'q': '@%s'%data_object.get('uuid'),
                    'type': 'file'},
            content=[data_object,])
        self.export_manager.export_file(
            '@%s' % data_object.get('uuid'),
            destination_directory=self.destination_directory)

        destination_file = os.path.join(
            self.destination_directory, self.file_paths[0])
        self.assertTrue(os.path.exists(destination_file))
        dest_md5 = md5calc.calculate_md5sum(destination_file)
        self.assertEqual(dest_md5, data_object['value']['md5'])

    def testBulkExportFile(self):
        data_object = self._get_data_object(
            self.filenames[0], self.md5_sums[0], self.file_urls[0])
        self.connection.add_route(
            'data-objects/',
            'GET',
            params={'q': '@%s'%data_object.get('uuid'),
                    'type': 'file'},
            content=[data_object,])
        self.export_manager.bulk_export(
            files=[data_object,], destination_directory=self.destination_directory)
        destination_file = os.path.join(
            self.destination_directory, 'files', self.file_paths[0])
        self.assertTrue(os.path.exists(destination_file))
        dest_md5 = md5calc.calculate_md5sum(destination_file)
        self.assertEqual(dest_md5, data_object['value']['md5'])

        
if __name__=='__main__':
    unittest.main()
