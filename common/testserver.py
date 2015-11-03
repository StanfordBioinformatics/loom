#!/usr/bin/env python

import os
import unittest
from datetime import datetime
import requests
import subprocess
import time
from loom.common.helper import Helper
from loom.client import loom_server_controls

class TestServer:
    """
    Launches a test loom server
    and executes management commands on it.
    The test server has its database flushed each time it starts.
    """

    def start(self, no_daemon=True):
        xsc_parser = loom_server_controls.LoomServerControls._get_parser()
        arglist = ['start', '--require_default_settings', '--test_database']
        if no_daemon == True:
            arglist.append('--no_daemon')
        args = xsc_parser.parse_args(arglist)
        self.xs = loom_server_controls.LoomServerControls(args=args)
        self.xs.main() # start server
        self.server_url = self.xs.settings_manager.get_server_url_for_client()

        # Confirm server started
        Helper.wait_for_true(self._webserver_started, timeout_seconds=5)

    def stop(self):
        xsc_parser = loom_server_controls.LoomServerControls._get_parser()
        args = xsc_parser.parse_args(['stop', '--require_default_settings'])
        xs = loom_server_controls.LoomServerControls(args=args)
        xs.main() # stop server

        # Confirm server stopped
        Helper.wait_for_true(self._webserver_stopped, timeout_seconds=5)

    def status(self):
        xsc_parser = loom_server_controls.LoomServerControls._get_parser()
        args = xsc_parser.parse_args(['status', '--require_default_settings'])
        xs = loom_server_controls.LoomServerControls(args=args)
        xs.main() # get server status

    def _webserver_started(self):
        return os.path.exists(self.xs.settings_manager.get_webserver_pidfile())

    def _webserver_stopped(self):
        return not os.path.exists(self.xs.settings_manager.get_webserver_pidfile())

    def run_job_queues(self):
        env = self._get_test_env()
        subprocess.call('%s run_job_queues' % self._get_manage_cmd(),
                        shell=True,
                        env=self._get_test_env())

    def dry_run_job_queues(self):
        env = self._get_test_env()
        subprocess.call('%s dry_run_job_queues' % self._get_manage_cmd(),
                        shell=True,
                        env=self._get_test_env())

    def _get_manage_cmd(self):
        return  os.path.join(os.path.dirname(__file__), '../master/manage.py')

    def _get_test_env(self):
        env = os.environ.copy()
        env['RACK_ENV'] = 'test'
        env['FILE_ROOT'] = '/tmp/'
        return env

    @classmethod
    def _get_parser(cls):
        import argparse
        parser = argparse.ArgumentParser("testserver")
        parser.add_argument('command', choices=['start', 'stop', 'status'])
        return parser

if __name__=='__main__':
    parser = TestServer._get_parser()
    args = parser.parse_args()
    if args.command == 'start':
        TestServer().start()
    elif args.command == 'stop':
        TestServer().stop()
    elif args.command == 'status':
        TestServer().status()
