#!/usr/bin/env python

import os
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
            cmd = [sys.executable,
                   MANAGE_EXECUTABLE,
                   'update_status']
            if self.logfile:
                cmd.append('--logfile')
                cmd.append(self.logfile)
            self.logger.info('Health check')
            retcode = subprocess.call(cmd)
            time.sleep(SLEEP_TIME_SECONDS)

if __name__=='__main__':
    App().run()

