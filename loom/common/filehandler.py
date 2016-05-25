import abc
import copy
import errno
import glob
import logging
import os
import shutil
import sys
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
import apiclient.discovery


def _urlparse(pattern):
    """Like urlparse except it assumes 'file://' if no scheme is specified
    """
    url = urlparse.urlparse(pattern)
    if not url.scheme:
        url = urlparse.urlparse('file://' + pattern)
    return url


def SourceSet(pattern):
    """Factory Method that returns a set of Sources matching the given pattern.
    Each Source represents one source file to be copied.
    """

    url = _urlparse(pattern)

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
        url = _urlparse(pattern)
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


def Source(url):
    """Factory method
    """
    parsed_url = _urlparse(url)

    if parsed_url.scheme == 'gs':
        return GoogleStorageSource(pattern)
    elif parsed_url.scheme == 'file':
        if parsed_url.hostname == 'localhost' or parsed_url.hostname is None:
            return LocalSource(url)
        else:
            raise Exception("Cannot process file pattern %s. Remote file hosts not supported." % url)
    else:
        raise Exception('Cannot recognize file scheme in "%s". '\
                        'Make sure the pattern starts with a supported protocol like gs:// or file://'
                        % url)


class AbstractSource:
    """A Source represents a single file to be copied.
    """

    __metaclass__ = abc.ABCMeta

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

    def __init__(self, url):
        parsed_url = _urlparse(url)
        self.file_path = os.path.abspath(os.path.expanduser(parsed_url.path))

    def get_hash_value(self, hash_function):
        if not hash_function == 'md5':
            raise Exception('Unsupported hash function %s' % hash_function)
        return md5calc.calculate_md5sum(self.file_path)

    def get_url(self):
        return 'file://'+ self.get_path()

    def get_path(self):
        return os.path.abspath(os.path.expanduser(self.file_path))

    def get_filename(self):
        return os.path.basename(self.file_path)


class GoogleStorageSource(AbstractSource):
    """A source file on Google Storage.
    """
    type = 'google_storage'

    def get_hash_value(self, hash_function):
        pass

    def get_url(self):
        pass

    def get_filename(self):
        pass


def Destination(url):
    """Factory method
    """
    parsed_url = _urlparse(url)

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


class AbstractDestination:
    """A Destination represents a path or directory to which a file will be copied
    """

    __metaclass__ = abc.ABCMeta

    def __init__(self, url):
        self.url = _urlparse(url)

    @abc.abstractmethod
    def get_url(self):
        pass

    @abc.abstractmethod
    def exists(self):
        pass


class LocalDestination(AbstractDestination):

    type = 'local'

    def get_path(self):
        return os.path.abspath(os.path.expanduser(self.url.path))

    def get_url(self):
        return 'file://'+ self.get_path()

    def exists(self):
        return os.path.exists(self.get_path())


class GoogleStorageDestination(AbstractDestination):

    type = 'google_storage'


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

    def copy(self):
        # TODO
        raise Exception('TODO')

    def move(self):
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
        
        file_import = self._create_file_import(source, note)

        temp_destination = Destination(file_import['temp_file_storage_location']['url'])
        hash_function = self.settings['HASH_FUNCTION']
        hash_value = source.hash_and_copy_to(temp_destination, hash_function)

        updated_file_import = self._add_file_object_to_file_import(file_import, source, hash_value, hash_function)

        temp_source = Source(temp_destination.get_url())
        final_destination = Destination(updated_file_import['file_storage_location']['url'])
        temp_source.move_to(final_destination)

        self._finalize_file_import(updated_file_import)
            
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
        for file_id in file_ids:
            self.export_file(file_id, destination_url)

    def export_file(self, file_id, destination_url=None):
        # Error raised if there is not exactly one matching file.
        file = self.objecthandler.get_file_data_object_index(file_id, max=1, min=1)[0]

        if not destination_url:
            destination_url = os.path.join(os.getcwd(), file['filename'])
            destination_url = self._rename_to_avoid_overwrite(destination_url)

        destination = Destination(destination_url)
        
        # Copy from the first storage location
        location = self.objecthandler.get_file_storage_locations_by_file(file['_id'])[0]
        Source(location['url']).copy_to(destination)

    def _rename_to_avoid_overwrite(self, destination_url):
        root = destination_url
        destination = Destination(root)
        counter = 0
        while destination.exists():
            counter += 1
            destination_url = '%s(%s)' % (root, counter)
            destination = Destination(destination_url)
        return destination_url
