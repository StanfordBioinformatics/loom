import abc
import copy
import errno
import glob
import logging
import os
import shutil
import sys
import tempfile
import urlparse
import gcloud.storage
import requests

from loom.common import md5calc
from loom.common.exceptions import *
from loom.common.objecthandler import ObjectHandler
from loom.common.logger import StreamToLogger

# Google Storage JSON API imports
from apiclient.http import MediaIoBaseDownload
from oauth2client.client import GoogleCredentials
from oauth2client.client import HttpAccessTokenRefreshError
import apiclient.discovery


def _urlparse(pattern):
    """Like urlparse except it assumes 'file://' if no scheme is specified
    """
    url = urlparse.urlparse(pattern)
    if not url.scheme:
        url = urlparse.urlparse('file://' + os.path.abspath(os.path.expanduser(pattern)))
    return url


def SourceSet(pattern, settings):
    """Factory Method that returns a set of Sources matching the given pattern.
    Each Source represents one source file to be copied.
    """

    url = _urlparse(pattern)

    if url.scheme == 'gs':
        return GoogleStorageSourceSet(pattern, settings)
    elif url.scheme == 'file':
        if url.hostname == 'localhost' or url.hostname is None:
            return LocalSourceSet(pattern, settings)
        else:
            raise Exception("Cannot process file pattern %s. Remote file hosts not supported." % pattern)
    else:
        raise Exception('Cannot recognize file scheme in "%s". '\
                        'Make sure the pattern starts with a supported protocol like gs:// or file://'
                        % pattern)


class AbstractSourceSet:
    """Creates an iterable set of Sources that match the given pattern.
    Pattern may include wildcards.
    """

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __init__(self, pattern, settings):
        pass

    @abc.abstractmethod
    def __iter__(self):
        pass


class LocalSourceSet(AbstractSourceSet):
    """A set of source files on local storage
    """
    
    def __init__(self, pattern, settings):
        url = _urlparse(pattern)
        matches = self._get_matching_files(url.path)
        self.sources = [LocalSource('file://' + path, settings) for path in matches]

    def __iter__(self):
        return self.sources.__iter__()

    def _get_matching_files(self, path):
        all_matches = glob.glob(path)
        return self._remove_directories(all_matches)

    def _remove_directories(self, all_matches):
        return filter(lambda x: os.path.isfile(x), all_matches)


class GoogleStorageSourceSet(AbstractSourceSet):
    """A set of source files on Google Storage
    """

    def __init__(self, pattern, settings):
        self.settings = settings
        self.sources = [GoogleStorageSource(pattern, settings)]

    def __iter__(self):
        return self.sources.__iter__()

    # TODO support wildcards with multiplt matches


def Source(url, settings):
    """Factory method
    """
    parsed_url = _urlparse(url)

    if parsed_url.scheme == 'gs':
        return GoogleStorageSource(url, settings)
    elif parsed_url.scheme == 'file':
        if parsed_url.hostname == 'localhost' or parsed_url.hostname is None:
            return LocalSource(url, settings)
        else:
            raise Exception("Cannot process file url %s. Remote file hosts not supported." % url)
    else:
        raise Exception('Unsupported scheme "%s" in file "%s"' % (parsed_url.scheme, url))


class AbstractSource:
    """A Source represents a single file to be copied.
    """

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __init__(self, url, settings):
        pass

    def hash_and_copy_to(self, destination, hash_function):
        copier = Copier(self, destination)
        return copier.hash_and_copy(hash_function)

    def copy_to(self, destination):
        copier = Copier(self, destination)
        copier.copy()

    def move_to(self, destination):
        copier = Copier(self, destination)
        copier.move()

    @abc.abstractmethod
    def get_hash_value(self, hash_function):
        pass

    @abc.abstractmethod
    def get_url(self):
        pass

    @abc.abstractmethod
    def get_filename(self):
        pass


class LocalSource(AbstractSource):
    """A source file on local storage.
    """

    type = 'local'

    def __init__(self, url, settings):
        self.url = _urlparse(url)

    def get_hash_value(self, hash_function):
        if not hash_function == 'md5':
            raise Exception('Unsupported hash function %s' % hash_function)
        return md5calc.calculate_md5sum(self.get_path())

    def get_url(self):
        return self.url.geturl()

    def get_path(self):
        return self.url.path

    def get_filename(self):
        return os.path.basename(self.get_path())

    def read(self):
        with open(self.get_path()) as f:
            return f.read()

