from unittest import TestCase
from loomengine.worker.task_runner import TaskRunner
from loomengine.utils.connection import MockConnection

class TestTaskRunner(TestCase):

    def setUp(self):
        parser = TaskRunner.get_parser()
        master_url = 'http://just.a.fake.url'
        args = parser.parse_args(['--server_name', 'test-loom',
                                  '--task_attempt_id', '123',
                                  '--master_url', master_url])
        
        mock_connection = MockConnection(master_url)
        mock_filemanager = 'placeholder'
        self.task_runner = TaskRunner(
            args = args,
            mock_connection=mock_connection,
            mock_filemanager=mock_filemanager)

    def testSaveNonfileOutput(self):
        output_text = 'a space-delimited array of words'
        output = {
            'id': 1,
            'type': 'string',
            'channel': 'words',
            'source': {
                'string': 'stdout',
                'filename': None
            },
            'parser': {
                'type': 'delimited',
                'options': {
                    'delimiter': ' ',
                    'strip': True,
                }
            },
            'mode': 'scatter',
            'data_object': None,
        }
        self.task_runner._save_nonfile_output(output, output_text)

        data_object = self.task_runner.connection.data['data_object']
        self.assertTrue(data_object['is_array'])
        self.assertEqual(data_object.get('value'), output_text.split(' '))


if __name__ == '__main__':
    unittest.main()
