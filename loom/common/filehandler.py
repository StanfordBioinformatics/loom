#!/usr/bin/env python

import abc
from copy import copy
import datetime
import errno
import os
import shutil
import subprocess

import gcloud.storage
import requests

from loom.common import md5calc
from loom.common.exceptions import *
from loom.common.objecthandler import ObjectHandler

# Google Storage JSON API imports
from apiclient.http import MediaIoBaseDownload
from oauth2client.client import GoogleCredentials
import apiclient.discovery


def FileHandler(master_url, *args, **kwargs):
    """Factory method that communicates with master server to retrieve settings 
    and determine which concrete subclass to instantiate.
    """
    settings = _get_settings(master_url)
    if settings['FILE_SERVER_TYPE'] == 'LOCAL':
        return LocalFileHandler(master_url, settings, *args, **kwargs)
    elif settings['FILE_SERVER_TYPE'] == 'REMOTE':
        return RemoteFileHandler(master_url, settings, *args, **kwargs)
    elif settings['FILE_SERVER_TYPE'] == 'GOOGLE_CLOUD':
        return GoogleCloudFileHandler(master_url, settings, *args, **kwargs)
    else:
        raise UnrecognizedFileServerTypeError(
            'Unrecognized file server type: %s' % settings['FILE_SERVER_TYPE'])

def _get_settings(master_url):
    url = master_url + '/api/filehandlerinfo/'
    try:
        response = requests.get(url)
    except requests.exceptions.ConnectionError:
        raise ServerConnectionError(
            'No response from server at %s. Do you need to run "loom server start"?' \
            % master_url)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        raise BadResponseError("%s\n%s" % (e.message, response.text))
    settings = response.json()['filehandlerinfo']
    return settings


