#!/usr/bin/env python

import json
import os
import unittest
import tempfile

from loom.client import settings_manager

class TestSettingsManager(unittest.TestCase):

    TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'testdata')

    def test_init(self):
        sm = settings_manager.SettingsManager(skip_init=True)
        sm.settings_file = os.path.join(self.TEST_DATA_DIR, 'path/that/dont/exist')
        sm._initialize()
        
        self.assertEqual(sm.get_webserver_pidfile(), sm.settings['WEBSERVER_PIDFILE'])

    def test_init_from_file(self):
        sm = settings_manager.SettingsManager(settings_file = os.path.join(self.TEST_DATA_DIR, 'testsettings.json'))

        # Verify settings came from saved file
        self.assertEqual(sm.get_webserver_pidfile(), '/tmp/test_xppf_webserver.pid')

    def test_save_settings_to_file(self):
        settingsdir = tempfile.mkdtemp()
        settingsfile = os.path.join(settingsdir, 'settings.json')

        sm = settings_manager.SettingsManager(skip_init=True)
        sm._initialize(settings_file=settingsfile)

        sm.save_settings_to_file()

        # Verify settings file was created with default values
        with open(settingsfile) as f:
            loaded_presets = json.load(f)
        loaded_current_preset = loaded_presets['CURRENT_PRESET']
        default_current_preset = sm.DEFAULT_PRESETS['CURRENT_PRESET']
        self.assertEqual(loaded_presets[loaded_current_preset]['WEBSERVER_PIDFILE'], sm.DEFAULT_PRESETS[default_current_preset]['WEBSERVER_PIDFILE'])
        os.remove(settingsfile)

    def test_delete_saved_settings(self):
        settingsdir = tempfile.mkdtemp()
        settingsfile = os.path.join(settingsdir, 'settings.json')

        sm = settings_manager.SettingsManager(skip_init=True)
        sm._initialize(settings_file=settingsfile)

        sm.save_settings_to_file()
        sm.delete_saved_settings()
    
        self.assertFalse(os.path.exists(settingsfile))

    def test_clean_settings(self):
        sm = settings_manager.SettingsManager(skip_init=True)
        
        with self.assertRaises(Exception):
            sm._clean_settings({'invalid': 'settings'})

    def test_make_settings_directory(self):
        settingsdir = tempfile.mkdtemp()
        settingsfile = os.path.join(settingsdir, 'settingsdir', 'settings.json')
        sm = settings_manager.SettingsManager(skip_init=True)
        sm.settings_file = os.path.join(settingsfile)
        sm.make_settings_directory()

    def test_make_settings_directory_already_exists(self):
        settingsdir = tempfile.mkdtemp()
        settingsfile = os.path.join(settingsdir, 'settings.json')
        sm = settings_manager.SettingsManager(skip_init=True)
        sm.settings_file = os.path.join(settingsfile)
        sm.make_settings_directory()

    def test_remove_dir_if_empty(self):
        settingsdir = tempfile.mkdtemp()
        sm = settings_manager.SettingsManager(skip_init=True)
        sm.remove_dir_if_empty(settingsdir)

        self.assertFalse(os.path.exists(settingsdir))

    def test_remove_dir_if_empty_nonempty(self):
        settingsdir = tempfile.mkdtemp()
        settingsfile = os.path.join(settingsdir, 'file.txt')
        open(settingsfile, 'w+')
        sm = settings_manager.SettingsManager(skip_init=True)
        sm.remove_dir_if_empty(settingsdir)

        self.assertTrue(os.path.exists(settingsdir))
        os.remove(settingsfile)

    # Verify get methods


if __name__ == '__main__':
    unittest.main()
