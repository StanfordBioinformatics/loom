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

if __name__=='__main__':
    unittest.main()
