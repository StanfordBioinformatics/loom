#!/usr/bin/env python

from datetime import datetime
import json
import os
import requests
import subprocess
import sys
import time
import unittest
import logging

from django.conf import settings

sys.path.append(os.path.join(settings.BASE_DIR, '../../..'))
from loom.common import fixtures
from loom.common.testserver import TestServer
from loom.master.analysis.worker_manager.factory import WorkerManagerFactory
from loom.master.analysis.worker_manager.cluster import ClusterWorkerManager
from loom.master.analysis.worker_manager.local import LocalWorkerManager
from analysis.models.work_in_progress import WorkInProgress

logger = logging.getLogger('loom')

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

    def test_local_worker_manager(self):
        settings.WORKER_TYPE = 'LOCAL'
        settings.MASTER_URL_FOR_WORKER = 'http://127.0.0.1:8000'
        self._run_helloworld()

        # Give tests some time to finish before shutting down the server. 
        time.sleep(5)

    def test_cluster_worker_manager(self):
        settings.WORKER_TYPE = 'ELASTICLUSTER'
        settings.MASTER_URL_FOR_WORKER = 'http://frontend001:8000'
        self._run_helloworld()

        # Give tests some time to finish before shutting down the server. 
        time.sleep(5)

    def _run_helloworld(self):
        WorkInProgress.submit_new_request(fixtures.helloworld_json)
        WorkInProgress.update_and_run()

if __name__=='__main__':
    unittest.main()
