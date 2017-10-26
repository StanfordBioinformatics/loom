#!/usr/bin/env python

import argparse
import glob
import os
from requests.exceptions import HTTPError
import sys
import warnings

from loomengine import _render_time
from loomengine.common import verify_server_is_running, get_server_url, \
    verify_has_connection_settings, parse_as_json_or_yaml, get_token
from loomengine.template_tag import TemplateTag
from loomengine.template_label import TemplateLabel
from loomengine_utils.filemanager import FileManager
from loomengine_utils.connection import Connection


class TemplateImport(object):

    def __init__(self, args):
        self.args = args
        verify_has_connection_settings()
        server_url = get_server_url()
        verify_server_is_running(url=server_url)
        token = get_token()
        self.filemanager = FileManager(server_url, token=token)
        self.connection = Connection(server_url, token=token)

    @classmethod
    def get_parser(cls, parser):
        parser.add_argument(
            'template',
            metavar='TEMPLATE_FILE', help='template to be imported, '\
            'in YAML or JSON format')
        parser.add_argument(
            '-c', '--comments',
            metavar='COMMENTS',
            help='comments. '\
            'Give enough detail for traceability')
        parser.add_argument('-d', '--force-duplicates', action='store_true',
                            default=False,
                            help='force upload even if another template with '\
                            'the same name and md5 exists')
        parser.add_argument('-r', '--retry', action='store_true',
                            default=False,
                            help='allow retries if there is a failure '\
                            'connecting to storage')
        parser.add_argument('-t', '--tag', metavar='TAG', action='append',
                            help='tag the template when it is created')
        parser.add_argument('-l', '--label', metavar='LABEL', action='append',
                            help='label the template when it is created')
        return parser

    def run(self):
        template = self.import_template(self.args.template,
                                    self.args.comments,
                                    self.filemanager,
                                    self.connection,
                                    force_duplicates=self.args.force_duplicates,
                                    retry=self.args.retry)
        self._apply_tags(template)
        self._apply_labels(template)
        return template


    @classmethod
    def import_template(cls, template_file, comments,
                        filemanager, connection, force_duplicates=False,
                        retry=False):
        print 'Importing template from "%s".' % filemanager.normalize_url(
            template_file)
        (template, source_url) = cls._get_template(template_file, filemanager, retry)
        if not force_duplicates:
            templates = filemanager.get_template_duplicates(template)
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
        if comments:
            template.update({'import_comments': comments})
        if source_url:
            template.update({'imported_from_url': source_url})

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
    def _get_template(cls, template_file, filemanager, retry):
        md5 = filemanager.calculate_md5(template_file, retry=retry)
        try:
            (template_text, source_url) = filemanager.read_file(template_file,
                                                                retry=retry)
        except Exception as e:
            raise SystemExit('ERROR! Unable to read file "%s". %s'
                            % (template_file, str(e)))
        template = parse_as_json_or_yaml(template_text)
        try:
            template.update({'md5': md5})
        except AttributeError:
            raise SystemExit(
                'ERROR! Template at "%s" could not be parsed into a dict.'
                % os.path.abspath(template_file))
        return template, source_url

    def _apply_tags(self, template):
        if not self.args.tag:
            return
        for tagname in self.args.tag:
            tag_data = {'tag': tagname}
            tag = self.connection.post_template_tag(template.get('uuid'), tag_data)
            print 'Template "%s@%s" has been tagged as "%s"' % \
                (template.get('name'),
                 template.get('uuid'),
                 tag.get('tag'))

    def _apply_labels(self, template):
        if not self.args.label:
            return
        for labelname in self.args.label:
            label_data = {'label': labelname}
            label = self.connection.post_template_label(
                template.get('uuid'), label_data)
            print 'Template "%s@%s" has been labeled as "%s"' % \
                (template.get('name'),
                 template.get('uuid'),
                 label.get('label'))


class TemplateExport(object):

    def __init__(self, args):
        self.args = args
        verify_has_connection_settings()
        server_url = get_server_url()
        verify_server_is_running()
        self.connection = Connection(server_url, token=get_token())
        self.filemanager = FileManager(server_url)

    @classmethod
    def get_parser(cls, parser):
        parser.add_argument(
            'template_id',
            metavar='TEMPLATE_ID', help='template to be downloaded')
        parser.add_argument(
            '-d', '--destination',
            metavar='DESTINATION',
            help='destination filename or directory')
        parser.add_argument(
            '-f', '--format',
            choices=['json', 'yaml'],
            default='yaml',
            help='data format for downloaded template')
        parser.add_argument(
            '-r', '--retry', action='store_true',
            default=False,
            help='allow retries if there is a failure '\
            'connecting to storage')
        return parser

    def run(self):
        template = self.connection.get_template_index(query_string=self.args.template_id, min=1, max=1)[0]
        destination_url = self._get_destination_url(template, retry=self.args.retry)
        self._save_template(template, destination_url, retry=self.args.retry)

    def _get_destination_url(self, template, retry=False):
        default_name = '%s.%s' % (template['name'], self.args.format)
        return self.filemanager.get_destination_file_url(self.args.destination, default_name, retry=retry)

    def _save_template(self, template, destination, retry=False):
        print 'Exporting template %s@%s to %s...' % (template.get('name'), template.get('uuid'), destination)
        if self.args.format == 'json':
            template_text = json.dumps(template, indent=4, separators=(',', ': '))
        elif self.args.format == 'yaml':
            template_text = yaml.safe_dump(template, default_flow_style=False)
        else:
            raise Exception('Invalid format type %s' % self.args.format)
        self.filemanager.write_to_file(destination, template_text, retry=retry)
        print '...finished exporting template'