class AbstractFileHandler:
    """Abstract base class for filehandlers.
    Public interface and required overrides. Perform file transfer or create 
    locations differently depending on fileserver type.
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, master_url, settings, logger=None):
        self.objecthandler = ObjectHandler(master_url)
        self.settings = settings
        self.logger = logger

    @abc.abstractmethod
    def upload(self, local_path, destination_location):
        pass

    @abc.abstractmethod
    def download(self, source_location, local_path):
        pass

    @abc.abstractmethod
    def get_step_output_location(self, local_path, file_object=None):
        pass

    @abc.abstractmethod
    def get_import_location(self, file_object, timestamp):
        pass

    def _get_import_path(self, file_object, timestamp):
        """Imported files are placed in IMPORT_DIR and named with timestamp, 
        file ID, and filename.
        """
        file_id = file_object.get('_id')
        if file_id is None:
            raise UndefinedFileIDError("File ID must be defined")
        return os.path.join(
            self.settings['FILE_ROOT'],
            self.settings['IMPORT_DIR'],
            "%s_%s_%s" % (timestamp, file_id[0:10], file_object['file_name']),
        )

    def download_by_file_id(self, file_id, local_path):
        storage_locations = self.objecthandler.get_file_storage_locations_by_file(file_id)
        # Attempt to download from each location
        for location in storage_locations:
            if os.path.exists(local_path):
                raise FileAlreadyExistsError('File "%s" already exists' % local_path)
            self.download(location, local_path)
            # TODO handle download failures
            break
    
    def _get_step_output_path(self, local_path):
        """Step outputs are placed in directories of the same name as the
        local directories, and named with the same filename.
        """
        filename = os.path.basename(local_path)
        step_run_dir = os.path.basename(os.path.dirname(local_path))
        workflow_dir = os.path.basename(os.path.dirname(
            os.path.dirname(local_path)))
        workflows_dir = os.path.basename(os.path.dirname(
            os.path.dirname(os.path.dirname(local_path))))
        return os.path.join(
            self.settings['FILE_ROOT'],
            workflows_dir,
            workflow_dir,
            step_run_dir,
            filename
        )

    @classmethod
    def create_file_data_object_from_local_path(cls, file_path, file_name=None):
        if file_name is None:
            file_name = os.path.basename(file_path)
        file_data_object = {
            'file_contents': {
                'hash_value': md5calc.calculate_md5sum(file_path),
                'hash_function': 'md5',
            },
            'file_name': file_name
        }
        return file_data_object

    def _log(self, message):
        if not self.logger:
            return
        self.logger.info(message)
    
    def upload_files_from_local_paths(self, local_paths, file_names=None, source_record=''):
        upload_request_time = self.objecthandler.get_server_time()
        file_objects = []
        destination_locations = []
        if file_names is None:
            file_names = [None] * len(local_paths)
        if len(file_names) != len(local_paths):
            raise WrongNumberOfFileNamesError('Cannot process %s file name(s) for %s file(s). '\
                                              'The lengths must match.' % (len(file_names), len(local_paths)))
            
        # Create Files
        for (local_path, file_name) in zip(local_paths, file_names):
            file_objects.append(self.upload_file_from_local_path(local_path, file_name=file_name))

        # Create source_record if one exists
        self._create_source_record(file_objects, source_record=source_record)

        # Create storage locations
        for file_object in file_objects:
            destination_locations.append(self.get_import_location(file_object, upload_request_time))
        
        # Upload files and post storage locations
        for (local_path, destination_location) in zip(local_paths, destination_locations):
            self.upload(local_path, destination_location)
            self.objecthandler.post_file_storage_location(destination_location)

    def upload_file_from_local_path(self, local_path, file_name=None, source_record=''):
        if file_name is None:
            self._log("Uploading %s ..." % local_path)
        else:
            self._log("Uploading %s as %s ..." % (local_path, file_name))
        file_object = self.create_file_data_object_from_local_path(local_path, file_name=file_name)
        server_file_object = self.objecthandler.post_data_object(file_object)
        # Create source_record if one exists
        self._create_source_record([file_object], source_record=source_record)
        self._log("Created file %s@%s" % (server_file_object['file_name'], server_file_object['_id']))
        return server_file_object

    def _create_source_record(self, data_objects, source_record=None):
        if source_record:
            self.objecthandler.post_data_source_record(
                {'data_objects': data_objects,
                 'source_description': source_record}
            )

    def download_files(self, file_ids, local_names=None, target_directory=None):
        if local_names is None:
            local_names = [None] * len(file_ids)
        if len(local_names) != len(file_ids):
            raise WrongNumberOfFileNamesError('Cannot process %s file_names for %s files. '\
                                              'The lengths must match.' % (len(local_names), len(file_ids)))

        for (file_id, local_name) in zip(file_ids, local_names):
            file = self.objecthandler.get_file_data_object_index(file_id, max=1, min=1)[0]
            # If no local name specified, use the file name from the object.
            if local_name is None:
                local_name = file['file_name']
                # Don't overwrite anyone's root directory based on a file path from the server.
                self._verify_not_absolute(local_name)
            if target_directory is not None:
                # We should never use target directory along with absolute paths.
                if self._is_absolute_path(local_name):
                    raise AbsolutePathInFileNameError('Cannot set download directory since the file name "%s" '\
                                                      'uses an absolute path.' % local_name)
                local_path = os.path.join(os.path.expanduser(target_directory), local_name)
            else:
                local_path = local_name
            self._log('Downloading file %s@%s to %s...' % (file['file_name'], file['_id'], local_path))
            self.download_by_file_id(file['_id'], local_path)
            self._log('...complete.')

    def _verify_not_absolute(self, file_name):
        if self._is_absolute_path(file_name):
            raise AbsolutePathInFileNameError('Refusing to download a file whose name is an absolute path.')

    def _is_absolute_path(self, file_names):
        return any([file_name.startswith('/') for file_name in file_names])


class AbstractPosixPathFileHandler(AbstractFileHandler):
    """Base class for filehandlers that deal with POSIX-style file paths."""
    __metaclass__ = abc.ABCMeta

    def get_step_output_location(self, local_path, file_object=None):
        if file_object is None:
            file_object = create_file_data_object_from_local_path(local_path)
        location = {
            'file_contents': file_object['file_contents'],
            'file_path': self._get_step_output_path(local_path),
            'host_url': self.settings['FILE_SERVER_FOR_WORKER']
            }
        return location

    def get_import_location(self, file_object, timestamp):
        location = {
            'file_contents': file_object['file_contents'],
            'file_path': self._get_import_path(file_object, timestamp),
            'host_url': self.settings['FILE_SERVER_FOR_WORKER']
            }
        return location


class LocalFileHandler(AbstractPosixPathFileHandler):
    """Subclass of FileHandler that uses cp or ln to 'copy' files.
    """
    def upload(self, local_path, destination_location):
        """For imports, create imports directory and copy file.
        For step outputs, don't need to do anything, because the working 
        directory is the destination.
        """
        destination_path = destination_location['file_path']
        if local_path != destination_path:
            try:
                os.makedirs(os.path.dirname(destination_path))
            except OSError as e:
                if e.errno == errno.EEXIST:
                    pass
                else:
                    raise e
            shutil.copyfile(local_path, destination_path)
        return

    def download(self, source_location, local_path):
        """Save space by hardlinking file into the working dir instead of 
        copying. However, won't work if the two locations are on different 
        filesystems.
        """
        cmd = ['ln', source_location['file_path'], local_path]
        subprocess.check_call(cmd)

class RemoteFileHandler(AbstractPosixPathFileHandler):
    """Subclass of FileHandler that uses ssh and scp to copy files."""

    def upload(self, local_path, destination_location):
        destination_path = destination_location['file_path']
        subprocess.check_call(
            ['ssh',
             self.fileserver,
             'mkdir',
             '-p',
             os.path.dirname(destination_path)]
        )
        subprocess.check_call(
            ['scp',
             local_path,
             ':'.join([self.fileserver, destination_path])]
        )

    def download(self, source_location, local_path):
        subprocess.check_call(
            ['scp',
             ':'.join(
                 [source_location['host_url'],
                  source_location['file_path']]
             ),
             local_path]
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

class ElasticlusterFileHandler(AbstractPosixPathFileHandler):
    """ TODO: Use elasticluster and GCE-specific parameters for file transfer. 
    Consider using elasticluster's ssh and sftp commands instead.
    - Would decouple loom from cloud specifics (key management, username, fileserver IP).
    - However, nesting virtualenvs seems problematic, and would have to locate
      elasticluster installation or let user specify.
    """

    def _upload_file_to_elasticluster(self):
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


class GoogleCloudFileHandler(AbstractFileHandler):
    """Subclass of FileHandler that uses the gcloud module to copy files to and from Google Storage."""

    def upload(self, local_path, destination_location):
        blob = self._get_blob(destination_location)
        blob.upload_from_filename(local_path)

    def download(self, source_location, local_path):
        blob = self._get_blob(source_location)
        blob.download_to_filename(local_path)

    def download_with_json_api(self, destination_location, local_path):
        """Download using Google Storage JSON API instead of gcloud-python."""
        blob_path = destination_location['blob_path']
        bucket_id = destination_location['bucket_id']
        credentials = GoogleCredentials.get_application_default()
        service = apiclient.discovery.build('storage', 'v1', credentials=credentials)
        file_request = service.objects().get_media(bucket=bucket_id, object=blob_path)
        with open(local_path, 'w') as local_file:
            downloader = MediaIoBaseDownload(local_file, file_request, chunksize=1024*1024)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    print 'Download %d%%.' % int(status.progress() * 100)
                print 'Download Complete!'

    def _get_blob(self, location):
        """Instantiate, configure, and return a gcloud blob."""
        blob_path = location['blob_path']
        project_id = location['project_id']
        bucket_id = location['bucket_id']
        client = gcloud.storage.client.Client(project_id)
        bucket = client.get_bucket(bucket_id)
        blob = bucket.get_blob(blob_path)
        if blob is None:
            blob = gcloud.storage.blob.Blob(blob_path, bucket)
        return blob

    def get_step_output_location(self, local_path, file_object=None):
        if file_object is None:
            file_object = create_file_data_object_from_local_path(local_path)
        location = {
            'file_contents': file_object['file_contents'],
            'project_id': self.settings['PROJECT_ID'],
            'bucket_id': self.settings['BUCKET_ID'],
            'blob_path': self._get_step_output_path(local_path),
            }
        return location

    def get_import_location(self, file_object, timestamp):
        location = {
            'file_contents': file_object['file_contents'],
            'project_id': self.settings['PROJECT_ID'],
            'bucket_id': self.settings['BUCKET_ID'],
            'blob_path': self._get_import_path(file_object, timestamp),
            }
        return location
