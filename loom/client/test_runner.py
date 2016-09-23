#!/usr/bin/env python

import argparse
import os
import subprocess
import sys

class TestRunner:

    def __init__(self, args=None):
        # Parse arguments
        if args is None:
            args = self._get_args()

    def _get_args(self):
        parser = self.get_parser()
        args = parser.parse_args()
        return args

    @classmethod
    def get_parser(cls, parser=None):
        if parser is None:
            parser = argparse.ArgumentParser(__file__)
        return parser

    def run(self):

        # Create an environment variable dict with loom root as the PYTHONPATH
        loomroot = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        loomenv = dict(os.environ.copy(), PYTHONPATH=loomroot)

        manage_script = (os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'master', 'manage.py')))
        manage_script_dir = os.path.dirname(manage_script)
        subprocess.call([sys.executable, manage_script, 'test'], env=loomenv, cwd=manage_script_dir)

        client_dir = (os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'client')))
        subprocess.call([sys.executable, '-m', 'unittest', 'discover', client_dir])

        worker_dir = (os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'worker')))
        subprocess.call([sys.executable, '-m', 'unittest', 'discover', worker_dir])

        common_dir = (os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'common')))
        subprocess.call([sys.executable, '-m', 'unittest', 'discover', common_dir])

if __name__=='__main__':
    TestRunner().run()
