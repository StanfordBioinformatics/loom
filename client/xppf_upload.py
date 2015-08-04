#!/usr/bin/env python

import json
import os
import requests
import shutil
import subprocess

from xppf.client import settings_manager
from xppf.utils import md5calc


class XppfUploadException(Exception):
    pass


class XppfUpload:

    LOCALHOST = ['localhost', '127.0.0.1']

    def __init__(self, args=None):
        if args is None:
            args=self._get_args()
        self.settings_manager = settings_manager.SettingsManager(settings_file = args.settings, require_default_settings=args.require_default_settings)

        self.local_path = args.file
        self.hostname = self.settings_manager.get_file_server() 
        self.remote_path = self._init_remote_path()

    def _get_args(self):
        parser = self.get_parser()
        args = parser.parse_args()
        return args

    @classmethod
    def get_parser(cls):
        import argparse
        parser = argparse.ArgumentParser('xppffile')
        parser.add_argument('file')
        parser.add_argument('--settings', '-s', metavar='SETTINGS_FILE', 
                            help="Settings indicate what server to talk to and how to launch it. Use 'xppfserver savesettings -s SETTINGS_FILE' to save.")
        parser.add_argument('--require_default_settings', '-d', action='store_true', help=argparse.SUPPRESS)
        return parser

    def run(self):

        print "Calculating md5sum for the file %s" % self.local_path
        file_obj = self._create_file_obj()

        print "Registering file with the XPPF server"
        file_id = self._post_file_obj(file_obj)

        print "Copying file to server"
        self._rsync_file()

        file_location_obj = self._create_file_location_obj(file_obj)
        file_location_id = self._post_file_location_obj(file_location_obj)

        return

    def _create_file_obj(self):
        return {
            'hash_value': md5calc.calculate_md5sum(self.local_path),
            'hash_function': 'md5',
            }

    def _post_file_obj(self, file_obj):
        try:
            response = requests.post(self.settings_manager.get_server_url()+'/api/files', data=json.dumps(file_obj))
        except requests.exceptions.ConnectionError as e:
            raise Exception("No response from server. (%s)" % e)
        
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise XppfUploadException("%s\n%s" % (e.message, response.text))
        return response.json().get('_id')

    def _rsync_file(self):
        if self._is_localhost():
            shutil.copyfile(self.local_path, self.remote_path)
        else:
            subprocess.call(
                ['scp',
                 self.local_path,
                 ':'.join([self.hostname, self.remote_path])]
                )

    def _is_localhost(self):
        return self.hostname in self.LOCALHOST

    def _init_remote_path(self):
        return os.path.join(
            self.settings_manager.get_file_root(),
            os.path.split(self.local_path)[1],
            )

    def _create_file_location_obj(self, file_obj):
        return {
            'file': file_obj,
            'file_path': self.remote_path,
            'host_url': self.hostname
            }

    def _post_file_location_obj(self, file_location_obj):
        try:
            response = requests.post(self.settings_manager.get_server_url()+'/api/file_locations', data=json.dumps(file_location_obj))
        except requests.exceptions.ConnectionError as e:
            raise Exception("No response from server. (%s)" % e)
        
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise XppfUploadException("%s\n%s" % (e.message, response.text))
        return response.json().get('_id')


if __name__=='__main__':
    response =  XppfUpload().run()