class GoogleStorageSource(AbstractSource):
    """A source file on Google Storage.
    """
    type = 'google_storage'

    def __init__(self, url, settings):
        self.url = _urlparse(url)
        assert self.url.scheme == 'gs'
        self.bucket_id = self.url.hostname
        self.blob_id = self.url.path.lstrip('/')
        if not self.bucket_id or not self.blob_id:
            raise Exception('Could not parse url "%s". Be sure to use the format "gs://bucket/blob_id".' % url)
        
        self.settings = settings

        self.client = gcloud.storage.client.Client(self.settings['PROJECT_ID'])    
        try:
            self.bucket = self.client.get_bucket(self.bucket_id)
            self.blob = self.bucket.get_blob(self.blob_id)
        except HttpAccessTokenRefreshError:
            raise Exception('Failed to access bucket "%s". Are you logged in? Try "gcloud auth login"' % self.bucket_id)


    def get_hash_value(self, hash_function):
        if hash_function == 'md5':
            return self._get_md5_hash_value()
        elif hash_function == 'crcmod32c':
            return self._get_crc32c_hash_value()
        
    def _get_md5_hash_value(self):
        md5_base64 = self.blob.md5_hash
        md5_hex = md5_base64.decode('base64').encode('hex').strip()
        return md5_hex

    def _get_crc32c_hash_value(self):
        return self.blob.crc32c
        
    def get_url(self):
        return self.url.geturl()

    def get_filename(self):
        return os.path.basename(self.blob_id)

    def read(self):
        tempdir = tempfile.mkdtemp()
        dest_file = os.path.join(tempdir, self.get_filename())
        self.copy_to(Destination(dest_file, self.settings))
        with open(dest_file) as f:
            text = f.read()
        os.remove(dest_file)
        os.rmdir(tempdir)
        return text
        
def Destination(url, settings):
    """Factory method
    """
    parsed_url = _urlparse(url)

    if parsed_url.scheme == 'gs':
        return GoogleStorageDestination(url, settings)
    elif parsed_url.scheme == 'file':
        if parsed_url.hostname == 'localhost' or parsed_url.hostname is None:
            return LocalDestination(url, settings)
        else:
            raise Exception("Cannot process file url %s. Remote file hosts not supported." % url)
    else:
        raise Exception('Unsupported scheme "%s" in file "%s"' % (parsed_url.scheme, url))


class AbstractDestination:
    """A Destination represents a path or directory to which a file will be copied
    """

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __init__(self, url, settings):
        pass
    
    @abc.abstractmethod
    def get_url(self):
        pass

    @abc.abstractmethod
    def exists(self):
        pass

    @abc.abstractmethod
    def is_dir(self):
        pass

    @abc.abstractmethod
    def write(self, contents):
        pass

class LocalDestination(AbstractDestination):

    type = 'local'

    def __init__(self, url, settings):
        self.url = _urlparse(url)
        self.settings = settings

    def get_path(self):
        return os.path.abspath(os.path.expanduser(self.url.path))

    def get_url(self):
        return 'file://'+ self.get_path()

    def exists(self):
        return os.path.exists(self.get_path())

    def is_dir(self):
        return os.path.isdir(self.get_path())

    def write(self, contents):
        with open(self.get_path(), 'w') as f:
            f.write(contents)


class GoogleStorageDestination(AbstractDestination):

    type = 'google_storage'

    def __init__(self, url, settings):
        self.settings = settings
        self.url = _urlparse(url)
        assert self.url.scheme == 'gs'
        self.bucket_id = self.url.hostname
        self.blob_id = self.url.path.lstrip('/')
        self.client = gcloud.storage.client.Client(self.settings['PROJECT_ID'])
        try:
            self.bucket = self.client.get_bucket(self.bucket_id)
            self.blob = self.bucket.get_blob(self.blob_id)
        except HttpAccessTokenRefreshError:
            raise Exception('Failed to access bucket "%s". Are you logged in? Try "gcloud auth login"' % self.bucket_id)
        if self.blob is None:
            self.blob = gcloud.storage.blob.Blob(self.blob_id, self.bucket)

    def get_url(self):
        return self.url.geturl()

    def exists(self):
        return self.blob.exists()

    def is_dir(self):
        # No dirs in Google Storage, just blobs
        return False

    def write(self, contents):
        with tempfile.NamedTemporaryFile('w') as f:
            f.write(contents)
            f.flush()
            Source(f.name, self.settings).copy_to(self)


