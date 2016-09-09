#!/usr/bin/env python

import argparse
import os
import unittest
from datetime import datetime
import requests
import subprocess
import sys
import time
from loomengine.utils import helper
from loomengine.client import server
from loomengine.client.common import get_server_url


class TestServer:
    """
    Launches a test loom server
    and executes management commands on it.
    The test server has its database flushed each time it starts.
    """

    def setlocal(self):
        xsc_parser = server.get_parser()
        args = xsc_parser.parse_args(['--require_default_settings', 'set', 'local'])
        self.xs = server.ServerControlsFactory(args=args)
        self.xs.run() # set local server

    def start(self):
        xsc_parser = server.get_parser()
        arglist = ['--require_default_settings', '--test_database']
        arglist.append('start')
        args = xsc_parser.parse_args(arglist)
        self.xs = server.ServerControlsFactory(args=args)
        self.xs.run() # start server
        self.server_url = get_server_url()

        # Confirm server started
        helper.wait_for_true(self._webserver_started, timeout_seconds=5)

    def stop(self):
        xsc_parser = server.get_parser()
        args = xsc_parser.parse_args(['--require_default_settings', 'stop'])
        self.xs = server.ServerControlsFactory(args=args)
        self.xs.run() # stop server

        # Confirm server stopped
        helper.wait_for_true(self._webserver_stopped, timeout_seconds=5)

    def status(self):
        xsc_parser = server.get_parser()
        args = xsc_parser.parse_args(['--require_default_settings', 'status'])
        xs = server.ServerControlsFactory(args=args)
        xs.run() # get server status

    def _webserver_started(self):
        return os.path.exists(self.xs.settings_manager.settings['WEBSERVER_PIDFILE'])

    def _webserver_stopped(self):
        return not os.path.exists(self.xs.settings_manager.settings['WEBSERVER_PIDFILE'])

    def run_job_queues(self):
        env = self._get_test_env()
        subprocess.call('%s %s run_job_queues' % (sys.executable, self._get_manage_cmd()),
                        shell=True,
                        env=self._get_test_env())

    def dry_run_job_queues(self):
        env = self._get_test_env()
        subprocess.call('%s %s dry_run_job_queues' % (sys.executable, self._get_manage_cmd()),
                        shell=True,
                        env=self._get_test_env())

    def _get_manage_cmd(self):
        return  os.path.join(os.path.dirname(__file__), '../master/manage.py')

    def _get_test_env(self):
        env = os.environ.copy()
        env['LOOM_TEST_DATABASE'] = 'true'
        env['FILE_ROOT'] = '/tmp/'
        env['FILE_SERVER_FOR_WORKER'] = '127.0.0.1'
        return env

    @classmethod
    def _get_parser(cls):
        parser = argparse.ArgumentParser("testserver")
        parser.add_argument('command', choices=['start', 'stop', 'status', 'set'])
        return parser

if __name__=='__main__':
    parser = TestServer._get_parser()
    args = parser.parse_args()
    if args.command == 'set':
        TestServer().setlocal()
    elif args.command == 'start':
        TestServer().start()
    elif args.command == 'stop':
        TestServer().stop()
    elif args.command == 'status':
        TestServer().status()
