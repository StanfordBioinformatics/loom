#!/usr/bin/env python

import os
import requests
import subprocess
import sys

class XppfServerControls:

    PID_FILE = '/tmp/xppf.pid'
    SERVER_MODULE = 'xppfserver.wsgi'
    BIND_IP = '127.0.0.1'
    BIND_PORT = '8000'
    SERVER_PATH = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '..', 'server'))
    STATUS_URL_RELATIVE = 'status'
    PROTOCOL = 'HTTP'

    def __init__(self, args=None):
        if args is None:
            args=self._get_args()
        self._set_run_method(args)
        self.run()

    def _get_args(self):
        from argparse import ArgumentParser
        parser = ArgumentParser()
        parser.add_argument('command', choices=['start', 'stop', 'status'])
        args = parser.parse_args()
        return args

    def _set_run_method(self, args):
        if args.command == 'status':
            self.run = self.status
        elif args.command == 'start':
            self.run = self.start
        elif args.command == 'stop':
            self.run = self.stop
        else:
            raise Exception('Did not recognize command %s' % args.command)

    def status(self):
        try:
            response = requests.get(
                "%s://%s:%s/%s" % (self.PROTOCOL, self.BIND_IP, self.BIND_PORT, self.STATUS_URL_RELATIVE)
            )
            if response.status_code == 200:
                print "server is ok"
            else:
                print "unexpected status code %s from server" % response.status_code
        except requests.exceptions.ConnectionError:
            print "no response from server"

    def start(self):
        env = self._add_server_to_python_path(os.environ.copy())
        subprocess.call(
            "gunicorn %s --bind %s:%s --pid %s --daemon" % (
                self.SERVER_MODULE, self.BIND_IP, self.BIND_PORT, self.PID_FILE),
            shell=True, 
            env=env)

    def stop(self):
        subprocess.call(
            "kill `cat %s`" % self.PID_FILE,
            shell=True
        )

    def _add_server_to_python_path(self, env):
        env.setdefault('PYTHONPATH', '')
        env['PYTHONPATH'] = "%s:%s" % (self.SERVER_PATH, env['PYTHONPATH'])
        return env


if __name__=='__main__':
    XppfServerControls()
