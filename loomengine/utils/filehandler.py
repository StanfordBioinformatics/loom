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

    # TODO support wildcards with multiple matches


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


    def copy_to(self, destination):
        copier = Copier(self, destination)
        copier.copy()

    def move_to(self, destination):
        copier = Copier(self, destination)
        copier.move()

    @abc.abstractmethod
    def calculate_hash_value(self, hash_function):
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

    def calculate_hash_value(self, hash_function):
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

    def delete(self):
        os.remove(self.get_path())


class GoogleStorageSource(AbstractSource):
    """A source file on Google Storage.
    """
    type = 'google_storage'
    
    # CHUNK_SIZE must be multiple of 256.
    # 2016-08-30: With default 1024*1024, download is 20x slower than gsutil.
    CHUNK_SIZE = 1024*1024*100 

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
            self.blob.chunk_size = self.CHUNK_SIZE
        except HttpAccessTokenRefreshError:
            raise Exception('Failed to access bucket "%s". Are you logged in? Try "gcloud auth login"' % self.bucket_id)


    def calculate_hash_value(self, hash_function):
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

    def delete(self):
        self.blob.delete()


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
    def write(self, content):
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

    def write(self, content):
        with open(self.get_path(), 'w') as f:
            f.write(content)


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

    def write(self, content):
        with tempfile.NamedTemporaryFile('w') as f:
            f.write(content)
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
    def copy(self, hash_function):
        pass

    @abc.abstractmethod
    def move(self):
        pass


class LocalCopier(AbstractCopier):

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

    def copy(self):
        self.source.bucket.copy_blob(self.source.blob, self.destination.bucket, self.destination.blob_id)

    def move(self):
        if not self.source.bucket_id == self.destination.bucket_id:
            raise Exception('"move" operation is not supported between buckets.')
        self.source.bucket.rename_blob(self.source.blob, self.destination.blob_id)


class Local2GoogleStorageCopier(AbstractCopier):

    def copy(self):
        self.destination.blob.upload_from_filename(self.source.get_path())

    def move(self):
        raise Exception('"move" operation is not supported from local to Google Storage.')


class GoogleStorage2LocalCopier(AbstractCopier):

    def copy(self):
        try:
            os.makedirs(os.path.dirname(self.destination.get_path()))
        except OSError as e:
            if e.errno == errno.EEXIST:
                pass
            else:
                raise e
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
        self.settings = self.objecthandler.get_filehandler_settings()
        self.logger = logger
        stdout_logger = StreamToLogger(self.logger, logging.INFO)
        sys.stdout = stdout_logger
        stderr_logger = StreamToLogger(self.logger, logging.ERROR)
        sys.stderr = stderr_logger

    def _log(self, message):
        if not self.logger:
            return
        self.logger.info(message)

    def import_from_patterns(self, patterns, note):
        for pattern in patterns:
            self.import_from_pattern(pattern, note)

    def import_from_pattern(self, pattern, note):
        for source in SourceSet(pattern, self.settings):
            self.import_file(
                source.get_url(),
                note
            )

    def import_file(self, source_url, note):
        return self._execute_file_import(
            self._create_file_data_object_for_import(source_url, note),
            source_url
        )

    def _create_file_data_object_for_import(self, source_url, note):
        return self.objecthandler.post_data_object({
            'source_type': 'imported',
            'file_import': {
                'note': note,
                'source_url': Source(source_url, self.settings).get_url(),
                }
        })

    def import_result_file(self, task_run_attempt_output, source_url):
        file_data_object = self._execute_file_import(
            self._create_task_run_attempt_output_file(task_run_attempt_output),
            source_url
        )
        return file_data_object

    def _create_task_run_attempt_output_file(self, task_run_attempt_output):
        updated_task_run_attempt_output = self.objecthandler.update_task_run_attempt_output(
            task_run_attempt_output['id'],
            {
                'data_object': {
                    'source_type': 'result',
                }})
        return updated_task_run_attempt_output['data_object']

    def import_log_file(self, task_run_attempt, source_url):
        log_name = os.path.basename(source_url)
        log_file = self.objecthandler.post_task_run_attempt_log_file(task_run_attempt['id'], {'log_name': log_name})
        return self._execute_file_import(
            log_file['file_data_object'],
            source_url
        )

    def _execute_file_import(self, file_data_object, source_url):
        # Prior to import, file_data_object should have no content and no
        # location
        assert file_data_object.get('file_location') is None
        assert file_data_object.get('file_content') is None

        source = Source(source_url, self.settings)
        self._log('Importing file from %s...' % source.get_url())

        hash_function = self.settings['HASH_FUNCTION']
        self._log('   calculating %s hash...' % hash_function)
        hash_value = source.calculate_hash_value(hash_function)

        # Adding file_content will cause a file_location with status=incomplete
        # to be added to file_data_object
        # If the server is configured not to save multiple files with
        # identical content, the data_object.file_location may have
        # status=complete, indicating that no re-upload is needed.
        #
        file_data_object = self._add_file_content_to_data_object(
            file_data_object,
            source.get_filename(),
            hash_value,
            hash_function
        )

        if file_data_object['file_location']['status'] == 'complete':
            self._log('   server already has the file. Skipping upload.')
        else:
            destination = Destination(
                file_data_object['file_location']['url'],
                self.settings)
            self._log('   copying to destination %s...' % destination.get_url())
            source.copy_to(destination)

        # Signal that the upload completed successfully
        file_data_object = self._flag_upload_as_complete(file_data_object)
        self._log('   imported file %s@%s' % (
            file_data_object['file_content']['filename'],
            file_data_object['id']))
        return file_data_object

    def _add_file_content_to_data_object(self, file_data_object, filename, hash_value, hash_function):
        return self.objecthandler.update_data_object(
            file_data_object['id'],
            {
                'file_content': {
                    'filename': filename,
                    'unnamed_file_content': {
                        'hash_function': hash_function,
                        'hash_value': hash_value
                    }
                }
            }
        )

    def _flag_upload_as_complete(self, file_data_object):
        """ Mark upload location as "complete".
        """
        file_location = file_data_object['file_location']
        file_location['status'] = 'complete'
        file_location = self.objecthandler.update_file_location(
            file_location['id'],
            file_location
        )
        file_data_object['file_location'] = file_location
        return file_data_object

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
        file_data_object = self.objecthandler.get_file_data_object_index(query_string=file_id, max=1, min=1)[0]

        if not destination_url:
            destination_url = os.getcwd()
        default_name = file_data_object['file_content']['filename']
        destination_url = self.get_destination_file_url(destination_url, default_name)
        destination = Destination(destination_url, self.settings)

        self._log('Exporting file %s%s to %s...' % (file_data_object['file_content']['filename'], file_data_object['id'], destination.get_url()))

        # Copy from the first file location
        source_url = file_data_object['file_location']['url']
        Source(source_url, self.settings).copy_to(destination)

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
        source = Source(url, self.settings)
        return source.read(), source.get_url()

    def write_to_file(self, url, content):
        Destination(url, self.settings).write(content)

    def normalize_url(self, url):
        return _urlparse(url).geturl()