def Copier(source, destination):
    """Factory method to select the right copier for a given source and destination.
    """

    if source.type == 'local' and destination.type == 'local':
        return LocalCopier(source, destination)
    elif source.type == 'local' and destination.type == 'google_storage':
        return Local2GoogleStorageCopier(source, destination)
    elif source.type == 'google_storage' and destination.type == 'local':
        return GoogleStorage2LocalCopier(source, destination)
    elif source.type == 'google_storage' and destination.type == 'google_storage':
        return GoogleStorageCopier(source, destination)
    else:
        raise Exception('Could not find method to copy from source "%s" to destination "%s".'
                        % (source, destination))


class AbstractCopier:
    __metaclass__ = abc.ABCMeta

    def __init__(self, source, destination):
        self.source = source
        self.destination = destination
            
    @abc.abstractmethod
    def hash_and_copy(self, hash_function):
        pass

    @abc.abstractmethod
    def copy(self, hash_function):
        pass

    @abc.abstractmethod
    def move(self):
        pass


class LocalCopier(AbstractCopier):

    def hash_and_copy(self, hash_function):
        # TODO make these concurrent
        hash_value = self.source.get_hash_value(hash_function)
        self.copy()
        return hash_value
        
    def copy(self):
        try:
            os.makedirs(os.path.dirname(self.destination.get_path()))
        except OSError as e:
            if e.errno == errno.EEXIST:
                pass
            else:
                raise e
        shutil.copy(self.source.get_path(), self.destination.get_path())

    def move(self):
        try:
            os.makedirs(os.path.dirname(self.destination.get_path()))
        except OSError as e:
            if e.errno == errno.EEXIST:
                pass
            else:
                raise e
        shutil.move(self.source.get_path(), self.destination.get_path())


class GoogleStorageCopier(AbstractCopier):

    def hash_and_copy(self, hash_function):
        self.copy()
        return self.source.get_hash_value(hash_function)

    def copy(self):
        self.source.bucket.copy_blob(s.source.blob, s.destination.bucket, s.destination.blobid)

    def move(self):
        if not self.source.bucket_id == self.destination.bucket_id:
            raise Exception('"move" operation is not supported between buckets.')
        self.source.bucket.rename_blob(self.source.blob, destination.blobid)


class Local2GoogleStorageCopier(AbstractCopier):

    def hash_and_copy(self, hash_function):
        self.copy()
        return self.destination.get_hash_value(hash_function)

    def copy(self):
        self.destination.blob.upload_from_filename(self.source.get_path())

    def move(self):
        raise Exception('"move" operation is not supported from local to Google Storage.')


class GoogleStorage2LocalCopier(AbstractCopier):

    def hash_and_copy(self, hash_function):
        self.copy()
        return self.source.get_hash_value(hash_function)

    def copy(self):
        self.source.blob.download_to_filename(self.destination.get_path())

    def move(self):
        raise Exception('"move" operation is not supported from Google Storage to local.')


