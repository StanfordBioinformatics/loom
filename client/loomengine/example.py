#!/usr/bin/env python

import argparse
from collections import OrderedDict
import glob
import os
import shutil

EXAMPLE_DIR = os.path.join(os.path.dirname(__file__), 'examples')
EXAMPLE_INDEX = [
    ('hello_world', 'steps in serial and parallel, file inputs'),
    ('join_two_words', 'simplest example'),
    ('capitalize_words', 'array data, iterating over an array input'),
    ('join_array_of_words', 'array data, gather mode on an input'),
    ('split_words_into_array', 'array data, scatter mode on an output, output parsers'),
    ('add_then_multiply', 'multistep templates, connecting inputs and outputs, custom interpreter'),
    ('building_blocks', 'reusing templates'),
    ('search_file', 'file inputs'),
    ('word_combinations', 'scatter-gather, input groups, output mode gather(n)'),
    ('sentence_scoring', 'nested scatter-gather'),
]


class ExampleExport(object):

    def __init__(self, args):
        self.args = args

    @classmethod
    def get_parser(cls, parser):
        parser.add_argument(
            'example_name',
            metavar='EXAMPLE_NAME',
            help='Name of example to be exported.')
        parser.add_argument(
            '-d', '--destination',
            metavar='DESTINATION',
            help='destination directory')
        return parser

    def run(self):
        example_names = OrderedDict(EXAMPLE_INDEX).keys()
        if not self.args.example_name in example_names:
            raise SystemExit('ERROR! Unknown example "%s".\nChoose from %s' % (self.args.example_name, example_names))
        example_path = os.path.join(EXAMPLE_DIR, self.args.example_name)
        if self.args.destination:
            destination = self.args.destination
        else:
            destination = os.getcwd()
        self._export_example(example_path, destination)

    def _export_example(self, example_path, destination):
        target_dir = os.path.join(destination, os.path.basename(example_path))
        if os.path.exists(target_dir):
            raise SystemExit(
                'ERROR! Target directory already exists: %s' % target_dir)
        shutil.copytree(example_path, target_dir)
        print 'Exported example "%s"\n    to "%s"' % \
            (os.path.basename(example_path), target_dir)

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


class ExampleList(object):

    def __init__(self, args):
        self.args = args

    @classmethod
    def get_parser(cls, parser):
        return parser

    def run(self):
        for example in EXAMPLE_INDEX:
            example_name = example[0]
            description = example[1]
            self._render_example(example_name, description)

    def _render_example(self, example_name, description):
        print '%s:\n    %s\n' % (example_name, description)


class Example(object):
    """Configures and executes subcommands under "example" on the main parser.
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

        list_subparser = subparsers.add_parser(
            'list', help='list examples')
        ExampleList.get_parser(list_subparser)
	list_subparser.set_defaults(SubSubcommandClass=ExampleList)

        export_subparser = subparsers.add_parser(
            'export', help='export an example to the current directory')
        ExampleExport.get_parser(export_subparser)
        export_subparser.set_defaults(SubSubcommandClass=ExampleExport)

        return parser

    def run(self):
        self.args.SubSubcommandClass(self.args).run()


if __name__=='__main__':
    response = Example().run()
