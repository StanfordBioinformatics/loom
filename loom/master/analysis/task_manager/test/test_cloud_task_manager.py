#!/usr/bin/env python
import sys
import unittest

from django.conf import settings

import libcloud.compute.base

from loom.master.analysis.task_manager import cloud 
from loom.common.helper import on_gcloud_vm


@unittest.skipIf(not on_gcloud_vm(), 'not running on Google Compute Engine VM')
class TestCloudTaskManager(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        settings.configure()

    @classmethod
    def tearDownClass(cls):
        pass
        
    def setUp(self):
        settings.BASE_DIR = ''
        settings.MASTER_TYPE = 'GOOGLE_CLOUD'
        settings.PROJECT_ID = 'gbsc-gcp-project-scgs-dev'

    def tearDown(self):
        pass

    def test_get_driver(self):
        cloud_driver = cloud.CloudTaskManager._get_cloud_driver()
        
    def test_invalid_cloud_type(self):
        settings.MASTER_TYPE = 'INVALID_CLOUD_TYPE'

        with self.assertRaises(cloud.CloudTaskManagerError):
            cloud_driver = cloud.CloudTaskManager._get_cloud_driver()

    def test_get_gcloud_pricelist(self):
        pricelist = cloud.CloudTaskManager._get_gcloud_pricelist()
        self.assertIsInstance(pricelist, dict)

    def test_get_cheapest_instance_type(self):
        """ May need to be updated if prices change.""" 
        cheapest_type = cloud.CloudTaskManager._get_cheapest_instance_type(cores=1, memory=4)
        self.assertEquals(cheapest_type, 'n1-standard-2')
        
    def test_huge_instance_request(self):
        """ May need to be updated if Google starts offering supercomputer instances.""" 
        with self.assertRaises(cloud.CloudTaskManagerError):
            cloud.CloudTaskManager._get_cheapest_instance_type(cores=sys.maxint, memory=sys.float_info.max)

    def test_vm_bootup(self):
        cloud_driver = cloud.CloudTaskManager._get_cloud_driver()
        node = cloud_driver.create_node(name='test', size='n1-standard-1', image='container-vm', location='us-central1-a')
        self.assertIsInstance(node, libcloud.compute.base.Node)


if __name__ == '__main__':
    unittest.main()
