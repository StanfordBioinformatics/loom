#!/usr/bin/env python

import json
import requests

from xppf.client import settings_manager

class XppfRun:

    def __init__(self, args=None, skip_initialization=False):
        if not skip_initialization:
            self._initialize(args)

    def _initialize(self, args=None):
        if args is None:
            args=self._get_args()
        self.settings_manager = settings_manager.SettingsManager(settings_file = args.settings)
        self.pipeline_files = args.pipeline_file
        self.run()

    def _get_args(self):
        from argparse import ArgumentParser
        parser = ArgumentParser('xppfrun')
        parser.add_argument('pipeline_file', nargs='+')
        parser.add_argument('--settings', '-s', nargs=1, metavar='SETTINGS_FILE', help="Server settings. Use 'xppfserver savesettings -s SETTINGS_FILE' to save.")
        args = parser.parse_args()
        return args

    def _set_main_from_input_command(self, args):
        if args.command == 'run':
            self.main = self.run
        else:
            raise Exception('Did not recognize command %s' % args.command)

    def run(self):
        pipeline = self.merge_pipeline_files()
        try:
            response = requests.post(self.settings_manager.get_server_url() + '/run', data=json.dumps(pipeline))
        except requests.exceptions.ConnectionError as e:
            raise Exception("No response from server. (%s)" % e)

    def merge_pipeline_files(self):
        pipeline = {}
        for pipeline_file in self.pipeline_files:
            try: 
                with open(pipeline_file, 'r') as f:
                    pipeline_data = json.load(f)
            except IOError as e:
                raise Exception('Failed to open pipeline file %s. (%s)' % (pipeline_file, e))
            except ValueError:
                raise Exception("Failed to parse pipeline file file because it is not in valid JSON format: %s" % pipeline_file)
            pipeline.update(pipeline_data)
        return pipeline

if __name__=='__main__':
    XppfRun()
