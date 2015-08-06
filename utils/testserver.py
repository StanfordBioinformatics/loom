import os
import unittest
from datetime import datetime
import requests
import subprocess
import time

from xppf.client import xppf_server_controls

class TestServer:
    """
    Launches a test XPPF server
    and executes management commands on it.
    The test server has its database flushed each time it starts.
    """

    def start(self, no_daemon=True):
        xsc_parser = xppf_server_controls.XppfServerControls._get_parser()
        arglist = ['start', '--require_default_settings', '--test_database']
        if no_daemon == True:
            arglist.append('--no_daemon')
        args = xsc_parser.parse_args(arglist)
        xs = xppf_server_controls.XppfServerControls(args=args)
        xs.main() # start server
        self.server_url = xs.settings_manager.get_server_url()
        self.wait_for_true(lambda: os.path.exists(xs.settings_manager.get_webserver_pidfile()))

    def stop(self):
        xsc_parser = xppf_server_controls.XppfServerControls._get_parser()
        args = xsc_parser.parse_args(['stop', '--require_default_settings'])
        xs = xppf_server_controls.XppfServerControls(args=args)
        xs.main()
        self.wait_for_true(lambda: not os.path.exists(xs.settings_manager.get_webserver_pidfile()))

    def wait_for_true(self, test_method, timeout_seconds=5):
        start_time = datetime.now()
        while not test_method():
            time.sleep(timeout_seconds/10.0)
            time_running = datetime.now() - start_time
            if time_running.seconds > timeout_seconds:
                raise Exception("Timeout")

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
