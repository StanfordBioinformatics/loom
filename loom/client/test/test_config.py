#!/usr/bin/env python

from datetime import datetime
import json
import os
import subprocess
import sys
import time
import unittest

from loom.client import config

TEST_SETTINGS_FILE = '/tmp/test_loom_settings.json'
SCRIPT_PATH = config.__file__.rstrip('c')

class TestLoomConfig(unittest.TestCase):

    def setUp(self):
        if os.path.exists(TEST_SETTINGS_FILE):
            os.remove(TEST_SETTINGS_FILE) 
            pass

    def tearDown(self):
        if os.path.exists(TEST_SETTINGS_FILE):
            os.remove(TEST_SETTINGS_FILE) 
            pass

    def test_set_local(self):
        subprocess.call([sys.executable, SCRIPT_PATH, "--settings", TEST_SETTINGS_FILE, "local"])
        self.assertSettingsFileCreated()
        current_preset = TestLoomConfig.getCurrentPreset()
        self.assertEqual(current_preset, 'LOCAL_SETTINGS', 'Current preset in settings file not set to local')

    def assertSettingsFileCreated(self):
        self.assertTrue(os.path.exists(TEST_SETTINGS_FILE), 'Settings file %s was not created' % TEST_SETTINGS_FILE)

    @staticmethod
    def getCurrentPreset():
        with open(TEST_SETTINGS_FILE) as fp:
            settings = json.load(fp)
        return settings['CURRENT_PRESET']


if __name__=='__main__':
    unittest.main()
