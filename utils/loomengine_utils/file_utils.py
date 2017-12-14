import copy
import errno
import glob
import google.cloud.storage
import os
import random
import re
from requests.exceptions import HTTPError
import shutil
import sys
import tempfile
import time
import urlparse
import warnings
import yaml

from . import execute_with_retries
from . import md5calc
from .exceptions import *
from .connection import Connection

# Google Storage JSON API imports
from oauth2client.client import HttpAccessTokenRefreshError
from oauth2client.client import ApplicationDefaultCredentialsError
import apiclient.discovery


class FileUtilsError(LoomengineUtilsError):
    pass

class Md5ValidationError(FileUtilsError):
    pass


def _urlparse(pattern):
    """Like urlparse except it assumes 'file://' if no scheme is specified
    """
    url = urlparse.urlparse(pattern)
    if not url.scheme:
        url = urlparse.urlparse(
            'file://' + os.path.abspath(os.path.expanduser(pattern)))
    return url


def FileSet(patterns, settings, retry=False):
    """Returns a list of unique Files matching the given patterns.
    """
    assert isinstance(patterns, list), 'patterns must be a list'
    files = []
    urls = set()
    for pattern in patterns:
        url = _urlparse(pattern)

        if url.scheme == 'gs':
            new_file_set = GoogleStorageFilePattern(pattern, settings, retry=retry)
        elif url.scheme == 'file':
            if url.hostname == 'localhost' or url.hostname is None:
                new_file_set = LocalFilePattern(pattern, settings, retry=retry)
            else:
                raise FileUtilsError('Cannot process file pattern %s. '\
                                       'Remote file hosts not supported.' % pattern)
        else:
            raise FileUtilsError('Cannot recognize file scheme in "%s". '\
                                   'Make sure the pattern starts with a '\
                                   'supported protocol like gs:// or file://'
                                   % pattern)
        for file in new_file_set:
            if file.get_url() not in urls:
                urls.add(file.get_url())
                files.append(file)
    return files


class AbstractFilePattern:
    """Creates an iterable set of Files that match the given pattern.
    Pattern may include wildcards.
    """

    def __init__(self, pattern, settings, retry=False):
        raise FileUtilsError('Child class must override this method')

    def __iter__(self):
        raise FileUtilsError('Child class must override this method')

    def _trim_metadata(self, all_matches):
        # For any file <filename>.metadata.yaml, return just <filename>
        return map(lambda path: path[:-len('.metadata.yaml')]
                   if path.endswith('.metadata.yaml')
                   else path,
                   all_matches)


class LocalFilePattern(AbstractFilePattern):
    """A set of Files for files on local storage
    """

    def __init__(self, pattern, settings, retry=False):
        # retry has no effect
        self.files = []
        pattern_without_scheme = re.sub('^file://', '', pattern)
        abs_path_pattern = \
            pattern_without_scheme if pattern_without_scheme.startswith('/') \
            else os.path.join(os.getcwd(),pattern_without_scheme)
        matches = self._get_matching_files(abs_path_pattern)
        self.files = [
            LocalFile('file://' + match, settings, retry=retry)
            for match in matches]

    def __iter__(self):
        return self.files.__iter__()

    def _get_matching_files(self, path):
        matches = glob.glob(path)
        matches = self._remove_directories(matches)
        matches = self._trim_metadata(matches)
        return matches

    def _remove_directories(self, all_matches):
        return filter(lambda path: os.path.isfile(path), all_matches)


def _contains_wildcard(string):
    return '*' in string or '?' in string

class GoogleStorageFilePattern(AbstractFilePattern):
    """A set of Files for files on Google Storage
    """

    def __init__(self, pattern, settings, retry=False):
        self.settings = settings
        if _contains_wildcard(pattern):
            raise FileUtilsError(
                'Wildcard expressions are not supported for GoogleStorage. "%s"'
                % pattern)
        if pattern.endswith('.metadata.yaml'):
            pattern = pattern[:-len('.metadata.yaml')]
        self.files = [GoogleStorageFile(pattern, settings,
                                        retry=retry, must_exist=True)]

    def __iter__(self):
        return self.files.__iter__()


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
            raise FileUtilsError(
                "Cannot process file url %s. Remote file hosts not supported."
                % url)
    else:
        raise FileUtilsError('Unsupported scheme "%s" in file "%s"'
                        % (parsed_url.scheme, url))


