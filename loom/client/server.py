#!/usr/bin/env python

import argparse
import os
import re
import requests
import subprocess
import sys
import warnings

from loom.client import settings_manager

DAEMON_EXECUTABLE = os.path.abspath(
    os.path.join(
    os.path.dirname(__file__),
    '../master/loomdaemon/loom_daemon.py'
    ))

def is_server_running(master_url):
    try:
        response = requests.get(master_url + '/api/status')
        if response.status_code == 200:
            return True
        else:
            raise Exception("unexpected status code %s from server" % response.status_code)
    except requests.exceptions.ConnectionError:
        return False


class ServerControls:
    """
    This class provides methods for managing the loom server, specifically the commands:
    - create
    - start
    - stop
    - delete
    - set
    - status

    Users should call this through 'loom server' to ensure the environment is configured.
    """

    def __init__(self, args=None):
        if args is None:
            args=self._get_args()
        self.args = args
        #self.settings_manager = settings_manager.SettingsManager(settings_file=args.settings, require_default_settings=args.require_default_settings)
        self._set_run_function(args)

    def _set_run_function(self, args):
        # Map user input command to class method
        command_to_method_map = {
            'status': self.status,
            'start': self.start,
            'stop': self.stop,
            'create': self.create,
            'delete': self.delete,
            'set': self.setserver
        }
        try:
            self.run = command_to_method_map[args.command]
        except KeyError:
            raise Exception('Did not recognize command %s' % args.command)

    @classmethod
    def get_parser(cls, parser=None):
        if parser is None:
            parser = argparse.ArgumentParser(__file__)

        parser.add_argument('--fg_webserver', action='store_true', help='Run webserver in the foreground. Needed to keep Docker container running.')
        parser.add_argument('--test_database', '-t', action='store_true', help=argparse.SUPPRESS)
        parser.add_argument('--no_daemon', '-n', action='store_true', help=argparse.SUPPRESS)
        parser.add_argument('--verbose', '-v', action='store_true', help='Provide more feedback to console.')

        subparsers = parser.add_subparsers(dest='command')
        start_parser = subparsers.add_parser('start')
        stop_parser = subparsers.add_parser('stop')
        status_parser = subparsers.add_parser('status')
        create_parser = subparsers.add_parser('create')
        create_parser.add_argument('--settings', '-s', metavar='SETTINGS_FILE',
            help="A settings file can be provided on server creation to override default settings and provide required settings instead of prompting.")
        create_parser.add_argument('--require_default_settings', '-d', action='store_true', help=argparse.SUPPRESS)
        delete_parser = subparsers.add_parser('delete')
        setserver_parser = subparsers.add_parser('set')

        return parser

    def _get_args(self):
        parser = self.get_parser()
        args = parser.parse_args()
        return args

    def start(self):
        env = os.environ.copy()
        env = self._add_server_to_python_path(env)
        env = self._set_database(env)
        env = self._export_django_settings(env)
        self._create_logdirs()
        self._start_daemon(env)
        self._start_webserver(env)

    def _create_logdirs(self):
        for logfile in (self.settings_manager.get_access_logfile(),
                        self.settings_manager.get_error_logfile(),
                        self.settings_manager.get_daemon_logfile()):
            logdir = os.path.dirname(logfile)
            if not os.path.exists(logdir):
                os.makedirs(logdir)
        
    def _start_webserver(self, env):
        cmd = "gunicorn %s --bind %s:%s --pid %s --access-logfile %s --error-logfile %s --log-level %s" % (
                self.settings_manager.get_server_wsgi_module(), 
                self.settings_manager.get_bind_ip(), 
                self.settings_manager.get_bind_port(), 
                self.settings_manager.get_webserver_pidfile(),
                self.settings_manager.get_access_logfile(),
                self.settings_manager.get_error_logfile(),
                self.settings_manager.get_log_level(),
                )
        if not self.args.fg_webserver:
            cmd = cmd + " --daemon"
        if self.args.verbose:
            print("Starting webserver with command:\n%s" % cmd)
        process = subprocess.Popen(
            cmd,
            shell=True,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        process.wait()
        (stdout, stderr) = process.communicate()
        if not process.returncode == 0:
            raise Exception('Loom webserver failed to start, with return code "%s". \nFailed command is "%s". \n%s \n%s' % (process.returncode, cmd, stdout, stderr))

    def _start_daemon(self, env):
        if self.args.no_daemon == True:
            return
        pidfile = self.settings_manager.get_daemon_pidfile()
        logfile = self.settings_manager.get_daemon_logfile()
        loglevel = self.settings_manager.get_log_level()
        cmd = "%s %s start --pidfile %s --logfile %s --loglevel %s" % (sys.executable, DAEMON_EXECUTABLE, pidfile, logfile, loglevel)
        if self.args.verbose:
            print("Starting loom daemon with command:\n%s" % cmd)
        process = subprocess.Popen(
            cmd,
            shell=True,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        process.wait()
        (stdout, stderr) = process.communicate()
        if not process.returncode == 0:
            raise Exception('Loom Daemon failed to start, with return code "%s". \nFailed command is "%s". \n%s \n%s' % (process.returncode, cmd, stderr, stdout))

    def status(self):
        url = self.settings_manager.get_server_url_for_client()
        if is_server_running(url):
            print 'OK. The server is running.'
        else:
            print 'No response for server at %s. Do you need to run "loom server start"?' % url

    def stop(self):
        self._stop_webserver()
        self._stop_daemon()

    def _stop_webserver(self):
        pid = self.settings_manager.get_webserver_pid()
        if pid is not None:
            subprocess.call(
                "kill %s" % pid,
                shell=True,
                )
        self._cleanup_pidfile(self.settings_manager.get_webserver_pidfile())

    def _stop_daemon(self):
        subprocess.call(
            "%s %s --pidfile %s stop" % (sys.executable, DAEMON_EXECUTABLE, self.settings_manager.get_daemon_pidfile()),
            shell=True
            )
        self._cleanup_pidfile(self.settings_manager.get_daemon_pidfile())

    def _cleanup_pidfile(self, pidfile):
        if os.path.exists(pidfile):
            try:
                os.remove(pidfile)
            except:
                warnings.warn('Failed to delete PID file %s' % pidfile)

    def _add_server_to_python_path(self, env):
        env.setdefault('PYTHONPATH', '')
        env['PYTHONPATH'] = "%s:%s" % (self.settings_manager.get_server_path(), env['PYTHONPATH'])
        return env

    def _set_database(self, env):
        manage_cmd = [sys.executable, '%s/manage.py' % self.settings_manager.get_server_path()]
        if self.args.test_database:
            # If test database requested, set LOOM_TEST_DATABSE to true and reset database
            env['LOOM_TEST_DATABASE'] = 'true'
            commands = [
                manage_cmd + ['flush', '--noinput'],
                manage_cmd + ['migrate'],
                ]
            for command in commands:
                stdout = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    env=env).communicate()
        else:
            stdout = subprocess.Popen(
                manage_cmd + ['migrate', '-l'],
                stdout=subprocess.PIPE,
                env=env).communicate()
            if re.search('\[ \]', stdout[0]):
                yes_or_no = None
                while not (yes_or_no == 'yes' or yes_or_no == 'no'):
                    yes_or_no = raw_input("The Loom database needs to be initialized or updated. Proceed? (yes/no)\n> ")
                if yes_or_no == 'yes':
                    stdout = subprocess.Popen(
                        manage_cmd + ['migrate'],
                        stdout=subprocess.PIPE,
                        env=env).communicate()
                else:
                    raise Exception("Declined to apply database migrations. Exiting now.")
        return env

    def _export_django_settings(self, env):
        env.update(self.settings_manager.get_django_env_settings())
        return env

    def create(self):
        print self.args

    def delete(self):
        print self.args

    def setserver(self):
        print self.args

if __name__=='__main__':
    ServerControls().run()