class TemplateList(object):

    def __init__(self, args):
        self.args = args
        verify_has_connection_settings()
        server_url = get_server_url()
        verify_server_is_running(url=server_url)
        self.connection = Connection(server_url, token=get_token())

    @classmethod
    def get_parser(cls, parser):
        parser.add_argument(
            'template_id',
            nargs='?',
            metavar='TEMPLATE_IDENTIFIER',
            help='Name or ID of template(s) to list.')
        parser.add_argument(
            '-d', '--detail',
            action='store_true',
            help='Show detailed view of templates')
        parser.add_argument(
            '-a', '--all',
            action='store_true',
            help='List all templates, including nested children. '\
            '(ignored when TEMPLATE_IDENTIFIER is given)')
        parser.add_argument('-l', '--label', metavar='LABEL', action='append',
                            help='Filter by label')
        return parser

    def run(self):
        if self.args.template_id:
            imported = False
        else:
            imported = not self.args.all
        offset=0
        limit=10
        while True:
            data = self.connection.get_template_index_with_limit(
                labels=self.args.label,
                limit=limit, offset=offset,
                query_string=self.args.template_id,
                imported=imported)
            if offset == 0:
                print '[showing %s templates]' % data.get('count')
            self._list_templates(data['results'])
            if data.get('next'):
                offset += limit
            else:
                break

    def _list_templates(self, templates):
        for template in templates:
            print self._render_template(template)

    def _render_template(self, template):
        template_identifier = '%s@%s' % (template['name'], template['uuid'])
        if self.args.detail:
            text = '---------------------------------------\n'
            text += 'Template: %s\n' % template_identifier
            text += '  - md5: %s\n' % template.get('md5')
            text += '  - Imported: %s\n' % \
                    _render_time(template['datetime_created'])
            if template.get('inputs'):
                text += '  - Inputs\n'
                for input in template['inputs']:
                    text += '    - %s\n' % input['channel']
            if template.get('outputs'):
                text += '  - Outputs\n'
                for output in template['outputs']:
                    text += '    - %s\n' % output['channel']
            if template.get('steps'):
                text += '  - Steps\n'
                for step in template['steps']:
                    text += '    - %s@%s\n' % (step['name'], step['uuid'])
            if template.get('command'):
                text += '  - Command: %s\n' % template['command']
        else:
            text = 'Template: %s' % template_identifier
        return text



class Template(object):
    """Configures and executes subcommands under "template" on the main parser.
    """

    def __init__(self, args=None):
        
        # Args may be given as an input argument for testing purposes.
        # Otherwise get them from the parser.
        if args is None:
            args = self._get_args()
        self.args = args

    def _get_args(self):
        parser = self.get_parser()
        return parser.parse_args()

    @classmethod
    def get_parser(cls, parser=None):

        # If called from main, a subparser should be provided.
        # Otherwise we create a top-level parser here.
        if parser is None:
            parser = argparse.ArgumentParser(__file__)

        subparsers = parser.add_subparsers()

        import_subparser = subparsers.add_parser(
            'import', help='import a template')
        TemplateImport.get_parser(import_subparser)
        import_subparser.set_defaults(SubSubcommandClass=TemplateImport)

        export_subparser = subparsers.add_parser(
            'export', help='export a template')
        TemplateExport.get_parser(export_subparser)
        export_subparser.set_defaults(SubSubcommandClass=TemplateExport)

        list_subparser = subparsers.add_parser(
            'list', help='list templates')
        TemplateList.get_parser(list_subparser)
	list_subparser.set_defaults(SubSubcommandClass=TemplateList)

        tag_subparser = subparsers.add_parser('tag', help='manage template tags')
        TemplateTag.get_parser(tag_subparser)
        tag_subparser.set_defaults(SubSubcommandClass=TemplateTag)

        label_subparser = subparsers.add_parser('label', help='manage template labels')
        TemplateLabel.get_parser(label_subparser)
        label_subparser.set_defaults(SubSubcommandClass=TemplateLabel)

        return parser

    def run(self):
        self.args.SubSubcommandClass(self.args).run()


if __name__=='__main__':
    response = Template().run()
