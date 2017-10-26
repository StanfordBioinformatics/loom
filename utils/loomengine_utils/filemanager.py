import copy
import errno
import glob
import google.cloud.storage
import logging
import os
import random
from requests.exceptions import HTTPError
import shutil
import sys
import tempfile
import time
import urlparse
import warnings

from . import execute_with_retries
from . import md5calc
from .exceptions import *
from .connection import Connection

# Google Storage JSON API imports
from oauth2client.client import HttpAccessTokenRefreshError
from oauth2client.client import ApplicationDefaultCredentialsError
import apiclient.discovery


class Md5ValidationError(Exception):
    pass


logger = logging.getLogger(__name__)

def _urlparse(pattern):
    """Like urlparse except it assumes 'file://' if no scheme is specified
    """
    url = urlparse.urlparse(pattern)
    if not url.scheme:
        url = urlparse.urlparse(
            'file://' + os.path.abspath(os.path.expanduser(pattern)))
    return url


def FileSet(pattern, settings, retry=False):
    """Factory Method that returns a set of Files matching the given pattern.
    """

    url = _urlparse(pattern)

    if url.scheme == 'gs':
        return GoogleStorageFileSet(pattern, settings, retry=retry)
    elif url.scheme == 'file':
        if url.hostname == 'localhost' or url.hostname is None:
            return LocalFileSet(pattern, settings, retry=retry)
        else:
            raise Exception('Cannot process file pattern %s. '\
                            'Remote file hosts not supported.' % pattern)
    else:
        raise Exception('Cannot recognize file scheme in "%s". '\
                        'Make sure the pattern starts with a '\
                        'supported protocol like gs:// or file://'
                        % pattern)


class AbstractFileSet:
    """Creates an iterable set of Files that match the given pattern.
    Pattern may include wildcards.
    """

    def __init__(self, pattern, settings, retry=False):
        raise Exception('Child class must override this method')

    def __iter__(self):
        raise Exception('Child class must override this method')


class LocalFileSet(AbstractFileSet):
    """A set of Files for files on local storage
    """

    def __init__(self, pattern, settings, retry=False):
        # retry has no effect
        url = _urlparse(pattern)
        matches = self._get_matching_files(url.path)
        self.files = [LocalFile('file://' + path, settings, retry=retry)
                        for path in matches]

    def __iter__(self):
        return self.files.__iter__()

    def _get_matching_files(self, path):
        all_matches = glob.glob(path)
        return self._remove_directories(all_matches)

    def _remove_directories(self, all_matches):
        return filter(lambda path: os.path.isfile(path), all_matches)


class GoogleStorageFileSet(AbstractFileSet):
    """A set of Files for files on Google Storage
    """

    def __init__(self, pattern, settings, retry=False):
        self.settings = settings
        self.files = [GoogleStorageFile(pattern, settings, retry=retry)]

    def __iter__(self):
        return self.files.__iter__()

    # TODO support wildcards with multiple matches


def File(url, settings, retry=False):
    """Factory method
    """
    parsed_url = _urlparse(url)

    if parsed_url.scheme == 'gs':
        return GoogleStorageFile(url, settings, retry=retry)
    elif parsed_url.scheme == 'file':
        if parsed_url.hostname == 'localhost' or parsed_url.hostname is None:
            return LocalFile(url, settings, retry=retry)
        else:
            raise Exception(
                "Cannot process file url %s. Remote file hosts not supported."
                % url)
    else:
        raise Exception('Unsupported scheme "%s" in file "%s"'
                        % (parsed_url.scheme, url))


class AbstractFile:
    """A File represents a single file that to be copied to or from, 
    or otherwise manipulated.
    """

    def __init__(self, url, settings, retry=False):
        raise Exception('Child class must override this method')

    def copy_to(self, destination, expected_md5=None):
        if self.retry or destination.retry:
            tries_remaining = 2
        else:
            tries_remaining = 1

        while True:
            try:
                copier = Copier(self, destination)
                copier.copy()
                destination.verify_md5(expected_md5)
                break
            except Md5ValidationError as e:
                logger.info('Copied file did not have the expected md5. '\
                            '%s retries remaining' % tries_remaining)
                if tries_remaining == 0:
                    raise
                tries_remaining -= 1
                destination.delete()

    def verify_md5(self, expected_md5):
        if expected_md5:
            md5 = self.calculate_md5()
            if md5 != expected_md5:
                raise Md5ValidationError(
                    'Expected md5 "%s" for file "%s", but found md5 "%s"'
                    % (expected_md5, self.get_url(), md5))

    def calculate_md5(self):
        raise Exception('Child class must override this method')
    def get_url(self):
        raise Exception('Child class must override this method')
    def get_path(self):
        raise Exception('Child class must override this method')
    def get_filename(self):
        raise Exception('Child class must override this method')
    def exists(self):
        raise Exception('Child class must override this method')
    def is_dir(self):
        raise Exception('Child class must override this method')
    def read(self, content):
        raise Exception('Child class must override this method')
    def write(self, content):
        raise Exception('Child class must override this method')
    def delete(self):
        raise Exception('Child class must override this method')

