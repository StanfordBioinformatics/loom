#!/usr/bin/env python

import argparse
import daemon
from daemon import runner
import os
import re
import subprocess
import time
from main import App

class LoomDaemon:
    """
    The loom daemon runs alongside the loom server.

    It periodically calls a heartbeat function that 
    triggers work queue updates, starts jobs, and 
    monitors jobs in progress.
    """

    def __init__(self, args=None):
        if args is None:
            parser = self.get_parser()
            args = parser.parse_args()

        self.command = args.command
        self.debug = args.debug
        self.pidfile = args.pidfile[0]

        self.logfile = self._get_argument(args.logfile, '/tmp/loom_daemon.log')
        self.loglevel = self._get_argument(args.loglevel, 'INFO')

    def _get_argument(self, arg_value, default):
        if arg_value is None:
            return default

        if len(arg_value) == 1:
            return arg_value[0]
        elif len(arg_value) > 1:
            raise Exception('Only 1 logfile was expected. There may be a bug in the parser. Found %s' % arg_value)
        else:
            return default

    def run(self):
        if self.command == 'start':
            self.start_server()
        elif self.command == 'stop':
            self.stop_server()
        else:
            raise Exception("Unrecognized command %s" % self.command)

    def start_server(self):
        if self._is_daemon_running():
            print "Daemon running, not starting"
            return
        if not self.debug:
            # Disable daemon if debug is on
            daemon_context = self._get_daemon_context()
            with daemon_context:
                App(logfile=self.logfile).run() # This is the main function of the daemon

    def stop_server(self):
        pid = self._get_pid()
        if pid is None:
            return
        else:
            subprocess.call('kill %s' % pid, shell=True)

    def _get_daemon_context(self):
        return daemon.DaemonContext(
            working_directory='.',
            pidfile=daemon.pidfile.PIDLockFile(self.pidfile)
            )

    def _get_pid(self):
        try:
            with open(self.pidfile) as f:
                pid = f.read().strip()
            self._validate_pid(pid)
            return pid
        except:
            return None

    def _validate_pid(self, pid):
        if not re.match('^[0-9]*$', pid):
            raise Exception('Invalid pid "%s"' % pid)

    def _is_daemon_running(self):
        if self._get_pid() is None:
            return False
        else:
            return True

    @classmethod
    def get_parser(cls):
        parser = argparse.ArgumentParser('loom daemon')
        parser.add_argument('command', choices=['start', 'stop'])
        parser.add_argument('--pidfile', '-p', help="Location of file to record the daemon's pid", required=True, nargs=1, metavar='PIDFILE')
        parser.add_argument('--logfile', '-l', help="Location of daemon log file", nargs=1, metavar='LOGFILE')
        parser.add_argument('--loglevel', '-f', help="Level of messsage to be logged", nargs=1, metavar='LOGLEVEL')
        parser.add_argument('--debug', '-d', help=argparse.SUPPRESS, action='store_true')
        return parser

if __name__=='__main__':
    LoomDaemon().run()
