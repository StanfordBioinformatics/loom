#!/usr/bin/env python

import os
import requests
import subprocess
import sys
import time
from loom.master.loomdaemon import loom_daemon_logger



MANAGE_EXECUTABLE = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        '../manage.py'
        )
    )

SLEEP_TIME_SECONDS = 1

class App():
   
    def __init__(self, logfile=None, loglevel='DEBUG'):
        self.logfile = logfile
        self.logger = loom_daemon_logger.get_logger(logfile, loglevel)

    def run(self):
        while True:
            cmd1 = [sys.executable,
                   MANAGE_EXECUTABLE,
                   'update_tasks']
            cmd2 = [sys.executable,
                   MANAGE_EXECUTABLE,
                   'run_tasks']
            if self.logfile:
                cmd1.append('--logfile')
                cmd1.append(self.logfile)
                cmd2.append('--logfile')
                cmd2.append(self.logfile)
            self.logger.info('Running job queues')
            retcode = subprocess.call(cmd1)
            retcode = subprocess.call(cmd2)
            time.sleep(SLEEP_TIME_SECONDS)

if __name__=='__main__':
    App().run()

