#!/usr/bin/env python

import copy
import os
import shutil
import tempfile
import unittest

from loomengine.worker.task_runner import TaskRunner
from loomengine.worker.test import mock
from loomengine.worker.test import fixtures

class TestTaskRunner(unittest.TestCase):

    def setUp(self):
        self.hello_file_pointer = tempfile.NamedTemporaryFile(mode='w')
        self.hello_file_pointer.write('hello')
        self.log_file_pointer = tempfile.NamedTemporaryFile(mode='w')
        self.task_run_attempt = copy.deepcopy(fixtures.task_run_attempt)
        self.task_run_attempt['inputs'][0]['data_object']['file_location']['url'] \
            = 'file://' + self.hello_file_pointer.name
        self.run_dir = tempfile.mkdtemp()
        args=mock.Args(
            run_attempt_id=self.task_run_attempt['id'],
            master_url='http://thistestserver',
            log_level='DEBUG',
            log_file=None #self.log_file_pointer.name
        )
        worker_settings = {
            'STDOUT_LOG_FILE': os.path.join(self.run_dir, 'logs', 'stdout.log'),
            'STDERR_LOG_FILE': os.path.join(self.run_dir, 'logs', 'stderr.log'),
            'WORKING_DIR': os.path.join(self.run_dir, 'work')
        }
        mock_connection = mock.Connection(worker_settings)
        mock_filemanager = mock.FileManager()
        self.task_runner = TaskRunner(
            args=args,
            mock_connection=mock_connection,
            mock_filemanager=mock_filemanager
        )

    def tearDown(self):
        self.hello_file_pointer.close()
        self.log_file_pointer.close()
        shutil.rmtree(self.run_dir)

    def testRunHelloTask(self):
        self.task_runner.run()
        self.assertEqual(self.task_runner.connection.monitor_status, 'finished')
        self.assertEqual(self.task_runner.connection.process_status, 'finished_successfully')
        
            
    
if __name__=='__main__':
    unittest.main()
