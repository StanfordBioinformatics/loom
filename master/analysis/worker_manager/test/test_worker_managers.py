from datetime import datetime
import json
import logging
import os
import requests
import subprocess
import sys
import time
import unittest

from django.conf import settings

from analysis.models import RunRequest
from analysis.worker_manager.factory import WorkerManagerFactory
from analysis.worker_manager.cluster import ClusterWorkerManager
from analysis.worker_manager.local import LocalWorkerManager
from xppf.common import fixtures
from xppf.common.testserver import TestServer


logger = logging.getLogger('xppf')


class TestWorkerManagers(unittest.TestCase):

    def setUp(self):
        self.test_server = TestServer()
        self.test_server.start()
        self.WORKER_TYPE_BEFORE = settings.WORKER_TYPE
        self.MASTER_URL_BEFORE = settings.MASTER_URL_FOR_WORKER
        self.RACK_ENV_BEFORE = settings.RACK_ENV
        settings.RACK_ENV = 'test'

    def tearDown(self):
        self.test_server.stop()
        settings.WORKER_TYPE = self.WORKER_TYPE_BEFORE
        settings.MASTER_URL_FOR_WORKER = self.MASTER_URL_BEFORE
        settings.RACK_ENV = self.RACK_ENV_BEFORE

    """
    def test_local_worker_manager(self):
        settings.WORKER_TYPE = 'LOCAL'
        settings.MASTER_URL_FOR_WORKER = 'http://127.0.0.1:8000'
        self._run_hello_world()

        # Give tests some time to finish before shutting down the server. 
        time.sleep(5)
        """

    def test_cluster_worker_manager(self):
        settings.WORKER_TYPE = 'ELASTICLUSTER'
        settings.MASTER_URL_FOR_WORKER = 'http://frontend001:8000'
        self._run_hello_world()

        # Give tests some time to finish before shutting down the server. 
        time.sleep(5)

    def _run_hello_world(self):
        RunRequest.create(fixtures.hello_world_run_request_obj)
        RunRequest.update_and_run()

