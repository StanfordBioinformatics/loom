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
        loom_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        loom_env = dict(os.environ.copy(), PYTHONPATH=loom_root)

        # Becomes 1 if any tests fail
        returncode = 0

        manage_script = (os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'master', 'manage.py')))
        manage_script_dir = os.path.dirname(manage_script)
        returncode |= subprocess.call([sys.executable, manage_script, 'test'], env=loom_env, cwd=manage_script_dir)

        client_dir = (os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'client')))
        returncode |= subprocess.call([sys.executable, '-m', 'unittest', 'discover', client_dir])

        worker_dir = (os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'worker')))
        returncode |= subprocess.call([sys.executable, '-m', 'unittest', 'discover', worker_dir])

        utils_dir = (os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'utils')))
        returncode |= subprocess.call([sys.executable, '-m', 'unittest', 'discover', utils_dir])

        print 'Return code: %s' % returncode
        return returncode

if __name__=='__main__':
    TestRunner().run()
