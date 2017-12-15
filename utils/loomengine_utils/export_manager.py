import datetime
import logging
import os
import yaml

from loomengine_utils.file_utils import File

logger = logging.getLogger(__name__)


class ExportManagerError(Exception):
    pass

def _replace_none_with_empty_list(myList):
    if myList is None:
        return []
    return myList

def _get_default_destination_directory():
    dirname = 'loom-bulk-export-%s' % \
              datetime.datetime.now().strftime('%Y-%m-%dT%H.%M.%S.%f')
    return os.path.join(os.getcwd(), dirname)

class ExportManager(object):

    def __init__(self, connection, storage_settings=None):
        self.connection = connection
        if storage_settings is None:
            storage_settings = connection.get_storage_settings()
        self.storage_settings = storage_settings      

    def bulk_export(self,
                    files=None,
                    templates=None,
                    runs=None,
                    destination_directory=None,
                    retry=False,
                    export_file_metadata=True,
                    template_editable=False,
                    file_links=False):
        files = _replace_none_with_empty_list(files)
        templates = _replace_none_with_empty_list(templates)
        runs = _replace_none_with_empty_list(runs)
        if destination_directory is None:
            destination_directory=_get_default_destination_directory()

        self._bulk_export_files(
            files,
            destination_directory,
            retry=retry,
            export_file_metadata=export_file_metadata,
            file_links=file_links)

    def _bulk_export_files(self, files, bulk_export_dir, **kwargs):
        for file in files:
            self._bulk_export_file(file, bulk_export_dir, **kwargs)

    def _bulk_export_file(self, file, bulk_export_dir, **kwargs):
        dest_dir = os.path.join(
            bulk_export_dir,
            'files',
            file.get('uuid'))
        self.export_file('@%s' % file.get('uuid'),
                         destination_directory=dest_dir,
                         retry=retry,
                         export_metadata=export_file_metadata,
                         export_raw_file=not file_links)

#    def export_files(self, file_ids, destination_directory=None, retry=False,
#                     export_metadata=False, export_raw_file=True):
#        for file_id in file_ids:
#            self.export_file(
#                file_id, destination_directory=destination_directory, retry=retry,
#                export_metadata=export_metadata, export_raw_file=export_raw_file)

    def export_file(self, file_id, destination_directory=None,
                    destination_filename=None, retry=False,
                    export_metadata=False, export_raw_file=True):
        """Export a file from Loom to some file storage location.
        Default destination_directory is cwd. Default destination_filename is the 
        filename from the file data object associated with the given file_id.
        """
        # Error raised if there is not exactly one matching file.
        data_object = self.connection.get_data_object_index(
            query_string=file_id, type='file', max=1, min=1)[0]

        if not destination_directory:
            destination_directory = os.getcwd()

        # We get filename from the dataobject
        if not destination_filename:
            destination_filename = data_object['value']['filename']

        destination_file_url = os.path.join(destination_directory,
                                            destination_filename)

        logger.info('Exporting file %s@%s ...' % (
            data_object['value']['filename'],
            data_object['uuid']))

        if export_raw_file:
            destination = File(
                destination_file_url, self.storage_settings, retry=retry)
            if destination.exists():
                raise ExportManagerError(
                    'File already exists at %s' % destination_file_url)
            logger.info('...copying file to %s' % (
                destination.get_url()))

            # Copy from the first file location
            file_resource = data_object.get('value')
            md5 = file_resource.get('md5')
            source_url = data_object['value']['file_url']
            File(source_url, self.storage_settings, retry=retry).copy_to(
                destination, expected_md5=md5)
        else:
            logger.info('...skipping raw file')

        if export_metadata:
            destination_metadata_url = os.path.join(
                destination_file_url + '.metadata.yaml')
            logger.info('...writing metadata to %s' % destination_metadata_url)
            metadata = yaml.safe_dump(data_object, default_flow_style=False)
            metadata_file = File(destination_metadata_url,
                                 self.storage_settings, retry=retry)
            metadata_file.write(metadata)
        else:
            logger.info('...skipping metadata')

        logger.info('...finished file export')
