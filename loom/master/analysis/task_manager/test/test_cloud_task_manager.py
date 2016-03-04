#!/usr/bin/env python
import logging
import unittest

from django.conf import settings
settings.configure()

logger = logging.getLogger('loom')


class TestCloudTaskManager(unittest.TestCase):

    def setUp(self):
        settings.BASE_DIR = ''
        settings.MASTER_TYPE = 'GOOGLE_CLOUD'
        settings.PROJECT_ID = 'gbsc-gcp-project-scgs-dev'

    def tearDown(self):
        pass

    def test_get_driver(self):
        from loom.master.analysis.task_manager import cloud 
        cloud_task_manager = cloud.CloudTaskManager()
        cloud_driver = cloud_task_manager._get_cloud_driver()
        
    def test_invalid_cloud_type(self):
        settings.MASTER_TYPE = 'INVALID_CLOUD_TYPE'
        from loom.master.analysis.task_manager import cloud 
        cloud_task_manager = cloud.CloudTaskManager()

        with self.assertRaises(cloud.CloudTaskManagerError):
            cloud_driver = cloud_task_manager._get_cloud_driver()

    """
    def test_local_worker_manager(self):
        settings.WORKER_TYPE = 'LOCAL'
        settings.MASTER_URL_FOR_WORKER = 'http://127.0.0.1:8000'
        self._run_hello_world()

        # Give tests some time to finish before shutting down the server. 
        time.sleep(5)

    def test_cluster_worker_manager(self):
        settings.WORKER_TYPE = 'ELASTICLUSTER'
        settings.MASTER_URL_FOR_WORKER = 'http://frontend001:8000'
        self._run_hello_world()

        # Give tests some time to finish before shutting down the server. 
        time.sleep(5)

    def _run_hello_world(self):
        Workflow.create(fixtures.hello_world_workflow_struct)
        Workflow.update_and_run()

    """

if __name__ == '__main__':
    unittest.main()