class AbstractFile:
    """A File represents a single file that to be copied to or from, 
    or otherwise manipulated.
    """

    def __init__(self, url, settings, retry=False):
        raise FileUtilsError('Child class must override this method')

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

    def get_path(self):
        return self.url.path

    def get_filename(self):
        return os.path.basename(self.get_path())

    def calculate_md5(self):
        raise FileUtilsError('Child class must override this method')
    def get_url(self):
        raise FileUtilsError('Child class must override this method')
    def exists(self):
        raise FileUtilsError('Child class must override this method')
    def is_dir(self):
        raise FileUtilsError('Child class must override this method')
    def read(self, content):
        raise FileUtilsError('Child class must override this method')
    def write(self, content):
        raise FileUtilsError('Child class must override this method')
    def delete(self, pruneto=None):
        raise FileUtilsError('Child class must override this method')

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

    def exists(self):
        return os.path.exists(self.get_path())

    def is_dir(self):
        return os.path.isdir(self.get_path())

    def read(self):
        try:
            with open(self.get_path()) as f:
                return f.read()
        except IOError as e:
            raise FileUtilsError(e.message)

    def write(self, content):
        try:
            os.makedirs(os.path.dirname(self.get_path()))
        except OSError as e:
            # This error just means the dir already exists. Ok.
            if e.errno == errno.EEXIST:
                pass
            else:
                raise FileUtilsError(str(e))
        with open(self.get_path(), 'w') as f:
            f.write(content)

    def delete(self, pruneto=None):
        os.remove(self.get_path())
        path = os.path.dirname(self.get_path())

        if pruneto is None:
            return

        # Delete any empty directories up to pruneto
        while os.path.dirname(path).startswith(pruneto):
            try:
                os.rmdir(path)
                path = os.path.dirname(path)
            except OSError:
                return


class GoogleStorageFile(AbstractFile):
    """For file saved on Google Storage
    """
    type = 'google_storage'
    
    # CHUNK_SIZE must be multiple of 256.
    # 2016-08-30: With default 1024*1024, download is 20x slower than gsutil.
    CHUNK_SIZE = 1024*1024*100 

    def __init__(self, url, settings, retry=False, must_exist=False):
        self.settings = settings
        self.url = _urlparse(url)
        self.retry = retry
        assert self.url.scheme == 'gs'
        self.bucket_id = self.url.hostname
        self.blob_id = self.url.path.lstrip('/')
        if not self.bucket_id or not self.blob_id:
            raise FileUtilsError('Could not parse url "%s". Be sure to use the format "gs://bucket/blob_id".' % url)
        try:
            if self.retry:
                self.client = execute_with_retries(
                    lambda: google.cloud.storage.client.Client(
                        self.settings['GCE_PROJECT']),
                    (Exception,),
                    logger,
                    'Get client')
            else:
                self.client = google.cloud.storage.client.Client(
                    self.settings['GCE_PROJECT'])
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
            raise FileUtilsError(
                'Failed to access bucket "%s". Are you logged in? '\
                'Try "gcloud auth login"' % self.bucket_id)
        if self.blob is None:
            if must_exist and not self.blob_id.endswith('/'):
                raise FileUtilsError('File not found: "%s"' % self.url.geturl())
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
        # Does not work on directories!
        return self.blob.exists()

    def is_dir(self):
        # No dirs in Google Storage, just blobs.
        # Call it a dir if it ends in /
        return self.url.geturl().endswith('/')

    def read(self):
        tempdir = tempfile.mkdtemp()
        dest_file = os.path.join(tempdir, self.get_filename())
        self.copy_to(File(dest_file, self.settings, retry=self.retry))
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

    def delete(self, pruneto=None):
        # pruning is automating in Google Storage
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
        raise FileUtilsError('Could not find method to copy from source '\
                        '"%s" to destination "%s".' % (source, destination))


class AbstractCopier:

    def __init__(self, source, destination, retry=False, expected_md5=None):
        self.source = source
        self.destination = destination
        self.expected_md5=expected_md5
        self.retry = self.source.retry or self.destination.retry
            
    def copy(self, path):
        raise FileUtilsError('Child class must override method')

class LocalCopier(AbstractCopier):

    def copy(self):
        # Retry has no effect in local copier
        try:
            os.makedirs(os.path.dirname(self.destination.get_path()))
        except OSError as e:
            # This error just means the dir already exists. Ok.
            if e.errno == errno.EEXIST:
                pass
            else:
                raise FileUtilsError(str(e))
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
            # This error just means the dir already exists. Ok.
            if e.errno == errno.EEXIST:
                pass
            else:
                raise FileUtilsError(str(e))
        if self.retry:
            execute_with_retries(
                lambda: self.source.blob.download_to_filename(
                    self.destination.get_path()),
                (Exception,),
                logger,
                'File download')
        else:
            self.source.blob.download_to_filename(self.destination.get_path())
