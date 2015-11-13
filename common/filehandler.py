#!/usr/bin/env python

import abc
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
    """Abstract base class for filehandlers.
    On instantiation, communicates with master server to retrieve settings and
    determine which concrete subclass to instantiate.
    """
    __metaclass__ = abc.ABCMeta

    def __new__(cls, master_url, fileserver):
        return FileHandler._factory(master_url, fileserver)

    @staticmethod
    def _factory(master_url, fileserver):
        settings = FileHandler._get_settings(master_url)
        if settings['FILE_SERVER_TYPE'] == 'LOCAL':
            return LocalFileHandler(master_url, fileserver, settings)
        elif settings['FILE_SERVER_TYPE'] == 'REMOTE':
            return RemoteFileHandler(master_url, fileserver, settings)
        elif settings['FILE_SERVER_TYPE'] == 'GOOGLE_CLOUD':
            return GoogleCloudFileHandler(master_url, fileserver, settings)
        else:
            raise FileHandlerError('Unrecognized file server type: %s' % settings['FILE_SERVER_TYPE'])

    @staticmethod
    def _get_settings(master_url):
        url = master_url + '/api/filehandlerinfo/'
        response = requests.get(url)
        response.raise_for_status()
        settings = response.json()['filehandlerinfo']
        return settings

    # Required overrides. Perform file transfer or create location differently depending on fileserver type.
    @abc.abstractmethod
    def upload(self, local_path, destination_location):
        pass

    @abc.abstractmethod
    def download(self, source_location, local_path):
        pass

    @abc.abstractmethod
    def get_step_output_destination(self, local_path, file_object=None):
        """Uploaded files are placed in a directory of the same name as the
        local directory, and named with the same filename. 

        Used by LocalFileHandler and RemoteFileHandler; overridden by GoogleCloudFileHandler.
        """
        if file_object is None:
            file_object = create_file_object(local_path)
        location = {
            'file_contents': file_object['file_contents'],
            'file_path': local_path,
            'host_url': self.fileserver
            }
        return location

    @abc.abstractmethod
    def get_import_destination(self, local_path, file_object=None, file_id=None):
        """Imported files are placed in IMPORT_DIR and named with timestamp, file ID, and filename. 

        Used by LocalFileHandler and RemoteFileHandler; overridden by GoogleCloudFileHandler.
        """
        if file_object is None:
            file_object = create_file_object(local_path)
        if file_id is None:
            file_id = post_file_obj(file_object) #TODO: hidden side effect; get file id without posting
        location = {
            'file_contents': file_object['file_contents'],
            'file_path': self._get_import_destination_path(file_id, local_path), 
            'host_url': self.fileserver
            }
        return location

    @abc.abstractmethod
    def _get_import_destination_path(self, file_id, local_path):
        """Overridden by GoogleCloudFileHandler."""
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%Hh%Mm%Ss")
        return os.path.join(
            self.settings['FILE_ROOT'],
            self.settings['IMPORT_DIR'],
            "%s_%s_%s" % (timestamp, file_id[0:10], os.path.split(local_path)[1]),
        )

    @abc.abstractmethod
    def get_step_output_destination(self, local_path, file_object=None):
        """Uploaded files are placed in a directory of the same name as the
        local directory, and named with the same filename. 

        Used by LocalFileHandler and RemoteFileHandler; overridden by GoogleCloudFileHandler.
        """
        if file_object is None:
            file_object = get_file_object(local_path)
        location = {
            'file_contents': file_object['file_contents'],
            'file_path': local_path,
            'host_url': self.fileserver,
            }
        return location

    @abc.abstractmethod
    def get_import_destination(self, local_path, file_object=None, file_id=None):
        """Imported files are placed in IMPORT_DIR and named with timestamp, file ID, and filename. 

        Used by LocalFileHandler and RemoteFileHandler; overridden by GoogleCloudFileHandler.
        """
        if file_object is None:
            file_object = get_file_object(local_path)
        if file_id is None:
            file_id = self._post_file_obj(file_object)
        location = {
            'file_contents': file_object['file_contents'],
            'file_path': self._get_import_destination_path(file_id, local_path), 
            'host_url': self.fileserver
            }
        return location
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


class LocalFileHandler(FileHandler):
    """Subclass of FileHandler that uses cp or ln to 'copy' files."""

    def __new__(cls, master_url, fileserver, settings):
        pass

    def __init__(master_url, fileserver, settings):
        self.master_url = master_url
        self.fileserver = fileserver
        self.settings = settings

    def upload(self, local_path, destination_location):
        destination_path = destination_location['file_path']
        try:
            os.makedirs(os.path.dirname(destination_path))
        except OSError as e:
            if e.errno == errno.EEXIST and os.path.isdir(os.path.dirname(destination_path)):
                pass
            else:
                raise
        shutil.copyfile(local_path, destination_path)

    def download(self, source_location, local_path):
        """Save space by hardlinking file instead of copying. However, won't
        work if the two locations are on different filesystems.
        """
        cmd = ['ln', source_location['file_path'], local_path]
        subprocess.call(cmd, cwd=self.settings['WORKING_DIR'])


class RemoteFileHandler(FileHandler):
    """Subclass of FileHandler that uses ssh and scp to copy files."""

    def __new__(cls, master_url, fileserver, settings):
        pass

    def __init__(master_url, fileserver, settings):
        self.master_url = master_url
        self.fileserver = fileserver
        self.settings = settings

    def upload(self, local_path, destination_location):
        destination_path = destination_location['file_path']
        subprocess.call(
            ['ssh',
             self.fileserver,
             'mkdir',
             '-p',
             os.path.dirname(destination_path)]
             )
        subprocess.call(
            ['scp',
             local_path,
             ':'.join([self.fileserver, destination_path])]
            )

    def download(self, source_location, local_path):
        subprocess.call(
            ['scp',
             ':'.join([source_location['host_url'], source_location['file_path']]),
             local_path]
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


class GoogleCloudFileHandler(FileHandler):
    """Subclass of FileHandler that uses gcloud library to copy files."""

    def __new__(cls, master_url, fileserver, settings):
        pass

    def __init__(master_url, fileserver, settings):
        self.master_url = master_url
        self.fileserver = fileserver
        self.settings = settings

    def get_location(self, file_object, file_path):
        location = {
            'file_contents': file_object['file_contents'],
            'file_path': file_path,
            'bucket_id': self.settings['BUCKET_ID']
            }
        return location



FileHandler.register(LocalFileHandler)
FileHandler.register(RemoteFileHandler)
FileHandler.register(GoogleCloudFileHandler)


# Utility functions used by FileHandler as well as external modules.
def create_file_object(file_path):
    file = {
        'file_contents': {
            'hash_value': md5calc.calculate_md5sum(file_path),
            'hash_function': 'md5',
            }
        }
    return file

def post_file_object(url, file_obj):
    """Register a file object with the server."""
    try:
        response = requests.post(url+'/api/files', data=json.dumps(file_obj))
    except requests.exceptions.ConnectionError as e:
        raise FileHandlerError("No response from server %s\n%s" % (url, e))
    
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        raise FileHandlerError("%s\n%s" % (e.message, response.text))
    return response.json().get('_id')

def post_location(url, file_storage_location_obj):
    """Register a file storage location with the server."""
    try:
        response = requests.post(url+'/api/file_storage_locations', data=json.dumps(file_storage_location_obj))
    except requests.exceptions.ConnectionError as e:
        raise FileHandlerError("No response from server %s\n%s)" % (url, e))
    
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        raise FileHandlerError("%s\n%s" % (e.message, response.text))
    return response.json().get('_id')
