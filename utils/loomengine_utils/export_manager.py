import datetime
import logging
import os
import yaml

from loomengine_utils.file_utils import File

logger = logging.getLogger(__name__)


class ExportManagerError(Exception):
    pass

def _get_default_bulk_export_directory():
    dirname = 'loom-bulk-export-%s' % \
              datetime.datetime.now().strftime('%Y-%m-%dT%H.%M.%S.%f')
    return os.path.join(os.getcwd(), dirname)

class ExportManager(object):

    def __init__(self, connection, storage_settings=None):
        self.connection = connection
        if storage_settings is None:
            storage_settings = connection.get_storage_settings()
        self.storage_settings = storage_settings      

    def bulk_export_files(self, files, destination_directory=None,
                          retry=False, export_metadata=True, link_files=False):
        if destination_directory == None:
            destination_directory = _get_default_bulk_export_directory()
        for file in files:
            file_directory = os.path.join(
                destination_directory,
                'files',
                file.get('uuid'))
            self.export_file('@%s' % file.get('uuid'),
                             destination_directory=file_directory,
                             retry=retry,
                             export_metadata=export_metadata,
                             export_raw_file=not link_files)

    def bulk_export_templates(self, templates,
                              destination_directory=None,
                              retry=False, link_files=False,
                              editable=False):
        if destination_directory is None:
            destination_directory=_get_default_bulk_export_directory()

        expanded_templates = self._expand_templates(templates)
        template_files = self._get_files_from_templates(expanded_templates)

        # If templates are editable, UUIDs will be stripped. But to avoid
        # file collisions, we save the UUIDs to use as a subdirectory that
        # makes each template's path unique
        template_uuids = [t['uuid'] for t in expanded_templates]

        if editable:
            templates = self._convert_templates_to_editable(expanded_templates)

        # If template is editable, exclude file metadata with UUIDs
        export_file_metadata = not editable

        self.bulk_export_files(template_files,
                               destination_directory=destination_directory,
                               retry=retry, link_files=link_files,
                               export_metadata=export_file_metadata)
        for template, uuid in zip(expanded_templates, template_uuids):
            template_destination = self._get_template_destination(
                template,
                destination_directory=os.path.join(
                    destination_directory, 'templates', uuid))
            self._save_template(template, template_destination, retry=retry)
        return templates

    def export_template(self, templates, destination_directory=None,
                        retry=False, link_files=False, editable=False):
        template = self._expand_template(template)
        files = self._get_files_from_template(template)
        if editable:
            template = self._convert_template_to_editable(template)
        template_destination = self._get_template_destination(
            template, destination_directory=destination_directory)
        # If template is editable, exclude file metadata with UUIDs
        export_file_metadata = not editable
        self.bulk_export_files(
            files, destination_directory=template_destination+'.dependencies',
            retry=retry, link_files=link_files, export_metadata=export_file_metadata)
        self._save_template(template, template_destination, retry=retry)

    def _expand_template(self, template):
        for input in template.get('inputs', []):
            if input['data']:
                input['data'] = self.connection.get_data_node(
                    input['data']['uuid'], expand=True)
        expanded_steps = []
        for step in template.get('steps', []):
            step = self.connection.get_template(step['uuid'])
            step = self._expand_template(step)
            expanded_steps.append(step)
        if expanded_steps:
            template['steps'] = expanded_steps
        return template

    def _expand_templates(self, templates):
        return [self._expand_template(t) for t in templates]

    def _convert_template_to_editable(self, template):
        # Delete data that is unique to the original instance. User can edit
        # and reimport this template with a new uuid, datetime_created, etc.
        template.pop('uuid', None)
        template.pop('url', None)
        template.pop('datetime_created', None)
        template.pop('imported_from_url', None)

        for input in template.get('inputs', []):
            if input['data']:
                input['data'] = self._convert_data_node_to_editable(input['data'])
        converted_steps = []
        for step in template.get('steps', []):
            converted_steps.append(self._convert_template_to_editable(step))
        if converted_steps:
            template['steps'] = converted_steps
        return template

    def _convert_templates_to_editable(self,templates):
        return [self._convert_template_to_editable(t) for t in templates]

    def _convert_data_node_to_editable(self, data_node):
        data_node.pop('uuid', None)
        data_node.pop('url', None)
        if data_node.get('contents'):
            data_node['contents'] = self._convert_data_contents_to_editable(
                data_node['contents'])
        return data_node

    def _convert_data_contents_to_editable(self, contents):
        if isinstance(contents, list):
            return [self._convert_data_contents_to_editable(item)
                    for item in contents]
        else:
            if contents.get('type') == 'file':
                new_contents = {
                    'type': 'file',
                    'value': {
                        'filename': contents['value'].get('filename'),
                        'md5': contents['value'].get('md5')
                    }
                }
            else:
                new_contents = {
                    'type': contents.get('type'),
                    'value': contents.get('value')
                }
            return new_contents

    def _get_files_from_template(self, template):
        return self._get_files_from_templates([template,])

    def _get_files_from_templates(self, templates):
        files = []
        file_uuids = set()

        def add_files(new_files, files, file_uuids):
            for file in new_files:
                if file.get('uuid') not in file_uuids:
                    file_uuids.add(file.get('uuid'))
                    files.append(file)

        for template in templates:
            inputs = template.get('inputs', None)
            if inputs:
                for input in inputs:
                    if input.get('type') == 'file' and input.get('data'):
                        add_files(
                            self._get_files_from_data_contents(
                                input['data']['contents']),
                            files,
                            file_uuids)
            steps = template.get('steps', None)
            if steps:
                add_files(self._get_files_from_templates(steps),
                          files,
                          file_uuids)
        return files

    def _get_files_from_data_contents(self, contents):
        if isinstance(contents, list):
            files = []
            for item in contents:
                files.extend(self._get_files_from_data_contents(item))
        else:
            files = [contents]
        return files

    def _get_template_destination(
            self, template, destination_directory=None):
        if destination_directory == None:
            destination_directory = os.getcwd()
        return os.path.join(destination_directory, template['name']+'.yaml')

    def _save_template(self, template, destination, retry=False):
        print 'Exporting template %s@%s to %s...' % (
            template.get('name'), template.get('uuid'), destination)
        template_text = yaml.safe_dump(template, default_flow_style=False)
        template_file = File(destination, self.storage_settings, retry=retry)
        template_file.write(template_text)
        print '...finished exporting template'

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
