#!/usr/bin/env python

import json
import os
import unittest
import tempfile

from loom.client import settings_manager

class TestSettingsManager(unittest.TestCase):

    TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'testdata')

    def test_init(self):
        sm = settings_manager.SettingsManager()

    def test_load_settings_from_file(self):
        sm = settings_manager.SettingsManager()
        testsettings = os.path.join(self.TEST_DATA_DIR, 'testsettings.ini')
        sm.load_settings_from_file(testsettings, section='local')

        # Verify settings came from test settings file
        self.assertEqual(sm.settings['EXTRA_TEST_SETTING'], 'thisisonlyatest')

    def test_save_settings_to_file(self):
        settingsdir = tempfile.mkdtemp()
        settingsfile = os.path.join(settingsdir, 'settings.ini')
        sm = settings_manager.SettingsManager(require_default_settings=True)
        testsettings = os.path.join(self.TEST_DATA_DIR, 'testsettings.ini')
        sm.load_settings_from_file(testsettings, section='local')
        sm.save_settings_to_file(settingsfile, 'local')
        self.assertTrue(os.path.exists(settingsfile))
        os.remove(settingsfile)

    def test_make_settings_directory(self):
        settingsdir = tempfile.mkdtemp()
        settingsfile = os.path.join(settingsdir, 'settingsdir', 'settings.json')
        sm = settings_manager.SettingsManager()
        sm.make_settings_directory(settingsfile)

    def test_make_settings_directory_already_exists(self):
        settingsdir = tempfile.mkdtemp()
        settingsfile = os.path.join(settingsdir, 'settings.json')
        sm = settings_manager.SettingsManager()
        sm.make_settings_directory(settingsfile)

if __name__ == '__main__':
    unittest.main()
