import logging
import os
from requests.exceptions import HTTPError
import yaml

from loomengine_utils.file_utils import File, FileSet


logger = logging.getLogger(__name__)


class ImportManagerError(Exception):
    pass


class ImportManager(object):

    def __init__(self, connection, storage_settings=None):
        self.connection = connection
        if storage_settings is None:
            storage_settings = connection.get_storage_settings()
	self.storage_settings = storage_settings

    def bulk_import(self, directory, link_files=False,
                    retry=False):
        self._bulk_import_files(
            os.path.join(directory, 'files'),
            link_files=link_files, retry=retry)
        self._bulk_import_templates(
            os.path.join(directory, 'templates'),
            link_files=link_files, retry=retry)
        self._bulk_import_runs(
            os.path.join(directory, 'runs'),
            link_files=link_files, retry=retry)

    def _bulk_import_files(self, directory, link_files=False, retry=False):
        # import all files directory/* and directory/*/*, with metadata if present
        files_to_import = FileSet(
            [os.path.join(directory, '*'), os.path.join(directory, '*/*')],
            self.storage_settings, retry=retry)
        for file_to_import in files_to_import:
            self.import_file(
                file_to_import.get_url(), '', link=link_files, retry=retry)

    def _bulk_import_templates(self, directory, link_files=False, retry=False):
        pass

    def _bulk_import_runs(self, directory, link_files=False, retry=False):
        pass

    def import_from_patterns(self, patterns, comments, link=False,
                            ignore_metadata=False, force_duplicates=False,
                            from_metadata=False, retry=False):
        files = []
        for source in FileSet(patterns, self.storage_settings,retry=retry):
            files.append(self.import_file(
                source.get_url(),
                comments,
                link=link,
                ignore_metadata=ignore_metadata,
                force_duplicates=force_duplicates,
                retry=retry))
        return files

    def _get_metadata(self, metadata_url, retry=False):
        try:
            raw_metadata = File(
                metadata_url,
                self.storage_settings, retry=retry).read()
        except Exception as e:
            raw_metadata = None
            metadata = {}
        if raw_metadata is not None:
            try:
                metadata = yaml.load(raw_metadata)
            except yaml.parser.ParserError:
                raise ImportManagerError(
                    'Metadata is not valid YAML format: "%s"' % metadata_url)
            except yaml.scanner.ScannerError as e:
                raise ImportManagerError(
                    'Metadata is not valid YAML format: "%s"' % metadata_url)
        return metadata

    def import_file(self, source_url, comments, link=False,
                    ignore_metadata=False, force_duplicates=False,
                    retry=False):

        if source_url.endswith('.metadata.yaml'):
            source_url = source_url[:-len('.metadata.yaml')]
        
        source = File(source_url, self.storage_settings, retry=retry)
        metadata_url = source.get_url() + '.metadata.yaml'

        if ignore_metadata:
            metadata = None
        else:
            metadata = self._get_metadata(metadata_url, retry=retry)
            if not source.exists() or source.is_dir():
                # No file found, so we need find it from the metadata
                if not metadata.get('value') or not metadata['value'].get('file_url'):
                    raise ImportManagerError(
                        'Failed to import because file "%s" was not found, '\
                        'and file URL was not found '
                        'in metadata "%s"' % (source_url, metadata_url))
                source_url = metadata['value'].get('file_url')
                source = File(source_url, self.storage_settings, retry=retry)

        self._import_file_and_metadata(source, metadata, comments, link=link,
                                  force_duplicates=force_duplicates, retry=retry)

    def _import_file_and_metadata(self, source, metadata, comments, link=False,
                             force_duplicates=False, retry=False):
        try:
            if link:
                data_object = self._create_file_data_object_from_original_copy(
                    source, comments, force_duplicates=force_duplicates,
                    metadata=metadata)
                return data_object
            else:
                data_object = self._create_file_data_object_for_import(
                    source, comments, force_duplicates=force_duplicates,
                    metadata=metadata)
                return self._execute_file_import(data_object, source, retry=retry)
        except HTTPError as e:
            if e.response.status_code==400:
                errors = e.response.json()
                raise SystemExit(
                    "ERROR! %s" % errors)
            else:
                raise

    def _create_file_data_object_for_import(
            self, source, comments, force_duplicates=True, metadata=None):
        if metadata is None:
            metadata = {}
        metadata_file_resource = metadata.get('value', {})
        filename = metadata_file_resource.get('filename', source.get_filename())
        logger.info('Calculating md5 on file "%s"...' % source.get_url())
        md5 = source.calculate_md5()
        metadata_md5 = metadata_file_resource.get('md5')
        imported_from_url = metadata_file_resource.get(
            'imported_from_url', source.get_url())
        source_type = metadata_file_resource.get('source_type', 'imported')
        if metadata:
            assert not comments, \
                'New comments are not allowed if metadata is used'
            comments = metadata_file_resource.get('import_comments', '')
        
        if metadata_md5 and md5 != metadata_md5:
            raise ImportManagerError(
                'md5 of file "%s" does not match value in its metadata '\
                'file. The file may have been corrupted. If it was changed '\
                'intentionally, you should not use the old metadata.'
                % source.get_url())
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
            'imported_from_url': imported_from_url,
            'source_type': source_type,
            'link': False,
        }
        if comments:
            value['import_comments'] = comments
        file_data_object = {
            'type': 'file',
            'value': value
        }
        if metadata.get('uuid'):
            file_data_object['uuid'] = metadata.get('uuid')
        if metadata.get('datetime_created'):
            file_data_object['datetime_created'] = metadata.get('datetime_created')

        return self.connection.post_data_object(file_data_object)

    def _create_file_data_object_from_original_copy(
            self, source, comments, force_duplicates=True, metadata=None):
        if metadata is None:
            metadata = {}
        metadata_file_resource = metadata.get('value', {})
        filename = metadata_file_resource.get('filename', source.get_filename())
        logger.info('Calculating md5 on file "%s"...' % source.get_url())
        md5 = source.calculate_md5()
        metadata_md5 = metadata_file_resource.get('md5')
        imported_from_url = metadata_file_resource.get(
            'imported_from_url', source.get_url())
        source_type = metadata_file_resource.get('source_type', 'imported')
        if metadata:
            assert not comments, \
                'New comments are not allowed if metadata is used'
            comments = metadata_file_resource.get('import_comments', '')
        if metadata_md5 and md5 != metadata_md5:
            raise ImportManagerError(
                'md5 of file "%s" does not match value in its metadata '\
                'file. The file may have been corrupted. If it was changed '\
                'intentionally, you should not use the old metadata.'
                % source.get_url())
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
            'imported_from_url': imported_from_url,
            'upload_status': 'complete',
            'source_type': 'imported',
            'link': True,
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
        source = File(source_url, self.storage_settings, retry=retry)
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
            source = File(source_url, self.storage_settings, retry=retry)
            md5_list.append(source.calculate_md5())
            filename_list.append(source.get_filename())
        task_attempt_output = self._create_task_attempt_output_file_array(
            task_attempt_output, md5_list, filename_list)
        data_object_array = task_attempt_output['data']['contents']
        imported_data_objects = []
        for (source_url, data_object) in zip(source_url_list, data_object_array):
            source = File(source_url, self.storage_settings, retry=retry)
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
        source = File(source_url, self.storage_settings, retry=retry)
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
                self.storage_settings,
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

