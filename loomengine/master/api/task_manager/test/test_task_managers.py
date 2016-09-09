import logging
import time
import unittest

from django.conf import settings

from api.models import WorkflowRun
#from loomengine.utils import fixtures
from loomengine.utils.testserver import TestServer


logger = logging.getLogger('loom')


class TestTaskManagers(unittest.TestCase):

    def setUp(self):
        self.test_server = TestServer()
        self.test_server.start()
        self.WORKER_TYPE_BEFORE = settings.WORKER_TYPE
        self.MASTER_URL_BEFORE = settings.MASTER_URL_FOR_WORKER

    def tearDown(self):
        self.test_server.stop()
        settings.WORKER_TYPE = self.WORKER_TYPE_BEFORE
        settings.MASTER_URL_FOR_WORKER = self.MASTER_URL_BEFORE

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
