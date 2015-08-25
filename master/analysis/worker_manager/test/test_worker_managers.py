#!/usr/bin/env python

from datetime import datetime
import json
import os
import requests
import subprocess
import time
import unittest

from xppf.master.analysis.test import fixtures
from xppf.utils.testserver import TestServer
from xppf.master.analysis.worker_manager.factory import WorkerManagerFactory
from xppf.master.analysis.worker_manager.cluster import ClusterWorkerManager
from xppf.master.analysis.worker_manager.local import LocalWorkerManager
from analysis.models.work_in_progress import WorkInProgress

class TestWorkerManagers(unittest.TestCase):

    def setUp(self):
        self.test_server = TestServer()
        self.test_server.start()

	work = WorkInProgress._get_queue_singleton()
	work.submit_new_request(fixtures.helloworld_json)
	WorkInProgress.update_and_dry_run()
	WorkInProgress.print_work_in_progress()	
	self.step_run = work.steps_ready_to_run.get()

    def tearDown(self):
        self.test_server.stop()

    def test_local_worker_manager(self):
	manager = LocalWorkerManager()
	proc = manager.run(self.step_run)
	proc.wait()

    def test_cluster_worker_manager(self):
	#manager = ClusterWorkerManager()
	#manager.run(self.step_run)
	pass

if __name__=='__main__':
    unittest.main()