class LocalFile(AbstractFile):
    """For files saved on local storage.
    """

    type = 'local'

    def __init__(self, url, settings, retry=False):
        self.url = _urlparse(url)
        self.retry = retry

    def calculate_md5(self):
        return md5calc.calculate_md5sum(self.get_path())

    def get_url(self):
        return self.url.geturl()

    def get_path(self):
        return self.url.path

    def get_filename(self):
        return os.path.basename(self.get_path())

    def exists(self):
        return os.path.exists(self.get_path())

    def is_dir(self):
        return os.path.isdir(self.get_path())

    def read(self):
        with open(self.get_path()) as f:
            return f.read()

    def write(self, content):
        with open(self.get_path(), 'w') as f:
            f.write(content)

    def delete(self):
        os.remove(self.get_path())


class GoogleStorageFile(AbstractFile):
    """For file saved on Google Storage
    """
    type = 'google_storage'
    
    # CHUNK_SIZE must be multiple of 256.
    # 2016-08-30: With default 1024*1024, download is 20x slower than gsutil.
    CHUNK_SIZE = 1024*1024*100 

    def __init__(self, url, settings, retry=False):
        self.settings = settings
        self.url = _urlparse(url)
        self.retry = retry
        assert self.url.scheme == 'gs'
        self.bucket_id = self.url.hostname
        self.blob_id = self.url.path.lstrip('/')
        if not self.bucket_id or not self.blob_id:
            raise Exception('Could not parse url "%s". Be sure to use the format "gs://bucket/blob_id".' % url)
        try:
            self.client = execute_with_retries(
                lambda: google.cloud.storage.client.Client(
                    self.settings['GCE_PROJECT']),
                (Exception,),
                logger,
                'Get client')
        except ApplicationDefaultCredentialsError as e:
            raise SystemExit(
                'ERROR! '\
                'Google Cloud application default credentials are not set. '\
                'Please run "gcloud auth application-default login"')

        try:
            if self.retry:
                self.bucket = execute_with_retries(
                    lambda: self.client.get_bucket(self.bucket_id),
                    (Exception,),
                    logger,
                    'Get bucket')
                self.blob = execute_with_retries(
                    lambda: self.bucket.get_blob(self.blob_id),
                    (Exception,),
                    logger,
                    'Get blob')
            else:
                self.bucket = self.client.get_bucket(self.bucket_id)
                self.blob = self.bucket.get_blob(self.blob_id)
        except HttpAccessTokenRefreshError:
            raise Exception(
                'Failed to access bucket "%s". Are you logged in? '\
                'Try "gcloud auth login"' % self.bucket_id)
        if self.blob is None:
            self.blob = google.cloud.storage.blob.Blob(
                self.blob_id, self.bucket, chunk_size=self.CHUNK_SIZE)
        if self.blob.size > self.CHUNK_SIZE:
            self.blob.chunk_size = self.CHUNK_SIZE

    def calculate_md5(self):
        md5_base64 = self.blob.md5_hash
        md5_hex = md5_base64.decode('base64').encode('hex').strip()
        return md5_hex

    def get_url(self):
        return self.url.geturl()

    def get_filename(self):
        return os.path.basename(self.blob_id)

    def exists(self):
        return self.blob.exists()

    def is_dir(self):
        # No dirs in Google Storage, just blobs.
        # Call it a dir if it ends in /
        self.url.geturl().endswith('/')

    def read(self):
        tempdir = tempfile.mkdtemp()
        dest_file = os.path.join(tempdir, self.get_filename())
        self.copy_to(File(dest_file, self.settings, retry=retry))
        with open(dest_file) as f:
            text = f.read()
        os.remove(dest_file)
        os.rmdir(tempdir)
        return text

    def write(self, content):
        with tempfile.NamedTemporaryFile('w') as f:
            f.write(content)
            f.flush()
            File(f.name, self.settings, retry=self.retry).copy_to(self)

    def delete(self):
        self.blob.delete()


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
        raise Exception('Could not find method to copy from source '\
                        '"%s" to destination "%s".' % (source, destination))


