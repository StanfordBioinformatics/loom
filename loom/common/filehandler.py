import abc
import errno
import glob
import logging
import os
import shutil
import sys
from urlparse import urlparse
import gcloud.storage
import requests

from loom.common import md5calc
from loom.common.exceptions import *
from loom.common.objecthandler import ObjectHandler
from loom.common.logger import StreamToLogger

# Google Storage JSON API imports
from apiclient.http import MediaIoBaseDownload
from oauth2client.client import GoogleCredentials
import apiclient.discovery


def SourceSet(pattern):
    """Factory Method that returns a set of Sources matching the given pattern.
    Each Source represents one source file to be copied.
    """

    url = urlparse(pattern)

    if not url.scheme:
        url = urlparse('file://' + pattern)

    if url.scheme == 'gs':
        return GoogleStorageSourceSet(pattern)
    elif url.scheme == 'file':
        if url.hostname == 'localhost' or url.hostname is None:
            return LocalSourceSet(pattern)
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
    def __init__(self, pattern):
        pass
    
    @abc.abstractmethod
    def __iter__(self):
        pass


class LocalSourceSet(AbstractSourceSet):
    """A set of source files on local storage
    """
    
    def __init__(self, pattern):
        url = urlparse(pattern)
        matches = self._get_matching_files(url.path)
        self.sources = [LocalSource('file://' + path) for path in matches]

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

    def __init__(self, pattern):
        self.files = self.get_matching_files(pattern)
        self.sources = [GoogleStorageSource(file) for file in self.files]

    def __iter__(self):
        return self.sources.__iter__()

    def _get_matching_files(self, pattern):
        # TODO
        raise exception('TODO')


class AbstractSource:
    """A Source represents a single file to be copied.
    """

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def copy_to(self, destination):
        pass

    @abc.abstractmethod
    def get_hash_function(self):
        pass

    @abc.abstractmethod
    def get_hash_value(self):
        pass

    @abc.abstractmethod
    def get_url(self):
        pass

    @abc.abstractmethod
    def get_filename(self):
        pass

    @abc.abstractmethod
    def transfer(self, destination):
        pass


class LocalSource:
    """A source file on local storage.
    """

    type = 'local'

    def __init__(self, url):
        parsed_url = urlparse(url)
        self.file_path = os.path.abspath(os.path.expanduser(parsed_url.path))

    def copy_to(self, destination):
        copier = Copier(self, destination)
        copier.copy()
        
    def get_hash_function(self):
        return 'md5'

    def get_hash_value(self):
        return md5calc.calculate_md5sum(self.file_path)

    def get_url(self):
        return 'file://'+ self.get_path()
    
    def get_path(self):
        return os.path.abspath(os.path.expanduser(self.file_path))

    def get_filename(self):
        return os.path.basename(self.file_path)


class GoogleStorageSource:
    """A source file on Google Storage.
    """
    type = 'google_storage'

    # TODO
    pass

def Destination(url):
    """Factory method
    """
    parsed_url = urlparse(url)
    if parsed_url.scheme == 'gs':
        return GoogleStorageDestination(pattern)
    elif parsed_url.scheme == 'file':
        if parsed_url.hostname == 'localhost' or parsed_url.hostname is None:
            return LocalDestination(url)
        else:
            raise Exception("Cannot process file pattern %s. Remote file hosts not supported." % url)
    else:
        raise Exception('Cannot recognize file scheme in "%s". '\
                        'Make sure the pattern starts with a supported protocol like gs:// or file://'
                        % url)

class LocalDestination:

    type = 'local'

    def __init__(self, url):
        parsed_url = urlparse(url)
        self.file_path = os.path.abspath(os.path.expanduser(parsed_url.path))

    def get_path(self):
        return self.file_path

class GoogleStorageDestination:

    type = 'google_storage'

    def __init__(self, url):
        pass


def Copier(source, destination):
    """Factory method to select the right copier for a given source and destination.
    """

    if source.type == 'local' and destination.type == 'local':
        return LocalCopier(source, destination)
    elif source.type == 'local' and destination.type == 'googlestorage':
        return GoogleStorageCopier(source, destination)
    elif source.type == 'googlestorage' and destination.type == 'local':
        return GoogleStorageCopier(source, destination)
    elif source.type == 'googlestorage' and destination.type == 'googlestorage':
        return GoogleStorageCopier(source, destination)
    else:
        raise Exception('Unable to copy from source "%s" to destination "%s".'
                        % (source, destination))


class AbstractCopier:
    __metaclass__ = abc.ABCMeta

    def __init__(self, source, destination):
        self.source = source
        self.destination = destination
            
    @abc.abstractmethod
    def copy(self):
        pass


class LocalCopier(AbstractCopier):
    
    """If destination differs from source, copy file.
    """

    def copy(self):
        if self.source.get_path() != self.destination.get_path():
            try:
                os.makedirs(os.path.dirname(self.destination.get_path()))
            except OSError as e:
                if e.errno == errno.EEXIST:
                    pass
                else:
                    raise e
            shutil.copyfile(self.source.file_path, self.destination.file_path)


class GoogleStorageCopier(AbstractCopier):

    def copy(self):
        # TODO
        raise Exception('TODO')


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
        for source in SourceSet(pattern):
            self.import_file(source, note)

    def import_file(self, source, note):
        
        file_import = self.create_file_import(source, note)
        destination_location = file_import['file_storage_location']

        if destination_location['status'] == 'complete':
            # No need to upload, the server already has a copy.
            return
        elif destination_location['status'] == 'incomplete':
            source.copy_to(Destination(destination_location['url']))
            # verify upload
            # mark complete
        else:
            raise Exception('Unknown FileStorageLocation status "%s"' % destination.status)

    def create_file_import(self, source, note):
        return self.objecthandler.post_file_import({
            'note': note,
            'source_url': source.get_url(),
            'file_data_object': {
                'filename': source.get_filename(),
                'file_contents': {
                    'hash_function': source.get_hash_function(),
                    'hash_value': source.get_hash_value()
                }
            }
        })
