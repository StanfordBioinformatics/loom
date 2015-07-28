#!/usr/bin/env python

from main import App
import daemon
from daemon import runner
import os
import re
import subprocess
import time

pid_file_path = '/tmp/xppf_async.pid'

def get_parser():
    import argparse
    parser = argparse.ArgumentParser('xppf async')
    parser.add_argument('command', choices=['start', 'stop'])
    return parser

def get_daemon_context():
    return daemon.DaemonContext(
        working_directory='.',
#        stdout=open('out.log', 'w'),
#        stderr=open('err.log', 'w'),
        pidfile=daemon.pidfile.PIDLockFile(pid_file_path)
        )

def get_pid():
    try:
        with open(pid_file_path) as f:
            pid = f.read().strip()
    except:
        return None
    if not re.match('^[0-9]*$', pid):
        return None
    else:
        return pid

def verify_daemon_not_running():
    if os.path.exists(pid_file_path):
        pid = get_pid()
        raise Exception('A daemon may already be running. The pid file "%s" exists with pid "%s"' % (pid_file_path, pid))

def start_server():
    verify_daemon_not_running()
    daemon_context = get_daemon_context()
    daemon_context.open()
    App().run()

def stop_server():
    pid = get_pid()
    if pid is None:
        raise Exception('A daemon may not be running. Could not find pid in "%s"' % pid_file_path)
    else:
        subprocess.call('kill %s' % pid, shell=True)

if __name__=='__main__':
    parser = get_parser()
    args = parser.parse_args()
    
    if args.command == 'start':
        start_server()
    elif args.command == 'stop':
        stop_server()
    else:
        raise Exception("Unrecognized command %s" % args.command)
