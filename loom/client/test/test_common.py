#!/usr/bin/env python

import os
import unittest

from loom.client.common import *

class TestClientCommon(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_get_gcloud_project(self):
        get_gcloud_project()
    
    def test_create_delete_service_account(self):
        account_id = 'testserviceaccountid'
        create_service_account(account_id)
        account_email = find_service_account_email(account_id)
        delete_service_account(account_email)

if __name__=='__main__':
    unittest.main()
