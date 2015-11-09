#!/usr/bin/env python

import datetime
import errno
import json
import logging
import os
import requests
import shutil
import socket
import subprocess

import loom.client.settings_manager
from loom.common import md5calc, filehandler


class LoomUpload:

    def __init__(self, args=None):

        # Parse arguments
        if args is None:
            args=self._get_args()
        self.local_paths = args.files
        settings_manager = loom.client.settings_manager.SettingsManager(settings_file = args.settings, require_default_settings=args.require_default_settings)

        # Get relevant settings
        self.master_url = settings_manager.get_server_url_for_client()
        self.file_server = settings_manager.get_file_server_for_client()
        file_root = settings_manager.get_file_root()
        import_dir = settings_manager.get_import_dir()
        self.import_path = os.path.join(file_root, import_dir)

        file_server_type = settings_manager.get_file_server_type() 

        # Initialize appropriate type of file handler
        if file_server_type == 'LOCAL':
            self.filehandler = filehandler.LocalFileHandler()
        elif file_server_type == 'REMOTE':
            self.filehandler = filehandler.RemoteFileHandler(master_url)
        elif file_server_type == 'GOOGLE_CLOUD':
            self.filehandler = filehandler.GoogleCloudFileHandler(master_url)
        else:
            raise LoomUploadError('Unrecognized file server type %s' % self.filehandler)

    def _get_args(self):
        parser = self.get_parser()
        args = parser.parse_args()
        return args

    @classmethod
    def get_parser(cls):
        import argparse
        parser = argparse.ArgumentParser(description='Register and upload one or more files to loom.')
        parser.add_argument('files', nargs='+')
        parser.add_argument('--settings', '-s', metavar='SETTINGS_FILE', 
                            help="The settings file specifies where and how to upload files. Use loomconfig to create or modify the settings file.")
        parser.add_argument('--require_default_settings', '-d', action='store_true', help=argparse.SUPPRESS)
        return parser

    def run(self):
        for local_path in self.local_paths:
            self.filehandler.import_file(local_path, self.import_path, self.file_server, self.master_url)


class LoomUploadError(Exception):
    pass


if __name__=='__main__':
    response = LoomUpload().run()
