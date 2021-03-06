#!/usr/bin/env python
import argparse
import os
import sys

from loomengine import server
from loomengine import verify_has_connection_settings, \
    get_server_url, verify_server_is_running, get_token
from loomengine_utils.connection import Connection
from loomengine_utils.exceptions import LoomengineUtilsError


class RunLabelAdd(object):
    """Add a new run labels
    """

    def __init__(self, args=None, silent=False):

        # Args may be given as an input argument for testing purposes
        # or from the main parser.
        # Otherwise get them from the parser.
        if args is None:
            args = self._get_args()
        self.args = args
        self.silent = silent
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
            help='identifier for run to be labeled')
        parser.add_argument(
            'label',
            metavar='LABEL', help='label name to be added')
        return parser

    def run(self):
        try:
            runs = self.connection.get_run_index(
                min=1, max=1,
                query_string=self.args.target)
        except LoomengineUtilsError as e:
            raise SystemExit("ERROR! Failed to get run list: '%s'" % e)

        label_data = {'label': self.args.label}
        try:
            label = self.connection.post_run_label(runs[0]['uuid'], label_data)
        except LoomengineUtilsError as e:
            raise SystemExit("ERROR! Failed to create label: '%s'" % e)
        if not self.silent:
            print 'Target "%s@%s" has been labeled as "%s"' % \
                (runs[0].get('name'),
                 runs[0].get('uuid'),
                 label.get('label'))


class RunLabelRemove(object):
    """Remove a run label
    """

    def __init__(self, args=None, silent=False):
        if args is None:
            args = self._get_args()
        self.args = args
        self.silent = silent
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
            help='identifier for run to be unlabeled')
        parser.add_argument(
            'label',
            metavar='LABEL', help='label name to be removed')
        return parser

    def run(self):
        try:
            runs = self.connection.get_run_index(
                min=1, max=1,
                query_string=self.args.target)
        except LoomengineUtilsError as e:
            raise SystemExit("ERROR! Failed to get run list: '%s'" % e)
        label_data = {'label': self.args.label}
        try:
            label = self.connection.remove_run_label(
                runs[0]['uuid'], label_data)
        except LoomengineUtilsError as e:
            raise SystemExit("ERROR! Failed to remove label: '%s'" % e)
        if not self.silent:
            print 'Label %s has been removed from run "%s@%s"' % \
                (label.get('label'),
                 runs[0].get('name'),
                 runs[0].get('uuid'))


class RunLabelList(object):

    def __init__(self, args=None, silent=False):
        if args is None:
            args = self._get_args()
        self.args = args
        self.silent = silent
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
            help='show labels only for the specified run')

        return parser

    def run(self):
        if self.args.target:
            try:
                runs = self.connection.get_run_index(
                    min=1, max=1,
                    query_string=self.args.target)
            except LoomengineUtilsError as e:
                raise SystemExit("ERROR! Failed to get run list: '%s'" % e)
            try:
                label_data = self.connection.list_run_labels(runs[0]['uuid'])
            except LoomengineUtilsError as e:
                raise SystemExit("ERROR! Failed to get label list: '%s'" % e)
            labels = label_data.get('labels', [])
            if not self.silent:
                print '[showing %s labels]' % len(labels)
                for label in labels:
                    print label
        else:
            try:
                label_list = self.connection.get_run_label_index()
            except LoomengineUtilsError as e:
                raise SystemExit("ERROR! Failed to get label list: '%s'" % e)
            label_counts = {}
            for item in label_list:
                label_counts.setdefault(item.get('label'), 0)
                label_counts[item.get('label')] += 1
            if not self.silent:
                print '[showing %s labels]' % len(label_counts)
                for key in label_counts:
                    print "%s (%s)" % (key, label_counts[key])


class RunLabel(object):
    """Configures and executes subcommands under "label" on the parent parser.
    """

    def __init__(self, args=None, silent=False):
        if args is None:
            args = self._get_args()
        self.args = args
        self.silent = silent

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
            'add', help='add a run label')
        RunLabelAdd.get_parser(add_subparser)
        add_subparser.set_defaults(SubSubSubcommandClass=RunLabelAdd)

        remove_subparser = subparsers.add_parser(
            'remove', help='remove a run label')
        RunLabelRemove.get_parser(remove_subparser)
        remove_subparser.set_defaults(SubSubSubcommandClass=RunLabelRemove)

        list_subparser = subparsers.add_parser(
            'list', help='list run labels')
        RunLabelList.get_parser(list_subparser)
        list_subparser.set_defaults(SubSubSubcommandClass=RunLabelList)

        return parser

    def run(self):
        return self.args.SubSubSubcommandClass(
            self.args, silent=self.silent).run()


if __name__ == '__main__':
    response = RunLabel().run()
