#!/usr/bin/env python

import datetime
import errno
import json
import os
import requests
import shutil
import subprocess
import logging

from xppf.client import settings_manager
from xppf.common import md5calc


class XppfUploadException(Exception):
    pass


class XppfUpload:

    LOCALHOST = ['localhost', '127.0.0.1']
    IMPORTED_FILES_DIR = 'imported_files'

    def __init__(self, args=None):
        if args is None:
            args=self._get_args()
        self.settings_manager = settings_manager.SettingsManager(settings_file = args.settings, require_default_settings=args.require_default_settings)

        self.local_paths = args.files
        self.file_server = self.settings_manager.get_file_server_for_client() 

    def _get_args(self):
        parser = self.get_parser()
        args = parser.parse_args()
        return args

    @classmethod
    def get_parser(cls):
        import argparse
        parser = argparse.ArgumentParser('xppffile')
        parser.add_argument('files', nargs='+')
        parser.add_argument('--settings', '-s', metavar='SETTINGS_FILE', 
                            help="Settings indicate what server to talk to and how to launch it. Use 'xppfserver savesettings -s SETTINGS_FILE' to save.")
        parser.add_argument('--require_default_settings', '-d', action='store_true', help=argparse.SUPPRESS)
        return parser

    def run(self):

        for local_path in self.local_paths:
            self.local_path = local_path

            print "Calculating md5sum for the file %s" % self.local_path
            file_obj = self._create_file_obj()

            print "Registering file with the XPPF server"
            self.file_id = self._post_file_obj(file_obj)

            print "Copying file to server"
            self._copy_file()

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
            url = self.settings_manager.get_server_url_for_client()
            response = requests.post(url+'/api/files', data=json.dumps(file_obj))
        except requests.exceptions.ConnectionError as e:
            raise Exception("No response from server %s\n%s" % (url, e))
        
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise XppfUploadException("%s\n%s" % (e.message, response.text))
        return response.json().get('_id')

    def _copy_file(self):
        if self._is_localhost():
            path = self.get_remote_path()
            try:
                os.makedirs(os.path.dirname(path))
            except OSError as e:
                if e.errno == errno.EEXIST and os.path.isdir(os.path.dirname(path)):
                    pass
                else:
                    raise
            shutil.copyfile(self.local_path, self.get_remote_path())
        elif self._is_outside_elasticluster():
            """ Use elasticluster and GCE-specific parameters for file transfer. 
            TODO: Consider using elasticluster's ssh and sftp commands instead.
                  - Would decouple XPPF from cloud specifics (key management, username, fileserver IP).
                  - However, nesting virtualenvs seems problematic, and would have to locate
                    elasticluster installation or let user specify.
            """
            username = self.settings_manager.get_remote_username()
            gce_key = os.path.join(os.getenv('HOME'),'.ssh','google_compute_engine')
            if not os.path.exists(gce_key):
                raise Exception("GCE key not found at %s" % gce_key)
            print "Creating working directory on elasticluster at %s" % self.file_server
            subprocess.check_call(
                ['ssh',
                 username+'@'+self.file_server,
                 '-i',
                 gce_key,
                 'mkdir',
                 '-p',
                 os.path.dirname(self.get_cluster_remote_path(username))]
                 )
            print "Uploading file to elasticluster at %s" % self.file_server
            subprocess.check_call(
                ['scp',
                 '-i',
                 gce_key,
                 self.local_path,
                 ':'.join([username+'@'+self.file_server, self.get_cluster_remote_path(username)])]
                )

        else:
            subprocess.call(
                ['ssh',
                 self.file_server,
                 'mkdir',
                 '-p',
                 os.path.dirname(self.get_remote_path())]
                 )
            subprocess.call(
                ['scp',
                 self.local_path,
                 ':'.join([self.file_server, self.get_remote_path()])]
                )

    def _is_outside_elasticluster(self):
        return self.settings_manager.get_client_type() in ('OUTSIDE_ELASTICLUSTER')

    def _is_localhost(self):
        return self.file_server in self.LOCALHOST

    def get_remote_path(self):
        if not hasattr(self,'_remote_path'):
            timestamp = datetime.datetime.now().strftime("%Y%m%d-%Hh%Mm%Ss")
            self._remote_path = os.path.join(
                self.settings_manager.get_file_root(),
                self.IMPORTED_FILES_DIR,
                "%s_%s_%s" % (timestamp, self.file_id[0:10], os.path.split(self.local_path)[1]),
            )
        return self._remote_path

    def get_cluster_remote_path(self, username):
        if not hasattr(self,'_remote_path'):
            timestamp = datetime.datetime.now().strftime("%Y%m%d-%Hh%Mm%Ss")
            self._remote_path = os.path.join(
                '/home',
                username,
                'working_dir',
                self.IMPORTED_FILES_DIR,
                "%s_%s_%s" % (timestamp, self.file_id[0:10], os.path.split(self.local_path)[1]),
            )
        return self._remote_path

    def _create_file_location_obj(self, file_obj):
        return {
            'file': file_obj,
            'file_path': self.get_remote_path(),
            'host_url': self.file_server,
            }

    def _post_file_location_obj(self, file_location_obj):
        try:
            url = self.settings_manager.get_server_url_for_client()
            response = requests.post(url+'/api/file_locations', data=json.dumps(file_location_obj))
        except requests.exceptions.ConnectionError as e:
            raise Exception("No response from server %s\n%s)" % (url, e))
        
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise XppfUploadException("%s\n%s" % (e.message, response.text))
        return response.json().get('_id')


if __name__=='__main__':
    response =  XppfUpload().run()