class FileHandler:
    """Abstract base class for filehandlers.
    Public interface and required overrides. Perform file transfer or create 
    locations differently depending on fileserver type.
    """

    def __init__(self, master_url, logger=None):
        self.objecthandler = ObjectHandler(master_url)
        self.settings = self._get_filehandler_settings(master_url)
        self.logger = logger
        stdout_logger = StreamToLogger(self.logger, logging.INFO)
        sys.stdout = stdout_logger
        stderr_logger = StreamToLogger(self.logger, logging.ERROR)
        sys.stderr = stderr_logger

    def _get_filehandler_settings(cls, master_url):
        url = master_url + '/api/file-handler-info/'
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
        filehandler_settings = response.json()['file_handler_info']
        return filehandler_settings

    def _log(self, message):
        if not self.logger:
            return
        self.logger.info(message)

    def import_from_patterns(self, patterns, note):
        for pattern in patterns:
            self.import_from_pattern(pattern, note)

    def import_from_pattern(self, pattern, note):
        for source in SourceSet(pattern, self.settings):
            self.import_file(source.get_url(), note)

    def import_file(self, source_url, note):
        source = Source(source_url, self.settings)
        self._log('Importing file from %s...' % source.get_url())

        file_import = self._create_file_import(source, note)

        temp_destination = Destination(file_import['temp_file_storage_location']['url'], self.settings)
        hash_function = self.settings['HASH_FUNCTION']
        hash_value = source.hash_and_copy_to(temp_destination, hash_function)

        updated_file_import = self._add_file_object_to_file_import(file_import, source, hash_value, hash_function)

        temp_source = Source(temp_destination.get_url(), self.settings)
        final_destination = Destination(updated_file_import['file_storage_location']['url'], self.settings)
        temp_source.move_to(final_destination)

        final_file_import =  self._finalize_file_import(updated_file_import)
        self._log('...finished importing file %s@%s' % (final_file_import['file_data_object']['filename'],
                                           final_file_import['file_data_object']['_id']))
        return final_file_import
    
    def _create_file_import(self, source, note):
        return self.objecthandler.post_file_import({
            'note': note,
            'source_url': source.get_url(),
        })
    
    def _add_file_object_to_file_import(self, file_import, source, hash_value, hash_function):

        update = {
                'file_data_object': {
                    'filename': source.get_filename(),
                    'file_contents': {
                        'hash_function': hash_function,
                        'hash_value': hash_value
                    }}}

        return self.objecthandler.update_file_import(
            file_import['_id'],
            { 'file_data_object': {
                'filename': source.get_filename(),
                'file_contents': {
                    'hash_function': hash_function,
                    'hash_value': hash_value
                }}})

    def _finalize_file_import(self, file_import):
        """ Nullify temp location and mark final location as "complete".
        """
        file_import_update = {
            'temp_file_storage_location': None,
            'file_storage_location': copy.deepcopy(file_import['file_storage_location'])
        }
        file_import_update['file_storage_location']['status'] = 'complete'
        
        return self.objecthandler.update_file_import(
            file_import['_id'],
            file_import_update
        )

    def export_files(self, file_ids, destination_url=None):
        if destination_url is not None and len(file_ids) > 1:
            # destination must be a directory
            if not Destination(destination_url, self.settings).is_dir():
                raise Exception(
                    'Destination must be a directory if multiple files are exported. "%s" is not a directory.'
                    % destination_url)
        for file_id in file_ids:
            self.export_file(file_id, destination_url=destination_url)

    def export_file(self, file_id, destination_url=None):
        # Error raised if there is not exactly one matching file.
        file = self.objecthandler.get_file_data_object_index(file_id, max=1, min=1)[0]

        if not destination_url:
            destination_url = os.getcwd()
        default_name = file['filename']
        destination_url = self.get_destination_file_url(destination_url, default_name)
        destination = Destination(destination_url, self.settings)

        self._log('Exporting file %s%s to %s...' % (file['filename'], file['_id'], destination.get_url()))

        # Copy from the first storage location
        location = self.objecthandler.get_file_storage_locations_by_file(file['_id'])[0]
        Source(location['url'], self.settings).copy_to(destination)

        self._log('...finished exporting file')

    def get_destination_file_url(self, requested_destination, default_name):
        """destination may be a file, a directory, or None
        This function accepts the specified file desitnation, 
        or creates a sensible default that will not overwrite an existing file.
        """
        if requested_destination is None:
            auto_destination = os.path.join(os.getcwd(), default_name)
            destination = self._rename_to_avoid_overwrite(auto_destination)
        elif Destination(requested_destination, self.settings).is_dir():
            auto_destination = os.path.join(requested_destination, default_name)
            destination = self._rename_to_avoid_overwrite(auto_destination)
        else:
            # Don't modify a file destination specified by the user, even if it overwrites something.
            destination = requested_destination
        return self.normalize_url(destination)

    def _rename_to_avoid_overwrite(self, destination_path):
        root = destination_path
        destination = Destination(root, self.settings)
        counter = 0
        while destination.exists():
            counter += 1
            destination_path = '%s(%s)' % (root, counter)
            destination = Destination(destination_path, self.settings)
        return destination_path

    def read_file(self, url):
        return Source(url, self.settings).read()

    def write_to_file(self, url, content):
        Destination(url, self.settings).write(content)

    def normalize_url(self, url):
        return _urlparse(url).geturl()
