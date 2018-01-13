import logging
import os
from requests.exceptions import HTTPError
import warnings
import yaml

from loomengine_utils.file_utils import File, FileSet, parse_as_yaml
from oauth2client.client import ApplicationDefaultCredentialsError

logger = logging.getLogger(__name__)

class ImportManagerError(Exception):
    pass

class FileDuplicateError(ImportManagerError):
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
        imported_files = []
        for file_to_import in files_to_import:
            imported_files.append(
                self.import_file(
                    file_to_import.get_url(), '', link=link_files, retry=retry)
            )
        return imported_files

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

    def _get_file_metadata(self, metadata_url, retry=False, ignore_metadata=False):
        if ignore_metadata:
            return None

        try:
            raw_metadata = File(
                metadata_url,
                self.storage_settings, retry=retry).read()
        except:
            return None

        if not raw_metadata:
            return None

        try:
            return yaml.load(raw_metadata)
        except yaml.parser.ParserError:
            raise ImportManagerError(
                'Metadata is not valid YAML format: "%s"' % metadata_url)
        except yaml.scanner.ScannerError as e:
            raise ImportManagerError(
                'Metadata is not valid YAML format: "%s"' % metadata_url)

    def import_file(self, requested_source_url, comments, link=False,
                    ignore_metadata=False, force_duplicates=False,
                    retry=False):
        # A file "mydata.txt" may have a corresponding metadata file
        # "mydata.txt.metadata.yaml". We use the naming convention to determine
        # whether requested_source_url points to the raw file or the metadata,
        # and get the names for the file-metadata pair.
        source_file_url, metadata_url = self._get_file_and_metadata_urls(
            requested_source_url)

        # Attempt to read metadata from the metadata file, if it exists.
        metadata = self._get_file_metadata(
            metadata_url, retry=retry, ignore_metadata=ignore_metadata)
        source_file = self._get_source_file(source_file_url, metadata, retry=retry)

        self._import_file_and_metadata(source_file, metadata, comments, link=link,
                                  force_duplicates=force_duplicates, retry=retry)

    def _get_file_and_metadata_urls(self, requested_source_url):
        if requested_source_url.endswith('.metadata.yaml'):
            source_file_url = requested_source_url[:-len('.metadata.yaml')]
            metadata_url = requested_source_url
        else:
            source_file_url = requested_source_url
            metadata_url = source_file_url + '.metadata.yaml'
        return source_file_url, metadata_url

    def _get_source_file(self, source_url, metadata, retry=False):
        source = File(source_url, self.storage_settings, retry=retry)
        if not source.exists() or source.is_dir():
            source = self._get_source_file_from_metadata(
                source_url, metadata, retry=retry)
        return source
        
    def _get_source_file_from_metadata(
            self, original_source_url, metadata, retry=False):
        try:
            source_url = metadata['value']['file_url']
        except KeyError:
            raise ImportManagerError(
                'Could not find file "%s", and could not find alternative '\
                'file_url in the metadata file.' % original_source_url)
        return File(source_url, self.storage_settings, retry=retry)

    def _import_file_and_metadata(self, source, metadata, comments, link=False,
                             force_duplicates=False, retry=False):
        try:
            data_object = self._render_file_data_object_dict(
                source, comments, metadata=metadata, link=link)
            try:
                data_object = self._check_for_duplicates(
                    data_object, force_duplicates=force_duplicates)
            except FileDuplicateError:
                return
            data_object = self.connection.post_data_object(data_object)
            data_object = self._execute_file_import(
                data_object, source, retry=retry)
            return data_object
        except HTTPError as e:
            if e.response.status_code==400:
                errors = e.response.json()
                raise SystemExit(
                    "ERROR! %s" % errors)
            else:
                raise

    def _check_for_duplicates(self, data_object, force_duplicates=False):
        if force_duplicates:
            return data_object
        else:
            filename = data_object['value']['filename']
            md5= data_object['value']['md5']

            files = self._get_file_duplicates(filename, md5)
            if len(files) > 0:
                logger.warn(
                    'WARNING! The name and md5 hash "%s$%s" is already in use by one '
                    'or more files. '\
                    'Use "--force-duplicates" to create another copy, but if you '\
                    'do you will have to use @uuid to reference these files.'
                    % (filename, md5))
                raise FileDuplicateError
            else:
                return data_object

    def _get_file_duplicates(self, filename, md5):
        files = self.connection.get_data_object_index(
            query_string='%s$%s' % (filename, md5), type='file')
        return files

    def _render_file_data_object_dict(
            self, source, comments, metadata=None, link=False):
        if metadata is None:
            metadata = {}
        metadata_file_resource = metadata.get('value', {})
        if metadata:
            assert not comments, \
                'New comments are not allowed if metadata is used'
            comments = metadata_file_resource.get('import_comments', '')
        filename = metadata_file_resource.get('filename', source.get_filename())
        logger.info('Calculating md5 on file "%s"...' % source.get_url())
        md5 = source.calculate_md5()
        metadata_md5 = metadata_file_resource.get('md5')
        imported_from_url = metadata_file_resource.get(
            'imported_from_url', source.get_url())
        source_type = metadata_file_resource.get('source_type', 'imported')
        if metadata_md5 and md5 != metadata_md5:
            raise ImportManagerError(
                'md5 of file "%s" does not match value in its metadata '\
                'file. The file may have been corrupted. If it was changed '\
                'intentionally, you should not use the old metadata.'
                % source.get_url())
        file_data_object = {
            'type': 'file',
            'value':{
                'filename': filename,
                'md5': md5,
                'imported_from_url': imported_from_url,
                'source_type': 'imported',
                'link': False,
            }
        }
        if link:
            file_data_object['value'].update({
                'file_url': source.get_url(),
                'upload_status': 'complete',
                'link': True,
            })
        if comments:
            file_data_object['value']['import_comments'] = comments
        if metadata.get('uuid'):
            file_data_object['uuid'] = metadata.get('uuid')
        if metadata.get('datetime_created'):
            file_data_object['datetime_created'] = metadata.get('datetime_created')
        return file_data_object

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
        if file_data_object['value'].get('upload_status') == 'complete':
            logger.info(
                '   skipping upload because server already has the file %s@%s.' % (
                    file_data_object['value'].get('filename'),
                    file_data_object.get('uuid')))
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
        uuid = file_data_object['uuid']
        return self.connection.update_data_object(
            uuid,
            {'uuid': uuid, 'value': { 'upload_status': upload_status}}
        )

    def import_template(self, template_file, comments,
                        connection, force_duplicates=False,
                        retry=False):
        print 'Importing template from "%s".' % template_file.get_url()
        template = self._get_template(template_file)
        if not force_duplicates:
            templates = self._get_template_duplicates(template)
            if len(templates) > 0:
                name = templates[-1]['name']
                md5 = templates[-1]['md5']
                uuid = templates[-1]['uuid']
                warnings.warn(
                    'WARNING! The name and md5 hash "%s$%s" is already in use by one '
                    'or more templates. '\
                    'Use "--force-duplicates" to create another copy, but if you '\
                    'do you will have to use @uuid to reference these templates.'
                    % (name, md5))
                print 'Matching template already exists as "%s@%s".' % (name, uuid)
                return templates[0]
        if not template.get('comments'):
            if comments:
                template.update({'import_comments': comments})
        if not template.get('imported_from_url'):
            template.update({'imported_from_url': template_file.get_url()})

        try:
            template_from_server = connection.post_template(template)

        except HTTPError as e:
            if e.response.status_code==400:
                errors = e.response.json()
                raise SystemExit(
                    "ERROR! %s" % errors)
            else:
                raise

        print 'Imported template "%s@%s".' % (
            template_from_server['name'],
            template_from_server['uuid'])
        return template_from_server

    @classmethod
    def _get_template(self, template_file):
        md5 = template_file.calculate_md5()
        try:
            template_text = template_file.read()
        except Exception as e:
            raise SystemExit('ERROR! Unable to read file "%s". %s'
                             % (template_file.get_url(), str(e)))
        template = parse_as_yaml(template_text)
        try:
            template.update({'md5': md5})
        except AttributeError:
            raise SystemExit(
                'ERROR! Template at "%s" could not be parsed into a dict.'
                % template_file.get_url())
        return template

    def _get_template_duplicates(self, template):
	md5 = template.get('md5')
        name = template.get('name')
        templates = self.connection.get_template_index(
            query_string='%s$%s' % (name, md5))
        return templates