class AbstractCopier:

    def __init__(self, source, destination, retry=False, expected_md5=None):
        self.source = source
        self.destination = destination
        self.expected_md5=expected_md5
        self.retry = self.source.retry or self.destination.retry
            
    def copy(self, path):
        raise Exception('Child class must override method')

class LocalCopier(AbstractCopier):

    def copy(self):
        # Retry has no effect in local copier
        try:
            os.makedirs(os.path.dirname(self.destination.get_path()))
        except OSError as e:
            if e.errno == errno.EEXIST:
                pass
            else:
                raise
        shutil.copy(self.source.get_path(), self.destination.get_path())


class GoogleStorageCopier(AbstractCopier):

    def copy(self):
        rewrite_token = None
        while True:
            if self.retry:
                rewrite_token, rewritten, size = execute_with_retries(
                    lambda: self.destination.blob.rewrite(
                        self.source.blob, token=rewrite_token),
                    (Exception,),
                    logger,
                    'File copy')
            else:
                rewrite_token, rewritten, size = self.destination.blob.rewrite(
                    self.source.blob, token=rewrite_token)
            logger.info("   copied %s of %s bytes ..." % (rewritten, size))
            if not rewrite_token:
                logger.info("   copy completed ...")
                break


class Local2GoogleStorageCopier(AbstractCopier):

    def copy(self):
        if self.retry:
            execute_with_retries(
                lambda: self.destination.blob.upload_from_filename(
                    self.source.get_path()),
                (Exception,),
                logger,
                'File upload')
        else:
            self.destination.blob.upload_from_filename(self.source.get_path())


class GoogleStorage2LocalCopier(AbstractCopier):

    def copy(self):
        try:
            os.makedirs(os.path.dirname(self.destination.get_path()))
        except OSError as e:
            if e.errno == errno.EEXIST:
                pass
            else:
                raise Exception(
                    'Failed to create local directory "%s": "%s"' %
                    (os.path.dirname(self.destination.get_path()),
                     e))
        if self.retry:
            execute_with_retries(
                lambda: self.source.blob.download_to_filename(
                    self.destination.get_path()),
                (Exception,),
                logger,
                'File download')
        else:
            self.source.blob.download_to_filename(self.destination.get_path())


