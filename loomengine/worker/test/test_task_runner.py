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
        self.log_file_pointer = tempfile.NamedTemporaryFile(mode='w')
        self.task_run_attempt = copy.deepcopy(fixtures.task_run_attempt)
        self.run_dir = os.path.realpath(tempfile.mkdtemp())
        args=mock.Args(
            run_attempt_id=self.task_run_attempt['id'],
            master_url='http://thistestserver',
            log_level='DEBUG',
            log_file=self.log_file_pointer.name
        )
        worker_settings = {
            'STDOUT_LOG_FILE': os.path.join(self.run_dir, 'logs', 'stdout.log'),
            'STDERR_LOG_FILE': os.path.join(self.run_dir, 'logs', 'stderr.log'),
            'WORKING_DIR': os.path.join(self.run_dir, 'work')
        }
        mock_connection = mock.Connection(worker_settings, self.task_run_attempt)
        mock_filemanager = mock.FileManager()
        self.task_runner = TaskRunner(
            args=args,
            mock_connection=mock_connection,
            mock_filemanager=mock_filemanager
        )

    def tearDown(self):
        self.log_file_pointer.close()
        shutil.rmtree(self.run_dir)

    def testRunHelloTask(self):
        self.task_runner.run()
        self.task_runner.cleanup()
        self.assertEqual(self.task_runner.connection.task_run_attempt['monitor_status'], 'finished')
        self.assertEqual(self.task_runner.connection.task_run_attempt['process_status'], 'finished_successfully')
        self.assertEqual(self.task_runner.connection.task_run_attempt['save_outputs_status'], 'finished_successfully')

    
if __name__=='__main__':
    unittest.main()
