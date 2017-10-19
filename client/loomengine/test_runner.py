#!/usr/bin/env python

import argparse
from datetime import datetime
import os
import re
import subprocess
import sys
import time


class IntegrationTestFailure(Exception):
    pass


class TestRunner(object):

    def __init__(self, args=None):
        # Parse arguments
        if args is None:
            args = _get_args()
        self.args = args
        self._set_run_function()

    def _set_run_function(self):
        # Map user input command to method
        commands = {
            'unit': self.unit_tests,
            'profile': self.profile_test,
            'integration': self.integration_test,
        }
        self.run = commands[self.args.command]

    def profile_test(self):
        raise SystemExit('TODO')

    def integration_test(self):
        self._find_or_start_server()

        failure = None
        try:
            self._run_integration_test()
        except IntegrationTestFailure as e:
            failure = e
        self._cleanup_server()

        if failure:
            raise SystemExit(e.message)

        print "Test passed"

    def _run_integration_test(self):
        loom_executable = sys.argv[0]
        template_dir = os.path.join(os.path.dirname(__file__), 'test', 'templates')
        input_file_name = 'message.txt'
        template_file_name = 'integration_test.yaml'

        import_file_cmd = [loom_executable, 'file', 'import',
                           os.path.join(template_dir, input_file_name),
                           '--force-duplicates']
        (returncode, stdout) = self._run_command(import_file_cmd)
        if returncode != 0:
            raise IntegrationTestFailure('ERROR: Failed to import file.')
        match = re.search(r'[a-zA-Z0-9\.\-\_]*@[a-z0-9\-]*', stdout)
        if not match:
            raise IntegrationTestFailure('Could not find id of imported file')
        file_id = match.group()
 
        import_template_cmd = [loom_executable, 'template', 'import',
                               os.path.join(template_dir, template_file_name),
                               '--force-duplicates']
        (returncode, stdout) = self._run_command(import_template_cmd)
        if returncode != 0:
            raise IntegrationTestFailure('ERROR: Failed to import template.')
        match = re.search(r'[a-zA-Z0-9\.\-\_]*@[a-z0-9\-]*', stdout)
        if not match:
            raise IntegrationTestFailure('ERROR: Could not find id of imported template')
        template_id = match.group()

        run_cmd = [loom_executable, 'run', 'start', template_id, 'message=%s' % file_id]
        (returncode, stdout) = self._run_command(run_cmd)
        if returncode != 0:
            raise IntegrationTestFailure('ERROR: Failed to execute run.')
        match = re.search(r'[a-zA-Z0-9\.\-\_]*@[a-z0-9\-]*', stdout)
        if not match:
            raise IntegrationTestFailure('ERROR: Could not find id of run')
        run_id = match.group()

        self._wait_for_run(run_id)

    def _wait_for_run(self, run_id):
        sleep_interval_seconds = 3
        start_time = datetime.now()
        loom_executable = sys.argv[0]
        timeout = int(self.args.timeout)
        cmd = [loom_executable, 'run', 'list', run_id]
        while (datetime.now() - start_time).total_seconds() < timeout:
            p = subprocess.Popen(cmd, env=os.environ,
                                stdout=subprocess.PIPE)
            p.wait()
            if not p.returncode == 0:
                raise IntegrationTestFailure(
                    'ERROR: "loom run list" command failed.')
            (stdout, stderr) = p.communicate()
            match = re.search(r'Run: .* \(([a-zA-Z0-9_\-]*)\)', stdout)
            if match:
                status = match.groups()[0]
                print 'Status: %s' % status
                if status == 'Finished':
                    # success
                    return
                elif status not in ['Running', 'Waiting']:
                    raise IntegrationTestFailure('Unexpected run status: %s' % status)
            time.sleep(sleep_interval_seconds)
        raise IntegrationTestFailure('ERROR: Test timed out after %s seconds' % timeout)

    def _run_command(self, cmd, display=True):
        stdout=''
        p = subprocess.Popen(cmd, env=os.environ,
                             stdout=subprocess.PIPE,
                             bufsize=1)
        for line in iter(p.stdout.readline, b''):
            stdout += line
            sys.stdout.write(line)
        p.stdout.close()
        p.wait()
        return (p.returncode, stdout)
        
    def unit_tests(self):

        # Create an environment variable dict with loom root as the PYTHONPATH
        loom_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        loom_env = dict(os.environ.copy(), PYTHONPATH=loom_root)

        client_dir = (os.path.abspath(os.path.dirname(__file__)))
        returncode = subprocess.call(
            [sys.executable, '-m', 'unittest', 'discover', client_dir])

        print 'Return code: %s' % returncode
        return returncode

    def _find_or_start_server(self):
        self._started_new_server_named = None
        if not self._is_server_running():
            self._start_server()

    def _is_server_running(self):
        loom_executable = sys.argv[0]
        # No need for text output. Returncode tells us if server is running.
        with open('/dev/null', 'w') as devnull:
            returncode = subprocess.call([loom_executable, 'server', 'status'],
                                         env=os.environ, stdout=devnull, stderr=devnull)
        if returncode == 0:
            return True
        else:
            return False
        pass

    def _start_server(self):
        self._started_new_server_named = 'loom-test-server'
        loom_executable = sys.argv[0]
        cmd = [loom_executable, 'server', 'start',
               '-e' 'LOOM_SERVER_NAME=%s' % self._started_new_server_named]
        returncode = subprocess.call(cmd, env=os.environ)
        if not returncode == 0:
            raise SystemExit('ERROR: Failed to start server')

    def _cleanup_server(self):
        if self._started_new_server_named:
            loom_executable = sys.argv[0]
            cmd = [loom_executable, 'server', 'delete',
                   '--confirm-server-name', self._started_new_server_named]
            returncode = subprocess.call(cmd, env=os.environ)

def get_parser(parser=None):
    if parser is None:
        parser = argparse.ArgumentParser(__file__)

    subparsers = parser.add_subparsers(dest='command')

    unit_parser = subparsers.add_parser(
        'unit',
        help='run unit tests')

    integration_parser = subparsers.add_parser(
        'integration',
        help='run integration test. If no Loom server is running, '\
        'a temporary local Loom server will be created')
    integration_parser.add_argument('--timeout', '-t', metavar='TIMEOUT_SECONDS',
                                    default=300)

    return parser

def _get_args():
    parser = get_parser()
    args = parser.parse_args()
    return args


if __name__=='__main__':
    TestRunner().run()