class FileManager:
    """Manages file import/export
    """

    def __init__(self, master_url, token=None):
        self.connection = Connection(master_url, token=token)
        self.settings = self.connection.get_filemanager_settings()

    def import_from_patterns(self, patterns, comments, original_copy=False,
                             force_duplicates=False, retry=False):

        files = []
        for pattern in patterns:
            files.extend(self.import_from_pattern(
                pattern, comments, original_copy=original_copy,
                force_duplicates=force_duplicates, retry=retry))
        return files

    def import_from_pattern(self, pattern, comments, original_copy=False,
                            force_duplicates=False, retry=False):
        files = []
        for source in FileSet(pattern, self.settings, retry=retry):
            files.append(self.import_file(
                source.get_url(),
                comments,
                original_copy=original_copy,
                force_duplicates=force_duplicates,
                retry=retry,
            ))
        return files

    def import_file(self, source_url, comments, original_copy=False,
                    force_duplicates=False, retry=False):
        source = File(source_url, self.settings, retry=retry)
        try:
            if original_copy:
                data_object = self._create_file_data_object_from_original_copy(
                    source, comments, force_duplicates=force_duplicates)
                return data_object
            else:
                data_object = self._create_file_data_object_for_import(
                    source, comments, force_duplicates=force_duplicates)
                return self._execute_file_import(data_object, source, retry=retry)
        except HTTPError as e:
            if e.response.status_code==400:
                errors = e.response.json()
                raise SystemExit(
                    "ERROR! %s" % errors)
            else:
                raise

    def _create_file_data_object_for_import(self, source, comments,
                                            force_duplicates=True):
        filename = source.get_filename()
        logger.info('Calculating md5 on file "%s"...' % source.get_url())
        md5 = source.calculate_md5()

        if not force_duplicates:
            files = self._get_file_duplicates(filename, md5)
            if len(files) > 0:
                warnings.warn(
                    'WARNING! The name and md5 hash "%s$%s" is already in use by one '
                    'or more files. '\
                    'Use "--force-duplicates" to create another copy, but if you '\
                    'do you will have to use @uuid to reference these files.'
                    % (filename, md5))
                return files[-1]

        value = {
            'filename': filename,
            'md5': md5,
            'imported_from_url': source.get_url(),
            'source_type': 'imported',
        }
        if comments:
            value['import_comments'] = comments

        return self.connection.post_data_object({
            'type': 'file',
            'value': value
        })

    def _create_file_data_object_from_original_copy(self, source, comments,
                                                    force_duplicates=True):
        filename = source.get_filename()
        logger.info('Calculating md5 on file "%s"...' % source.get_url())
        md5 = source.calculate_md5()

        if not force_duplicates:
            files = self._get_file_duplicates(filename, md5)
            if len(files) > 0:
                warnings.warn(
                    'WARNING! The name and md5 hash "%s$%s" is already in use by one '
                    'or more files. '\
                    'Use "--force-duplicates" to create another copy, but if you '\
                    'do you will have to use @uuid to reference these files.'
                    % (filename, md5))
                return files[-1]

        value = {
            'filename': filename,
            'md5': md5,
            'file_url': source.get_url(),
            'imported_from_url': source.get_url(),
            'upload_status': 'complete',
            'source_type': 'imported',
        }
        if comments:
            value['import_comments'] = comments

        file_data_object = self.connection.post_data_object({
            'type': 'file',
            'value': value
        })
        logger.info('   registered file %s@%s' % (
            file_data_object['value']['filename'],
            file_data_object['uuid']))
        return file_data_object

    def _get_file_duplicates(self, filename, md5):
        files = self.connection.get_data_object_index(
            query_string='%s$%s' % (filename, md5), type='file')
        return files

    def import_result_file(self, task_attempt_output, source_url, retry=False):
        logger.info('Calculating md5 on file "%s"...' % source_url)
        source = File(source_url, self.settings, retry=retry)
        md5 = source.calculate_md5()
        task_attempt_output = self._create_task_attempt_output_file(
            task_attempt_output, md5, source.get_filename())
        data_object = task_attempt_output['data']['contents']
        return self._execute_file_import(data_object, source, retry=retry)

    def _create_task_attempt_output_file(
            self, task_attempt_output, md5, filename):
        return self.connection.update_task_attempt_output(
            task_attempt_output['uuid'],
            {
                'data': {
                    'type': 'file',
                    'contents': {
                        'type': 'file',
                        'value': {
                            'filename': filename,
                            'source_type': 'result',
                            'md5': md5,
                        }}}})

    def import_result_file_list(self, task_attempt_output, source_url_list,
                                retry=False):
        md5_list = []
        filename_list = []
        for source_url in source_url_list:
            logger.info('Calculating md5 on file "%s"...' % source_url)
            source = File(source_url, self.settings, retry=retry)
            md5_list.append(source.calculate_md5())
            filename_list.append(source.get_filename())
        task_attempt_output = self._create_task_attempt_output_file_array(
            task_attempt_output, md5_list, filename_list)
        data_object_array = task_attempt_output['data']['contents']
        imported_data_objects = []
        for (source_url, data_object) in zip(source_url_list, data_object_array):
            source = File(source_url, self.settings, retry=retry)
            imported_data_objects.append(
                self._execute_file_import(data_object, source, retry=retry))
        return imported_data_objects

    def _create_task_attempt_output_file_array(
            self, task_attempt_output, md5_array, filename_array):
        contents = []
        for md5, filename in zip(md5_array, filename_array):
            contents.append({
                'type': 'file',
                'value': {
                    'filename': filename,
                    'source_type': 'result',
                    'md5': md5,
                }})
        return self.connection.update_task_attempt_output(
            task_attempt_output['uuid'],
            {
                'data': {
                    'type': 'file',
                    'contents': contents
                    }})
            
    def import_log_file(self, task_attempt, source_url, retry=False):
        log_name = os.path.basename(source_url)
        log_file = self.connection.post_task_attempt_log_file(
            task_attempt['uuid'], {'log_name': log_name})

        logger.info('Calculating md5 on file "%s"...' % source_url)
        source = File(source_url, self.settings, retry=retry)
        md5 = source.calculate_md5()

        data_object = self.\
                      connection.post_task_attempt_log_file_data_object(
                          log_file['uuid'],
                          {
                              'type': 'file',
                              'value': {
                                  'filename': log_name,
                                  'source_type': 'log',
                                  'md5': md5,
                }})
        
        return self._execute_file_import(data_object, source, retry=retry)

    def _execute_file_import(self, file_data_object, source, retry=False):
        logger.info('Importing file from %s...' % source.get_url())
        if file_data_object['value']['upload_status'] == 'complete':
            logger.info(
                '   skipping upload because server already has the file %s@%s.' % (
                    file_data_object['value']['filename'], file_data_object['uuid']))
            return file_data_object
        try:
            destination = File(
                file_data_object['value']['file_url'],
                self.settings,
                retry=retry)
            logger.info(
                '   copying to destination %s ...' % destination.get_url())
            source.copy_to(destination)
        except ApplicationDefaultCredentialsError as e:
            self._set_upload_status(file_data_object, 'failed')
            raise SystemExit(
                'ERROR! '\
                'Google Cloud application default credentials are not set. '\
                'Please run "gcloud auth application-default login"')
        except Exception as e:
            self._set_upload_status(file_data_object, 'failed')
            raise

        # Signal that the upload completed successfully
        file_data_object = self._set_upload_status(
            file_data_object, 'complete')
        logger.info('   imported file %s@%s' % (
            file_data_object['value']['filename'],
            file_data_object['uuid']))
        return file_data_object

    def _set_upload_status(self, file_data_object, upload_status):
        """ Set file_data_object.file_resource.upload_status
        """
        file_data_object['value']['upload_status'] = upload_status
        return self.connection.update_data_object(
            file_data_object['uuid'],
            file_data_object)

    def export_files(self, file_ids, destination_url=None, retry=False):
        if destination_url is not None and len(file_ids) > 1:
            # destination must be a directory
            if not File(destination_url, self.settings, retry=retry).is_dir():
                raise Exception(
                    'Destination must be a directory if multiple files '\
                    'are exported. "%s" is not a directory.'
                    % destination_url)
        for file_id in file_ids:
            self.export_file(file_id, destination_url=destination_url, retry=retry)

    def export_file(self, file_id, destination_url=None,
                    destination_filename=None, retry=False):
        """Export a file from Loom to some file storage location.
        Default destination_url is cwd. Default destination_filename is the 
        filename from the file data object associated with the given file_id.
        destination_url may be for a file or a directory. If destination_filename
        is given, destination_url must be a directory.
        """
        # Error raised if there is not exactly one matching file.
        data_object = self.connection.get_data_object_index(
            query_string=file_id, type='file', max=1, min=1)[0]

        if not destination_url:
            destination_url = os.getcwd()
        
        if File(destination_url, self.settings, retry=retry).is_dir():
            # Filename not given with destination_url. We get it from inputs
            # or from the object specified by file_id
            if not destination_filename:
                destination_filename = data_object['value']['filename']
            destination_file_url = os.path.join(destination_url,
                                                destination_filename)
        else:
            if destination_filename:
                raise Exception('Conflicting args: cannot give both destination_url '
                                ' and destination_filename unless destination_url '
                                ' is a directory')
            # Filename is included with destination_url
            destination_file_url = destination_url   

        destination = File(destination_file_url, self.settings, retry=retry)
        if destination.exists():
            raise FileAlreadyExistsError('File already exists at %s' % destination_url)

        logger.info('Exporting file %s@%s to %s...' % (
            data_object['value']['filename'],
            data_object['uuid'],
            destination.get_url()))

        # Copy from the first file location
        file_resource = data_object.get('value')
        md5 = file_resource.get('md5')
        source_url = data_object['value']['file_url']
        File(source_url, self.settings, retry=retry).copy_to(
            destination, expected_md5=md5)

        logger.info('...finished exporting file')

    def read_file(self, url, retry=False):
        source = File(url, self.settings, retry=retry)
        return source.read(), source.get_url()

    def write_to_file(self, url, content, retry=False):
        destination = File(url, self.settings, retry=retry)
        if destination.exists():
            raise FileAlreadyExistsError('File already exists at %s' % url)
        destination.write(content)

    def normalize_url(self, url):
        return _urlparse(url).geturl()

    def calculate_md5(self, url, retry=False):
        return File(url, self.settings, retry=retry).calculate_md5()

    def get_template_duplicates(self, template):
        md5 = template.get('md5')
        name = template.get('name')
        templates = self.connection.get_template_index(
            query_string='%s$%s' % (name, md5))
        return templates
    
    def get_destination_file_url(self, requested_destination, default_name,
                                 retry=False):
        """destination may be a file, a directory, or None
        This function accepts the specified file desitnation, 
        or creates a sensible default that will not overwrite an existing file.
        """
        if requested_destination is None:
            destination = os.path.join(os.getcwd(), default_name)
        elif File(requested_destination, self.settings, retry=retry).is_dir():
            destination = os.path.join(requested_destination, default_name)
        else:
            # Don't modify a file destination specified by the user
            destination = requested_destination
        return self.normalize_url(destination)
