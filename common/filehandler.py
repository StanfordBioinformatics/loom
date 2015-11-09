#!/usr/bin/env python

import datetime
import errno
import json
import logging
import os
import shutil
import socket
import subprocess

import gcloud
import requests

from loom.common import md5calc


class FileHandlerError(Exception):
    pass


class FileHandler:

    def __init__(self):
        pass

    def upload_file(self, local_path, step_dir, file_server, master_url):
        """Uploaded files are placed in step_dir and named with filename.""" 
        self.local_path = local_path
        self.step_dir = step_dir
        self.file_server = file_server
        self.master_url = master_url

        self._register_file()
        self.remote_path = self.get_remote_upload_path()
        self._register_file_storage_location()

        print "Copying file to server"
        self._upload_file()

    def import_file(self, local_path, import_dir, file_server, master_url):
        """Imported files are placed in import_dir and named with timestamp, file ID, and filename.""" 
        self.local_path = local_path
        self.import_dir = import_dir
        self.file_server = file_server
        self.master_url = master_url

        self._register_file()
        self.remote_path = self.get_remote_import_path()
        self._register_file_storage_location()

        print "Copying file to server"
        self._upload_file()

    def download(self, local_path):
        self.local_path = local_path

        print "Copying file from server"
        self._download_file()

    def _register_file(self):
        print "Calculating md5sum for the file %s" % self.local_path
        self.file_obj = self._create_file_obj()

        print "Registering file with the loom server"
        self.file_id = self._post_file_obj(self.file_obj)

    def _register_file_storage_location(self):
        file_storage_location_obj = self._create_file_storage_location_obj(self.file_obj)
        file_storage_location_id = self._post_file_storage_location_obj(file_storage_location_obj)

    def _create_file_obj(self):
        return {
            'file_contents': self._create_file_contents_obj()
            }

    def _create_file_contents_obj(self):
        return {
            'hash_value': md5calc.calculate_md5sum(self.local_path),
            'hash_function': 'md5',
            }

    def _post_file_obj(self, file_obj):
        try:
            url = self.master_url
            response = requests.post(url+'/api/files', data=json.dumps(file_obj))
        except requests.exceptions.ConnectionError as e:
            raise FileHandlerError("No response from server %s\n%s" % (url, e))
        
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise FileHandlerError("%s\n%s" % (e.message, response.text))
        return response.json().get('_id')

    def get_remote_import_path(self):
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%Hh%Mm%Ss")
        return os.path.join(
            self.import_dir,
            "%s_%s_%s" % (timestamp, self.file_id[0:10], os.path.split(self.local_path)[1]),
        )

    def get_remote_upload_path(self):
        return os.path.join(
            self.step_dir,
            os.path.split(self.local_path)[1]
        )

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

    def _create_file_storage_location_obj(self, file_obj):
        return {
            'file_contents': file_obj['file_contents'],
            'file_path': self.remote_path,
            'host_url': self.file_server,
            }
        return {
            'file_contents': file_obj['file_contents'],
            'google_cloud_project_id': 'asdf',
            'bucket': 'asdf',
            'path': 'asdf'
            }

    def _post_file_storage_location_obj(self, file_storage_location_obj):
        try:
            url = self.master_url
            response = requests.post(url+'/api/file_storage_locations', data=json.dumps(file_storage_location_obj))
        except requests.exceptions.ConnectionError as e:
            raise FileHandlerError("No response from server %s\n%s)" % (url, e))
        
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise FileHandlerError("%s\n%s" % (e.message, response.text))
        return response.json().get('_id')


class LocalFileHandler(FileHandler):
    """Subclass of FileHandler that uses cp to copy files."""

    def __init__(self):
        pass

    def _upload_file(self):
        path = self.remote_path
        try:
            os.makedirs(os.path.dirname(path))
        except OSError as e:
            if e.errno == errno.EEXIST and os.path.isdir(os.path.dirname(path)):
                pass
            else:
                raise
        shutil.copyfile(self.local_path, path)


class GoogleCloudFileHandler(FileHandler):
    """Subclass of FileHandler that uses gcloud library to copy files."""

    def __init__(self, master_url, project_id, bucket, file_root):
        super(GoogleCloudFileHandler, self).__init__(master_url)
        self.project_id = project_id
        self.bucket = bucket
        self.file_root = file_root


class RemoteFileHandler(FileHandler):
    """Subclass of FileHandler that uses ssh and scp to copy files."""

    def __init__(self, master_url, file_server, file_root):
        super(RemoteFileHandler, self).__init__(master_url)
        self.file_server = file_server

    def _upload_file(self):
        subprocess.call(
            ['ssh',
             self.file_server,
             'mkdir',
             '-p',
             os.path.dirname(self.remote_path)]
             )
        subprocess.call(
            ['scp',
             self.local_path,
             ':'.join([self.file_server, self.remote_path])]
            )

    def _upload_file_to_elasticluster(self):
        """ Use elasticluster and GCE-specific parameters for file transfer. 
        TODO: Consider using elasticluster's ssh and sftp commands instead.
              - Would decouple loom from cloud specifics (key management, username, fileserver IP).
              - However, nesting virtualenvs seems problematic, and would have to locate
                elasticluster installation or let user specify.
        """
        username = self.settings_manager.get_remote_username()
        gce_key = os.path.join(os.getenv('HOME'),'.ssh','google_compute_engine')
        if not os.path.exists(gce_key):
            raise FileHandlerError("GCE key not found at %s" % gce_key)
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

    def _download_file(self):
        subprocess.call(
            ['scp',
             ':'.join([self.file_server, self.remote_path]),
             self.local_path]
            )
