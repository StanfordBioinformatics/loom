#!/usr/bin/env python
import os
import sys

if __name__ == "__main__" and __package__ is None:
    rootdir=os.path.abspath('../..')
    sys.path.append(rootdir)

import argparse

from loomengine import server
from loomengine.common import verify_has_connection_settings, \
    get_server_url, verify_server_is_running, get_token
from loomengine.exceptions import *
from loomengine_utils.connection import Connection


class FileLabelAdd(object):
    """Add a new file labels
    """

    def __init__(self, args=None):

        # Args may be given as an input argument for testing purposes
        # or from the main parser.
        # Otherwise get them from the parser.
        if args is None:
            args = self._get_args()
        self.args = args
        verify_has_connection_settings()
        server_url = get_server_url()
        verify_server_is_running(url=server_url)
        self.connection = Connection(server_url, token=get_token())

    def _get_args(self):
        self.parser = self.get_parser()
        return self.parser.parse_args()

    @classmethod
    def get_parser(cls, parser=None):
        # If called from main, use the subparser provided.
        # Otherwise create a top-level parser here.
        if parser is None:
            parser = argparse.ArgumentParser(__file__)

        parser.add_argument(
            'target',
            metavar='TARGET',
            help='identifier for file to be labeled')
        parser.add_argument(
            'label',
            metavar='LABEL', help='label name to be added')
        return parser

    def run(self):
        files = self.connection.get_data_object_index(
            min=1, max=1,
            query_string=self.args.target, type='file')

        label_data = {'label': self.args.label}
        label = self.connection.post_data_label(files[0]['uuid'], label_data)
        print 'Target "%s@%s" has been labeled as "%s"' % \
            (files[0]['value'].get('filename'),
             files[0].get('uuid'),
             label.get('label'))

class FileLabelRemove(object):
    """Remove a file label
    """

    def __init__(self, args=None):
        if args is None:
            args = self._get_args()
        self.args = args
        verify_has_connection_settings()
        server_url = get_server_url()
        verify_server_is_running(url=server_url)
        self.connection = Connection(server_url, token=get_token())

    def _get_args(self):
        self.parser = self.get_parser()
        return self.parser.parse_args()

    @classmethod
    def get_parser(cls, parser=None):
        # If called from main, use the subparser provided.
        # Otherwise create a top-level parser here.
        if parser is None:
            parser = argparse.ArgumentParser(__file__)

        parser.add_argument(
            'target',
            metavar='TARGET',
            help='identifier for file to be unlabeled')
        parser.add_argument(
            'label',
            metavar='LABEL', help='label name to be removed')
        return parser

    def run(self):
        files = self.connection.get_data_object_index(
            min=1, max=1,
            query_string=self.args.target, type='file')

        label_data = {'label': self.args.label}
        label = self.connection.remove_data_label(files[0]['uuid'], label_data)
        print 'Label %s has been removed from file "%s@%s"' % \
            (label.get('label'),
             files[0]['value'].get('filename'),
             files[0].get('uuid'))


class FileLabelList(object):

    def __init__(self, args=None):
        if args is None:
            args = self._get_args()
        self.args = args
        verify_has_connection_settings()
        server_url = get_server_url()
        verify_server_is_running(url=server_url)
        self.connection = Connection(server_url, token=get_token())

    def _get_args(self):
        self.parser = self.get_parser()
        return self.parser.parse_args()

    @classmethod
    def get_parser(cls, parser=None):
        # If called from main, use the subparser provided.
        # Otherwise create a top-level parser here.
        if parser is None:
            parser = argparse.ArgumentParser(__file__)

        parser.add_argument(
            'target',
            metavar='TARGET',
            nargs='?',
            help='show labels only for the specified file')

        return parser

    def run(self):
        if self.args.target:
            files = self.connection.get_data_object_index(
                min=1, max=1,
                query_string=self.args.target, type='file')
            label_data = self.connection.list_data_labels(files[0]['uuid'])
            labels = label_data.get('labels', [])
            print '[showing %s labels]' % len(labels)
            for label in labels:
                print label
        else:
            label_list = self.connection.get_data_label_index()
            label_counts = {}
            for item in label_list:
                label_counts.setdefault(item.get('label'), 0)
                label_counts[item.get('label')] += 1
            print '[showing %s labels]' % len(label_counts)
            for key in label_counts:
                print "%s (%s)" % (key, label_counts[key])


class FileLabel(object):
    """Configures and executes subcommands under "label" on the parent parser.
    """

    def __init__(self, args=None):
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

        add_subparser = subparsers.add_parser(
            'add', help='add a file label')
        FileLabelAdd.get_parser(add_subparser)
        add_subparser.set_defaults(SubSubSubcommandClass=FileLabelAdd)

        remove_subparser = subparsers.add_parser(
            'remove', help='remove a file label')
        FileLabelRemove.get_parser(remove_subparser)
        remove_subparser.set_defaults(SubSubSubcommandClass=FileLabelRemove)

        list_subparser = subparsers.add_parser(
            'list', help='list file labels')
        FileLabelList.get_parser(list_subparser)
        list_subparser.set_defaults(SubSubSubcommandClass=FileLabelList)

        return parser

    def run(self):
        self.args.SubSubSubcommandClass(self.args).run()


if __name__=='__main__':
    response = FileLabel().run()
